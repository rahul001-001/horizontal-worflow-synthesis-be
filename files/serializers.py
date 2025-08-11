from rest_framework import serializers
from .models import (
    UploadedWheelFile, 
    UploadedModelFile, 
    UploadedInputFile,
    UploadedClassFile,
    UploadedGroundTruthFile
)

class UploadedWheelFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedWheelFile
        fields = [
            'id',
            'name',
            'path',
            'description',
            'uploaded_at',
            'uploaded_by',
            'size'
        ]


class UploadedModelFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedModelFile
        fields = [
            'id',
            'name',
            'path',
            'description',
            'uploaded_at',
            'uploaded_by',
            'size'
        ]

class UploadedInputFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedInputFile
        fields = [
            'id',
            'name',
            'path',
            'description',
            'uploaded_at',
            'uploaded_by',
            'size',
            'input_type'

        ]

class UploadedClassFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedClassFile
        fields = [
            'id',
            'name',
            'path',
            'description',
            'uploaded_at',
            'uploaded_by',
            'size'
        ]

class UploadedGroundTruthFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedGroundTruthFile
        fields = [
            'id',
            'name',
            'path',
            'description',
            'uploaded_at',
            'uploaded_by',
            'size'
        ]