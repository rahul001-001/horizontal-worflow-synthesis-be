from django.db import models

INPUT_TYPES = [
    ("file", "File"),
    ("folder", "Folder")
]

class UploadedInputFile(models.Model):

    name = models.CharField(max_length=255, blank=True, unique=True)
    path = models.CharField(max_length=1024, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255)
    size = models.BigIntegerField(null=True, blank=True)
    input_type = models.CharField(max_length=10, choices=INPUT_TYPES)

    def __str__(self):
        return self.name

class UploadedModelFile(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)
    path = models.CharField(max_length=1024, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255)
    size = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class UploadedWheelFile(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)
    path = models.CharField(max_length=1024, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255)
    size = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class UploadedClassFile(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)
    path = models.CharField(max_length=1024, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255)
    size = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class UploadedGroundTruthFile(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)
    path = models.CharField(max_length=1024, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=255)
    size = models.BigIntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


