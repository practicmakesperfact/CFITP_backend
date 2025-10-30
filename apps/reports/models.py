from django.db import models
import uuid
from apps.users.models import User

class Report(models.Model):
    TYPE_CHOICES = (
        ('issues_by_status', 'Issues by Status'),
        ('issues_by_assignee', 'Issues by Assignee'),
        ('issues_by_priority', 'Issues by Priority'),
        ('feedback_summary', 'Feedback Summary'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('generated', 'Generated'),
        ('failed', 'Failed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_path = models.FileField(upload_to='reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)