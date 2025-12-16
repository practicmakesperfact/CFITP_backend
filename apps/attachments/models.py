from django.db import models
import uuid
from apps.users.models import User
from django.core.validators import FileExtensionValidator, MaxValueValidator
import hashlib
import os
from django.utils import timezone
from django.urls import reverse
from .storage import CustomAttachmentStorage

custom_storage = CustomAttachmentStorage()

class Attachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        upload_to='attachments/%Y/%m/%d/',
        storage=custom_storage,
        validators=[
            FileExtensionValidator([
                'pdf', 'jpg', 'png', 'jpeg', 'gif', 'webp',
                'doc', 'docx', 'txt', 'csv', 'xls', 'xlsx'
            ])
        ]
    )
    mime_type = models.CharField(max_length=100, blank=True)
    size = models.IntegerField(default=0, validators=[MaxValueValidator(10*1024*1024)])
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attachments')
    checksum = models.CharField(max_length=64, blank=True)
    issue = models.ForeignKey('issues.Issue', null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    comment = models.ForeignKey('comments.Comment', null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    feedback = models.ForeignKey('feedback.Feedback', null=True, blank=True, on_delete=models.CASCADE, related_name='attachments')
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, help_text="Optional description of the attachment")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['issue', 'created_at']),
            models.Index(fields=['comment', 'created_at']),
            models.Index(fields=['uploaded_by', 'created_at']),
        ]

    def save(self, *args, **kwargs):
        # Calculate file properties before saving
        if self.file and hasattr(self.file, 'file'):
            # Set mime_type if not already set
            if not self.mime_type:
                ext = os.path.splitext(self.file.name)[1].lower()
                mime_map = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp',
                    '.pdf': 'application/pdf',
                    '.doc': 'application/msword',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.txt': 'text/plain',
                    '.csv': 'text/csv',
                    '.xls': 'application/vnd.ms-excel',
                    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                }
                self.mime_type = mime_map.get(ext, 'application/octet-stream')
            
            # Set size
            try:
                if hasattr(self.file, 'size'):
                    self.size = self.file.size
                elif hasattr(self.file.file, 'size'):
                    self.size = self.file.file.size
            except (AttributeError, OSError):
                pass
            
            # Calculate checksum
            try:
                hasher = hashlib.sha256()
                # Reset file pointer
                self.file.seek(0)
                for chunk in iter(lambda: self.file.read(8192), b''):
                    hasher.update(chunk)
                self.checksum = hasher.hexdigest()
                # Reset file pointer
                self.file.seek(0)
            except Exception as e:
                print(f"Error calculating checksum: {e}")
                self.checksum = ''
        
        # Ensure defaults
        self.size = self.size or 0
        self.mime_type = self.mime_type or 'application/octet-stream'
        self.checksum = self.checksum or ''
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{os.path.basename(self.file.name)} ({self.size_formatted()})"

    def size_formatted(self):
        """Return human-readable file size"""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.1f} GB"

    def is_image(self):
        """Check if the file is an image"""
        return self.mime_type.startswith('image/') if self.mime_type else False

    def is_pdf(self):
        """Check if the file is a PDF"""
        return self.mime_type == 'application/pdf'

    def is_document(self):
        """Check if the file is a document"""
        return any(doc_type in self.mime_type for doc_type in [
            'msword', 'vnd.openxmlformats', 'text/plain'
        ])

    def get_absolute_url(self):
        """Get absolute URL for the attachment"""
        return reverse('attachments:download', kwargs={'pk': self.id})

    def get_preview_url(self):
        """Get URL for image preview (returns download URL for non-images)"""
        if self.is_image():
            return reverse('attachments:preview', kwargs={'pk': self.id})
        return self.get_absolute_url()

    def get_icon_class(self):
        """Get icon class based on file type"""
        if self.is_image():
            return '🖼️'
        elif self.is_pdf():
            return '📄'
        elif self.is_document():
            return '📝'
        else:
            return '📎'