from django.db import models
import uuid
from apps.users.models import User
from apps.issues.models import Issue

class Feedback(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('converted', 'Converted to Issue'),
        ('closed', 'Closed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')  # NOT 'type'!
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    converted_to = models.ForeignKey(Issue, null=True, blank=True, on_delete=models.SET_NULL)  # Use converted_to
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feedback: {self.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-created_at']