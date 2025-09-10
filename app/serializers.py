from rest_framework import serializers
from .models import (
    Workflow, 
    ModelPerformance,
    WorkflowStep,
    WorkflowRun,
    WorkflowStepRun
)
from files.serializers import (
    UploadedInputFileSerializer,
    UploadedModelFileSerializer,
    UploadedWheelFileSerializer,
    UploadedClassFileSerializer,
    UploadedGroundTruthFileSerializer
)

class WorkflowStepReadSerializer(serializers.ModelSerializer):

    wheel_file = UploadedWheelFileSerializer()
    model_file = UploadedModelFileSerializer()
    class_file = UploadedClassFileSerializer()
    ground_truth_file = UploadedGroundTruthFileSerializer()

    class Meta:
        model = WorkflowStep
        fields = ['id','step_number', 'wheel_file', 'model_file', 'class_file', 'ground_truth_file', 'result_file', 'input_type']

class WorkflowStepRunSerializer(serializers.ModelSerializer):
    workflow_step = WorkflowStepReadSerializer()

    class Meta:
        model = WorkflowStepRun
        fields = '__all__'

class WorkflowReadSerializer(serializers.ModelSerializer):

    input = UploadedInputFileSerializer()
    steps = WorkflowStepReadSerializer(many=True, read_only=True)

    class Meta:
        model = Workflow
        fields = '__all__'

class WorkflowWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = [
            'name',
            'description',
            'input',
            'created_at',
            'created_by',
            'pinned'
        ]

class WorkflowStepWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = [
            'workflow_id',
            'step_number',
            'wheel_file_id',
            'class_file_id',
            'ground_truth_file_id',
            'model_file_id',
            'input_type'
        ]

class WorkflowRunReadSerializer(serializers.ModelSerializer):
    workflow = WorkflowReadSerializer()

    class Meta:
        model = WorkflowRun
        fields = '__all__'

class WorkflowRunWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRun
        fields = [
            'workflow',
            'start_time',
            'end_time',
            'run_by',
            'error',
            'error_message'
        ]

class ModelPerformanceSerializer(serializers.ModelSerializer):
    workflow_run = WorkflowRunReadSerializer()
    workflow_step_run = WorkflowStepRunSerializer()

    class Meta:
        model = ModelPerformance
        fields = '__all__'