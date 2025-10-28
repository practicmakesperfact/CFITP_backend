from django.db import models
from django.conf import settings
from apps.users.models import User
import uuid

class Issue(models.Model):
    STATUS_CHOICES =(
        ('open','Open'),
        ('in_progess','In_progress'),
        ('resolved','Resolved'),
        ('closed','Closed'),
        ('reopen','Reopen'),
    )
    PRIORITY_CHOICES =(
        ('low','Low'),
        ('medium','Medium'),
        ('high','High'),
        ('critical','Critical'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status =models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=50,choices=PRIORITY_CHOICES,default='medium')
    reporter =models.ForeignKey(User,related_name='reported_issues', on_delete=models.CASCADE)
    assignee =models.ForeignKey(User,related_name='assigned_issues', on_delete=models.CASCADE, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='issues'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
class IssueHistory(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    issue = models.ForeignKey(Issue,related_name='history',on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)