from django.db import models
import uuid
from apps.users.models import User
from django.core.validators import FileExtensionValidator, MaxValueValidator
from django.core.files.storage import default_storage
import hashlib

class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='attachments/', validators=[FileExtensionValidator(['pdf', 'jpg', 'png', 'doc', 'docx','txt'])])
    mime_type = models.CharField(max_length=100)
    size = models.IntegerField(validators=[MaxValueValidator(10*1024*1024)])  # 10MB
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    checksum = models.CharField(max_length=64)  # SHA256
    issue = models.ForeignKey('issues.Issue', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.ForeignKey('comments.Comment', null=True, blank=True, on_delete=models.CASCADE)
    feedback = models.ForeignKey('feedback.Feedback', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Only set mime_type if available (file being uploaded)
        self.mime_type = getattr(self.file, 'content_type', self.mime_type)
        self.size = self.file.size
        hasher = hashlib.sha256()
        for chunk in self.file.chunks():
            hasher.update(chunk)
        self.checksum = hasher.hexdigest()
        super().save(*args, **kwargs)
