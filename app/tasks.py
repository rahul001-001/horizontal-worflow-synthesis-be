import zipfile
import tempfile
import importlib.util
import os
import pandas as pd
from celery import Celery
import subprocess
from datetime import datetime
import json
import logging
from pathlib import Path
from app.models import (
    Workflow, 
    ModelPerformance,
    WorkflowRun,
    WorkflowStep,
    WorkflowStepRun
)
from django.conf import settings

celery_app = Celery(
    "cv_tasks",
    broker="amqp://guest:guest@localhost:5672//",  # RabbitMQ URL
    backend="rpc://",  # or redis://localhost:6379/0
)

def get_package_name_from_whl(whl_path):
    with zipfile.ZipFile(whl_path, 'r') as z:
        for file in z.namelist():
            if file.endswith('METADATA'):
                with z.open(file) as meta:
                    for line in meta:
                        if line.startswith(b'Name:'):
                            return line.decode().split(':',1)[1].strip()
    
    return None

def load_classes_from_model_folder(classes_txt_path):
    class_indices = []
    with open(classes_txt_path, 'r') as f:
        for line in f:
            if ':' in line:
                index, _ = line.strip().split(':', 1)
                if index.strip().isdigit():
                    class_indices.append(int(index.strip()))
        return class_indices
    return None

def compute_accuracy(ground_truth_path, model_result_path):
    try:
        gt_df = pd.read_csv(ground_truth_path)
        model_df = pd.read_csv(model_result_path)

        gt_counts = gt_df.set_index('Frame No')['Object Count']
        model_counts = model_df.set_index('Frame No')['Object Count']

        common_frames = gt_counts.index.intersection(model_counts.index)
        correct = sum(gt_counts[frame] == model_counts[frame] for frame in common_frames)
        accuracy = (correct / len(common_frames)) * 100 if common_frames.any() else 0
        return round(accuracy, 2)
    except Exception as e:
        print("Accuracy computation failed:", e)
        return 0.0

def get_task_logger(task_id, output_path):
    os.makedirs(output_path, exist_ok=True)  # ensure output folder exists

    logger = logging.getLogger(f"task_{task_id}")
    logger.setLevel(logging.INFO)

    log_file = os.path.join(output_path, f"{task_id}.log")
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        logger.addHandler(handler)

    return logger, log_file

import sys

@celery_app.task(name="tasks.run_whl_task", bind=True)
def run_whl_task(
    self,
    run_id,
    step_number,
    step_id,
    whl_path,
    input_path,
    output_path,
    classes_path,
    ground_truth_path,
    model_path,
    input_type,
    prev_result=None
):
    os.makedirs(output_path, exist_ok=True)
    log_file = os.path.join(output_path, f"{self.request.id}.log")

    # Redirect stdout & stderr to log file
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log_fh = open(log_file, "a")
    sys.stdout = log_fh
    sys.stderr = log_fh

    print(f"[{datetime.now()}] Starting task {self.request.id} for workflow run {run_id}")

    run = WorkflowRun.objects.filter(id=run_id).first()
    step = WorkflowStep.objects.filter(id=step_id).first()

    workflow_step_run = WorkflowStepRun.objects.create(
        workflow_step=step,
        start_time=datetime.now()
    )

    # Validate input
    if input_type == "video" and not input_path.endswith(settings.VIDEO_EXTENSIONS):
        raise ValueError(f'Expected video input for step {step_number}.')
    if input_type == "image" and (not input_path.endswith(settings.IMAGE_EXTENSIONS) and not os.path.isdir(input_path)):
        raise ValueError(f'Expected image or folder for step {step_number}.')

    print(f"[{datetime.now()}] Installing wheel: {whl_path}")
    subprocess.check_call(["pip", "install", "--no-deps", "--no-cache-dir", "--force-reinstall", whl_path])

    package_name = get_package_name_from_whl(whl_path)
    classes = load_classes_from_model_folder(classes_path)

    try:
        print(f"[{datetime.now()}] Running inference for package: {package_name}")
        module = importlib.import_module("inference.inference")

        result = module.run_inference(
            input_path=input_path,
            step_number=step_number,
            output_path=output_path,
            classes=classes,
            model_path=model_path,
            input_type=input_type
        )

        workflow_step_run.end_time = datetime.now()
        workflow_step_run.save()

        csv_path = os.path.join(output_path, f"{step_number}_results.csv")
        video_path = os.path.join(output_path, f"{step_number}_output.mp4")

        # step.result_file = result["csv_file"]
        step.result_file = csv_path
        step.save()

        # accuracy = compute_accuracy(ground_truth_path, result["csv_file"])
        accuracy = compute_accuracy(ground_truth_path, csv_path)
        ModelPerformance.objects.create(
            workflow_run=run,
            workflow_step_run=workflow_step_run,
            accuracy=accuracy
        )

        run.end_time = datetime.now()
        run.save()

        print(f"[{datetime.now()}] Task completed successfully.")
        return result

    except Exception as e:
        run.error = True
        run.error_message = str(e)
        run.save()

        print(f"[{datetime.now()}] Task failed: {e}")
        raise

    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        log_fh.close()

@celery_app.task
def chain_step_wrapper(prev_result, run_id, step_number, step_id, whl_path, output_path, classes_path, ground_truth_path, model_path, input_type):
    # Dynamically choose input_path from prev_result
    input_path = (
        prev_result.get("video_file")
        or prev_result.get("image_folder")
        or prev_result.get("csv_file")
        or prev_result.get("output_path")
    )

    # Call the actual task
    return run_whl_task.run(
        run_id,
        step_number,
        step_id,
        whl_path,
        input_path,
        output_path,
        classes_path,
        ground_truth_path,
        model_path,
        input_type
    )

# @celery_app.task(name="tasks.run_whl_task")
# def run_whl_task(run_id, model_performance_id, model_number,whl_path, input_path, output_path, metadata_path, model_path):

#     run = Workflow.objects.filter(id=run_id).first()
#     model_performance = ModelPerformance.objects.filter(id=model_performance_id).first()
#     if model_performance:
#         model_performance.start_time = datetime.now()
#         model_performance.save()
    
#     subprocess.check_call(["pip", "install", whl_path])
#     try:
#         with tempfile.TemporaryDirectory() as temp_dir:
#             # Extract wheel file
#             with zipfile.ZipFile(whl_path, 'r') as zip_ref:
#                 zip_ref.extractall(temp_dir)

#             # Locate script.py inside package folder
#             script_file = None
#             for root, dirs, files in os.walk(temp_dir):
#                 for f in files:
#                     if f == "script.py":
#                         script_file = os.path.join(root, f)
#                         break

#             if not script_file:
#                 return "script.py not found in wheel."

#             # Load module
#             spec = importlib.util.spec_from_file_location("script", script_file)
#             module = importlib.util.module_from_spec(spec)
#             spec.loader.exec_module(module)

#             # Call the script's run function
#             if hasattr(module, 'run'):
#                 module.run(input_path, output_path, metadata_path, model_path)
#                 with open(metadata_path, "r") as f:
#                     metadata = json.load(f)
#                 metadata_path = Path(metadata_path).parent
#                 with open(metadata_path/f'metadata_{model_number}.json', "w") as f:
#                     json.dump(metadata, f, indent=4)
                
#                 try:
#                     run.end_time = datetime.now()
#                     setattr(run, f'{model_number}_metadata', metadata_path/f'metadata_{model_number}.json')
#                     model_performance.end_time = datetime.now()
#                     run.save()
#                     model_performance.save()
#                 except Exception as e:
#                     return "No Run associated"

#                 return "Script ran successfully."
#             else:
#                 return "run() function not found in script."

#     except Exception as e:
#         run.error = True
#         run.error_message = str(e)
#         run.save()
#         return f"Error running wheel: {e}"

@celery_app.task(name="tasks.evaluate_performance")
def evaluate_performance(run_id):
    return