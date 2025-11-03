from rest_framework import serializers
from apps.users.serializers import UserSerializer
from .models import Attachment
import uuid


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file = serializers.FileField(write_only=True, required=True)

    # Accept string UUIDs in PATCH
    issue = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, write_only=True
    )
    comment = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, write_only=True
    )
    feedback = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, write_only=True
    )

    class Meta:
        model = Attachment
        fields = [
            'id', 'file', 'mime_type', 'size', 'uploaded_by',
            'created_at', 'issue', 'comment', 'feedback'
        ]
        read_only_fields = [
            'id', 'mime_type', 'size', 'checksum',
            'created_at', 'uploaded_by'
        ]

    def to_internal_value(self, data):
        # Convert string UUIDs → UUID objects
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