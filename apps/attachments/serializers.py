
from rest_framework import serializers
from apps.users.serializers import UserSerializer
from .models import Attachment
import os

# Import the related models
try:
    from apps.issues.models import Issue
    from apps.comments.models import Comment
    from apps.feedback.models import Feedback
except ImportError:
    # Fallback imports if apps structure is different
    from issues.models import Issue
    from comments.models import Comment
    from feedback.models import Feedback


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    file = serializers.FileField(write_only=True, required=True)
    file_url = serializers.SerializerMethodField(read_only=True)
    
    # Use CharField for foreign keys to accept UUID strings
    issue = serializers.CharField(required=False, allow_null=True, write_only=True)
    comment = serializers.CharField(required=False, allow_null=True, write_only=True)
    feedback = serializers.CharField(required=False, allow_null=True, write_only=True)
    
    # Read-only fields for representation
    issue_id = serializers.UUIDField(source='issue.id', read_only=True, allow_null=True)
    comment_id = serializers.UUIDField(source='comment.id', read_only=True, allow_null=True)
    feedback_id = serializers.UUIDField(source='feedback.id', read_only=True, allow_null=True)
    filename = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Attachment
        fields = [
            'id', 'file', 'file_url', 'mime_type', 'size', 'uploaded_by',
            'created_at', 'issue', 'comment', 'feedback',
            'issue_id', 'comment_id', 'feedback_id', 'filename', 'checksum'
        ]
        read_only_fields = [
            'id', 'mime_type', 'size', 'checksum',
            'created_at', 'uploaded_by', 'issue_id', 'comment_id', 'feedback_id', 'filename'
        ]

    def get_file_url(self, obj):
        if obj.file and hasattr(obj.file, 'url'):
            # Return absolute URL if request context is available
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_filename(self, obj):
        if obj.file:
            return os.path.basename(obj.file.name)
        return None

    def create(self, validated_data):
        # Extract foreign key UUID strings
        issue_uuid = validated_data.pop('issue', None)
        comment_uuid = validated_data.pop('comment', None)
        feedback_uuid = validated_data.pop('feedback', None)
        
        # Get the request user
        request = self.context.get('request')
        if request and request.user:
            validated_data['uploaded_by'] = request.user
        
        # Create the attachment instance
        attachment = Attachment(**validated_data)
        
        # Set foreign keys if UUIDs are provided
        if issue_uuid and issue_uuid != 'null' and issue_uuid != '':
            try:
                from apps.issues.models import Issue
                attachment.issue = Issue.objects.get(id=issue_uuid)
            except (Issue.DoesNotExist, ValueError):
                pass
        
        if comment_uuid and comment_uuid != 'null' and comment_uuid != '':
            try:
                from apps.comments.models import Comment
                attachment.comment = Comment.objects.get(id=comment_uuid)
            except (Comment.DoesNotExist, ValueError):
                pass
        
        if feedback_uuid and feedback_uuid != 'null' and feedback_uuid != '':
            try:
                from apps.feedback.models import Feedback
                attachment.feedback = Feedback.objects.get(id=feedback_uuid)
            except (Feedback.DoesNotExist, ValueError):
                pass
        
        # Save the attachment (this will trigger the save() method which sets size, mime_type, checksum)
        attachment.save()
        return attachment

    def to_representation(self, instance):
        """Custom representation to include foreign key IDs"""
        representation = super().to_representation(instance)
        
        # Include the IDs in the response
        if instance.issue:
            representation['issue'] = str(instance.issue.id)
        if instance.comment:
            representation['comment'] = str(instance.comment.id)
        if instance.feedback:
            representation['feedback'] = str(instance.feedback.id)
        
        return representation