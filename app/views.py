from django.shortcuts import render
from .tasks import run_whl_task
from datetime import datetime
from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from users.permissions import IsAdminRole
from .tasks import run_whl_task, evaluate_performance, chain_step_wrapper
from .models import (
    Workflow, 
    ModelPerformance, 
    WorkflowStep,
    WorkflowRun,
    WorkflowStepRun
)
from .serializers import (
    WorkflowReadSerializer,
    WorkflowWriteSerializer,
    WorkflowStepRunSerializer,
    WorkflowStepReadSerializer,
    WorkflowStepWriteSerializer,
    WorkflowRunReadSerializer,
    WorkflowRunWriteSerializer,
    ModelPerformanceSerializer
)
from celery import chain
from django.conf import settings
import os

class WorkFlowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        object_dict = {}

        serializer = WorkflowWriteSerializer(data={
            'name': request.data['name'],
            'description': request.data['description'],
            'input': request.data['input'],
            'created_by': request.user.username,
            'created_at': datetime.now()
        })
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        step_counter = 0
        for step in request.data['steps']:
            step_counter += 1
            workflow_step = WorkflowStepWriteSerializer(data={
                'workflow': instance.id,
                'step_number': step['step_number'],
                'wheel_file': step['script'],
                'model_file': step['model'],
                'class_file': step['class'],
                'input_type': step['input_type'],
                'ground_truth_file': step['ground_truth'],
                'result_file': f"media/output/u{step['step_number']}_inference.csv"
            })
            workflow_step.is_valid(raise_exception=True)
            workflow_step_instance = workflow_step.save()

        return Response({"detail": "Chained pipeline launched via Celery."}, status=status.HTTP_202_ACCEPTED)

class WorkflowRunListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            instances = WorkflowRun.objects.all()
        except WorkflowRun.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkflowRunReadSerializer(instances, many=True)

        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_all_video_paths(base_path):
    video_files = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.lower().endswith(settings.VIDEO_EXTENSIONS):
                video_files.append(os.path.join(root, file))
    return video_files

class WorkflowRunView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            instance = WorkflowRun.objects.get(id=pk)
        except WorkflowRun.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkflowRunReadSerializer(instance)

        if serializer:
            video_paths = get_all_video_paths(os.path.join(settings.MEDIA_ROOT, 'output', f'{instance.workflow.name}_{instance.id}'))
            response = serializer.data
            response['video_paths'] = video_paths
            return Response(response, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            instance = WorkflowRun.objects.get(id=pk)
        except WorkflowRun.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class TriggerWorkFlowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            instance = Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkflowReadSerializer(instance)

        workflow_run = WorkflowRun.objects.create(
            workflow = instance,
            start_time = datetime.now(),
            run_by = request.user.username
        )

        workflow_run.output = f"output/{instance.name}_{workflow_run.id}/"
        workflow_run.save()

        if serializer:
            serializer_data = serializer.data
            
            if not serializer_data['steps']:
                return Response('This workflow did not have any steps. Execution was stopped', status=status.HTTP_400_BAD_REQUEST)

            task_chain = []
            # Seed the chain with the first task (dummy prev_result)
            first = run_whl_task.s(
                workflow_run.id,
                1,
                serializer_data['steps'][0]['id'],
                os.path.join(settings.MEDIA_ROOT, serializer_data['steps'][0]['wheel_file']['path']),
                os.path.join(settings.MEDIA_ROOT, instance.input.path),
                os.path.join(settings.MEDIA_ROOT, workflow_run.output),
                os.path.join(settings.MEDIA_ROOT, serializer_data['steps'][0]['class_file']['path']),
                os.path.join(settings.MEDIA_ROOT, serializer_data['steps'][0]['ground_truth_file']['path']),
                os.path.join(settings.MEDIA_ROOT, serializer_data['steps'][0]['model_file']['path']) if serializer_data['steps'][0]['model_file'] else None,
                serializer_data['steps'][0]['input_type'].lower()
            )
            task_chain.append(first)

            # Remaining steps: use wrapper to inject previous result
            for step in serializer_data['steps'][1:]:
                task_chain.append(
                    chain_step_wrapper.s(
                        workflow_run.id,
                        step['step_number'],
                        step['id'],
                        os.path.join(settings.MEDIA_ROOT, step['wheel_file']['path']),
                        os.path.join(settings.MEDIA_ROOT, workflow_run.output),
                        os.path.join(settings.MEDIA_ROOT, step['class_file']['path']),
                        os.path.join(settings.MEDIA_ROOT, step['ground_truth_file']['path']),
                        os.path.join(settings.MEDIA_ROOT, step['model_file']['path']) if step['model_file'] else None,
                        step['input_type'].lower()
                    )
                )

            chain(*task_chain).apply_async()
            return Response({"detail": "Chained pipeline launched via Celery."}, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WorkflowListView(generics.ListAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowReadSerializer

class WorkflowPinView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            instance = Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)
        
        set_pinned_status = True
        if instance.pinned == True:
            set_pinned_status = False


        serializer = WorkflowWriteSerializer(instance, data={
            'pinned': set_pinned_status,
        }, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkflowListView(generics.ListAPIView):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowReadSerializer

class WorkflowDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            instance = Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkflowReadSerializer(instance)

        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            instance = Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        instance.steps.all().delete()

        step_counter = 0
        new_steps = []
        for step in request.data['steps']:
            step_counter += 1
            workflow_step = WorkflowStep(
                workflow=instance,
                step_number=step['step_number'],
                wheel_file_id=step['wheel_file']['id'],
                model_file_id=step['model_file']['id'] if step['model_file'] else None,
            )
            new_steps.append(workflow_step)
        
        WorkflowStep.objects.bulk_create(new_steps)

        # return Response(status=status.HTTP_200_OK)
        serializer = WorkflowWriteSerializer(instance, data={
            'name': request.data['name'],
            'description': request.data['description'],
            'input': request.data['input'],
        }, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        try:
            instance = Workflow.objects.get(id=pk)
        except Workflow.DoesNotExist:
            return Response({"error": "Workflow not found"}, status=status.HTTP_404_NOT_FOUND)

        instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

class ModelPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            instances = ModelPerformance.objects.filter(workflow_run_id=pk)
        except not instances:
            return Response({"error": "Model performance not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModelPerformanceSerializer(instances, many=True)

        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ModelPerformanceListView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            instances = ModelPerformance.objects.all().order_by('-accuracy','-workflow_step_run__workflow_step__model_file__size')
        except not instances:
            return Response({"error": "Model performance not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = ModelPerformanceSerializer(instances, many=True)

        if serializer:
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

