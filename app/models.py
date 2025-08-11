from django.db import models
from files.models import UploadedWheelFile, UploadedModelFile, UploadedInputFile, UploadedClassFile, UploadedGroundTruthFile

# Create your models here.

def output_upload_path(instance, filename):
    run_name = instance.name if hasattr(instance, "name") else "unnamed_run"
    return f'output/{run_name}/final_output.json'

def output_metadata_path(instance, filename):
    run_name = instance.name if hasattr(instance, "name") else "unnamed_run"
    return f'output/{run_name}/metadata.json'


class Workflow(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, unique=True)
    input = models.ForeignKey(UploadedInputFile, null=True, on_delete=models.CASCADE)
    created_by = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-pinned']

    def __str__(self):
        return self.name

class WorkflowStep(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField()
    wheel_file = models.ForeignKey(UploadedWheelFile, on_delete=models.CASCADE)
    model_file = models.ForeignKey(UploadedModelFile, null=True, on_delete=models.CASCADE)
    class_file = models.ForeignKey(UploadedClassFile, null=True, on_delete=models.CASCADE)
    ground_truth_file = models.ForeignKey(UploadedGroundTruthFile, null=True, on_delete=models.CASCADE)
    result_file = models.CharField(max_length=2048, blank=True)
    input_type = models.CharField(max_length=24, blank=True)

    class Meta:
        unique_together = ('workflow', 'step_number')
        ordering = ['step_number']

    def __str__(self):
        return f"{self.workflow.name} - Step {self.step_number}"

class WorkflowStepRun(models.Model):
    workflow_step = models.ForeignKey(WorkflowStep, on_delete=models.CASCADE, related_name='steps')
    start_time = models.DateTimeField(auto_now_add=True, null=True)
    end_time = models.DateTimeField(null=True)

    class Meta:
        ordering = ['end_time']

    def __str__(self):
        return f"{self.workflow_step.workflow.name} - Step {self.workflow_step.step_number}"

class WorkflowRun(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='workflowrun')
    start_time = models.DateTimeField(auto_now_add=True, null=True)
    end_time = models.DateTimeField(null=True)
    run_by = models.CharField(max_length=255, blank=True)
    output = models.CharField(max_length=255, null=True, blank=True)
    error = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True)
    task_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

class ModelPerformance(models.Model):
    workflow_run = models.ForeignKey(WorkflowRun, null=False, on_delete=models.CASCADE, related_name='performance_workflow_run')
    workflow_step_run = models.ForeignKey(WorkflowStepRun, null=False, on_delete=models.CASCADE, related_name='performance_workflow_step_run')
    accuracy = models.FloatField(null=True)

    def __str__(self):
        return self.workflow_run.workflow.name