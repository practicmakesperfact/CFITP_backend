# apps/reports/models.py
from django.db import models
import uuid
from apps.users.models import User

class Report(models.Model):
    TYPE_CHOICES = (
        ('issues_by_status', 'Issues by Status'),
        ('issues_by_assignee', 'Issues by Assignee'),
        ('issues_by_priority', 'Issues by Priority'),
        ('feedback_summary', 'Feedback Summary'),
        ('team_performance', 'Team Performance'),
        ('resolution_analytics', 'Resolution Analytics'),
        ('performance_dashboard', 'Performance Dashboard'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('generated', 'Generated'),
        ('failed', 'Failed'),
    )
    
    FORMAT_CHOICES = (
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    parameters = models.JSONField(default=dict, blank=True)
    result_path = models.FileField(upload_to='reports/', null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.user.email} ({self.status})"