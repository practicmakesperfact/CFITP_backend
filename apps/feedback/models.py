from django.db import models
import uuid
from apps.users.models import User
from apps.issues.models import Issue

class Feedback(models.Model):
    STATUS_CHOICES = (
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('converted', 'Converted'),
        ('closed', 'Closed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)  # Optional
    converted_to = models.OneToOneField(Issue, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)