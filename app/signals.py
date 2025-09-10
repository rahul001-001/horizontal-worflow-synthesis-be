import os
import shutil
from django.db.models.signals import post_delete
from django.dispatch import receiver
from app.models import WorkflowRun
from django.conf import settings

@receiver(post_delete, sender=WorkflowRun)
def delete_workflowrun_output(sender, instance, **kwargs):
    if instance.output:
        folder_path = os.path.join(settings.MEDIA_ROOT, instance.output)

        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)