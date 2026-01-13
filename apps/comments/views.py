from rest_framework import viewsets,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Comment
from .services import CommentService
from .serializers import CommentSerializer
from apps.issues.models import Issue
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework import serializers
 

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        issue_id = self.kwargs.get('issue_pk')
        if issue_id:
            return Comment.objects.filter(issue__id=issue_id).select_related('author', 'issue').order_by('-created_at')
        # Fallback for non-nested routes
        return Comment.objects.all().select_related('author', 'issue').order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        # Handle attachments field mapping before serializer validation
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # Map 'attachments' to 'attachments_ids' if present
        if 'attachments' in data:
            attachments = data.pop('attachments', [])
            if attachments:
                data['attachments_ids'] = attachments
            else:
                data['attachments_ids'] = []
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        issue_id = self.kwargs.get('issue_pk')
        if not issue_id:
            raise serializers.ValidationError("Issue ID is required")
        issue = get_object_or_404(Issue, id=issue_id)
        comment = CommentService.create_comment(self.request.user, issue, serializer.validated_data)
        serializer.instance = comment
    
    def perform_update(self, serializer):
        comment = CommentService.update_comment(serializer.instance, self.request.data, self.request.user)
        serializer.instance = comment

    def perform_destroy(self, instance):
        CommentService.delete_comment(instance, self.request.user)

