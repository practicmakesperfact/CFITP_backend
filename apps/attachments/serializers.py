from rest_framework import serializers
from .models import Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ['id', 'file', 'mime_type', 'size', 'uploaded_by', 'created_at']
        read_only_fields = ['mime_type', 'size', 'checksum', 'created_at', 'uploaded_by'] 
