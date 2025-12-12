from rest_framework import serializers
from apps.users.serializers import UserSerializer
from .models import Attachment
import uuid

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file = serializers.FileField(write_only=True, required=True)
    file_url = serializers.SerializerMethodField(read_only=True)

    # Keep these readable so the client can filter
    issue = serializers.UUIDField(required=False, allow_null=True)
    comment = serializers.UUIDField(required=False, allow_null=True)
    feedback = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Attachment
        fields = [
            'id', 'file', 'file_url', 'mime_type', 'size', 'uploaded_by',
            'created_at', 'issue', 'comment', 'feedback'
        ]
        read_only_fields = [
            'id', 'mime_type', 'size', 'checksum',
            'created_at', 'uploaded_by'
        ]

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            return obj.file.url
        return None

    def to_internal_value(self, data):
        # Convert string UUIDs → UUID objects; allow blank/None
        for field in ['issue', 'comment', 'feedback']:
            value = data.get(field)
            if value in ['', None]:
                data[field] = None
            elif isinstance(value, str):
                try:
                    data[field] = uuid.UUID(value)
                except ValueError:
                    raise serializers.ValidationError({
                        field: f"'{value}' is not a valid UUID."
                    })
        return super().to_internal_value(data)