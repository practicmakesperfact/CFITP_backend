from django.db import models
import uuid
from apps.users.models import User
from apps.issues.models import Issue

class Notification(models.Model):
    TYPE_CHOICES = (
        ('new_comment', 'New Comment'),
        ('assignment', 'Assignment'),
        ('status_change', 'Status Change'),
        ('mention', 'Mention'),
        ('feedback_converted', 'Feedback Converted'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, related_name='notification_notifications', on_delete=models.CASCADE)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    issue = models.ForeignKey(Issue, null=True, blank=True, on_delete=models.SET_NULL, related_name='notification_issues')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)