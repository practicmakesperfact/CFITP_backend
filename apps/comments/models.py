
from django.db import models
from apps.users.models import User
from apps.issues.models import Issue
import uuid

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    visibility = models.CharField(
        max_length=20,
        choices=[('public', 'Public'), ('internal', 'Internal')],
        default='public'
    )
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.email if self.author else 'Anonymous'} on {self.issue.title}"