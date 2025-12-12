
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse
from drf_spectacular.utils import extend_schema, inline_serializer
import hashlib
from django.shortcuts import get_object_or_404

from .models import Attachment
from .serializers import AttachmentSerializer


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        issue_id = self.request.query_params.get('issue')
        if issue_id:
            qs = qs.filter(issue_id=issue_id)
        return qs

    def perform_create(self, serializer):
        issue_id = self.request.data.get('issue')
        comment_id = self.request.data.get('comment')
        feedback_id = self.request.data.get('feedback')
        serializer.save(
            uploaded_by=self.request.user,
            issue_id=issue_id,
            comment_id=comment_id,
            feedback_id=feedback_id,
        )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    # PUT: 
    def perform_update(self, serializer):
        file = self.request.FILES.get('file')
        if not file:
            raise serializers.ValidationError({"file": "No file was submitted."})

        attachment = self.get_object()
        if attachment.file:
            attachment.file.delete(save=False)

        attachment.file = file
        attachment.mime_type = file.content_type or 'application/octet-stream'
        attachment.size = file.size

        # keep associations if present in request
        attachment.issue_id = self.request.data.get('issue', attachment.issue_id)
        attachment.comment_id = self.request.data.get('comment', attachment.comment_id)
        attachment.feedback_id = self.request.data.get('feedback', attachment.feedback_id)

        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        attachment.checksum = hasher.hexdigest()
        attachment.save()
        serializer.instance = attachment

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {'type': 'string', 'format': 'binary'}
                },
                'required': ['file']
            }
        },
        responses={200: AttachmentSerializer}
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    # PATCH: Update metadata only (issue, comment, feedback)
    @extend_schema(
        request=inline_serializer(
            name='AttachmentPatch',
            fields={
                'issue': serializers.CharField(allow_blank=True, allow_null=True, required=False),
                'comment': serializers.CharField(allow_blank=True, allow_null=True, required=False),
                'feedback': serializers.CharField(allow_blank=True, allow_null=True, required=False),
            }
        ),
        responses={200: AttachmentSerializer},
        # content_type='application/json'  # FORCES JSON in Swagger
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    # Download file
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        attachment = self.get_object()
        if not attachment.file or not attachment.file.storage.exists(attachment.file.name):
            return Response({"detail": "File not found."}, status=404)

        file_handle = attachment.file.open()
        response = FileResponse(
            file_handle,
            content_type=attachment.mime_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{attachment.file.name.split("/")[-1]}"'
        return response