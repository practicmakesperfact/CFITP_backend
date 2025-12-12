from rest_framework import serializers
from .models import Comment
from apps.users.serializers import UserSerializer
from apps.attachments.serializers import AttachmentSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_name = serializers.SerializerMethodField()
    author_email = serializers.SerializerMethodField()
    author_role = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    # Add attachments as write-only field
    attachments_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'author', 'issue']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.email
        return "Unknown"

    def get_author_email(self, obj):
        return obj.author.email if obj.author else ""

    def get_author_role(self, obj):
        return obj.author.role if obj.author else "unknown"
    
    def get_attachments(self, obj):
        # Return attachments linked to this comment
        attachments = obj.attachment_set.all() if hasattr(obj, 'attachment_set') else []
        return AttachmentSerializer(attachments, many=True).data
    
    def to_internal_value(self, data):
        # Create a mutable copy of data
        if hasattr(data, '_mutable'):
            data._mutable = True
        
        # Map 'attachments' to 'attachments_ids' for internal use
        if isinstance(data, dict):
            if 'attachments' in data:
                attachments_value = data.pop('attachments', [])
                if attachments_value:
                    data['attachments_ids'] = attachments_value
                else:
                    data['attachments_ids'] = []
        
        return super().to_internal_value(data)

