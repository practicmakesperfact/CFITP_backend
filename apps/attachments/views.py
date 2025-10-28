from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import AttachmentSerializer
from .models import Attachment
from .services import AttachmentService
from django.http import FileResponse
from rest_framework.permissions import IsAuthenticated

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        file = self.request.FILES.get('file')
        # Related obj would be passed in data, but for simplicity, assume standalone or link later
        attachment = AttachmentService.upload_attachment(self.request.user, file)
        serializer.instance = attachment

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        attachment = self.get_object()
        file_handle = attachment.file.open()
        response = FileResponse(file_handle, content_type=attachment.mime_type)
        response['Content-Disposition'] = f'attachment; filename="{attachment.file.name}"'
        return response