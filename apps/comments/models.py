from django.db import models
from apps.users.models import User
from apps.issues.models import Issue
import uuid

class Comment(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    issue= models.ForeignKey(Issue,related_name='comments',on_delete=models.CASCADE)
    author=models.ForeignKey(User,on_delete=models.CASCADE)
    content=models.TextField()
    parent= models.ForeignKey('self',null=True,blank=True,related_name='replies',on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    update=models.DateTimeField(auto_now=True)