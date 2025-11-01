# apps/attachments/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse
from drf_spectacular.utils import extend_schema
import hashlib

from .models import Attachment
from .serializers import AttachmentSerializer


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Custom create logic to:
        - Set uploaded_by
        - Set mime_type BEFORE saving
        - Calculate checksum
        """
        uploaded_file = self.request.FILES.get('file')
        if not uploaded_file:
            raise serializers.ValidationError({"file": "No file was submitted."})

        # Create instance manually to control fields
        attachment = Attachment(
            file=uploaded_file,
            uploaded_by=self.request.user,
            mime_type=uploaded_file.content_type or 'application/octet-stream',
            size=uploaded_file.size
        )

        # Calculate checksum
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        attachment.checksum = hasher.hexdigest()

        # Save to DB and storage
        attachment.save()

        # Set instance for serializer
        serializer.instance = attachment

    @extend_schema(
        request={
            'multipart/form-data': {
                'type': 'object',
                'properties': {
                    'file': {
                        'type': 'string',
                        'format': 'binary',
                        'description': 'Upload a file (PDF, DOCX, PNG, etc.)'
                    }
                },
                'required': ['file']
            }
        },
        responses={201: AttachmentSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        attachment = self.get_object()
        
        # Ensure file exists
        if not attachment.file or not attachment.file.storage.exists(attachment.file.name):
            return Response({"detail": "File not found."}, status=404)

        file_handle = attachment.file.open()
        response = FileResponse(
            file_handle,
            content_type=attachment.mime_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{attachment.file.name.split("/")[-1]}"'
        return response