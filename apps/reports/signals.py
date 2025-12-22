
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
import os
from .models import Report

@receiver(post_delete, sender=Report)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Delete report file when report record is deleted"""
    if instance.result_path and hasattr(instance.result_path, 'path'):
        try:
            if os.path.isfile(instance.result_path.path):
                os.remove(instance.result_path.path)
        except (OSError, ValueError):
            # Log error or pass silently
            pass

@receiver(post_save, sender=Report)
def cleanup_failed_reports(sender, instance, **kwargs):
    """Clean up files from failed reports after 7 days"""
    from django.utils import timezone
    from datetime import timedelta
    
    if (instance.status == 'failed' and 
        instance.created_at < timezone.now() - timedelta(days=7) and
        instance.result_path):
        try:
            if os.path.isfile(instance.result_path.path):
                os.remove(instance.result_path.path)
        except (OSError, ValueError):
            pass