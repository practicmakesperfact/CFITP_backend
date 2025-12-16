from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from drf_spectacular.utils import extend_schema
from PIL import Image
import io

from .models import Attachment
from .serializers import AttachmentSerializer
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny
import jwt
from django.conf import settings


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated]

    # Image preview endpoint - allow token in query params
    @action(detail=True, methods=['get'], url_path='preview', 
            permission_classes=[AllowAny], authentication_classes=[])
    def preview(self, request, pk=None):
        # Check for token in query params
        token = request.query_params.get('token')
        
        if token:
            try:
                # Verify JWT token
                jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                # If valid, authenticate the request
                request.user = self.get_object().uploaded_by
            except jwt.ExpiredSignatureError:
                return Response({"detail": "Token expired."}, status=401)
            except jwt.InvalidTokenError:
                return Response({"detail": "Invalid token."}, status=401)
        
        attachment = self.get_object()
        
        if not attachment.is_image():
            return Response({"detail": "File is not an image."}, status=400)

    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by issue ID
        issue_id = self.request.query_params.get('issue')
        if issue_id:
            qs = qs.filter(issue_id=issue_id)
        
        # Filter by comment ID
        comment_id = self.request.query_params.get('comment')
        if comment_id:
            qs = qs.filter(comment_id=comment_id)
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(uploaded_by_id=user_id)
        
        # Filter by file type
        file_type = self.request.query_params.get('type')
        if file_type:
            if file_type == 'image':
                qs = qs.filter(mime_type__startswith='image/')
            elif file_type == 'pdf':
                qs = qs.filter(mime_type='application/pdf')
            elif file_type == 'document':
                qs = qs.filter(mime_type__in=[
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/plain'
                ])
        
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def create(self, request, *args, **kwargs):
        try:
            # Log the incoming data for debugging
            print("Creating attachment with data:", request.data)
            print("Files:", request.FILES)
            
            # Ensure we have the request in serializer context
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            
            # Save the attachment
            attachment = serializer.save()
            
            # Return the created attachment
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"Attachment creation error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return a more helpful error message
            return Response({
                'detail': 'Failed to upload file.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

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

    # Image preview endpoint
    @action(detail=True, methods=['get'], url_path='preview')
    def preview(self, request, pk=None):
        attachment = self.get_object()
        
        if not attachment.is_image():
            return Response({"detail": "File is not an image."}, status=400)
        
        if not attachment.file or not attachment.file.storage.exists(attachment.file.name):
            return Response({"detail": "File not found."}, status=404)

        try:
            # Open and resize image for preview
            with attachment.file.open('rb') as f:
                img = Image.open(f)
                
                # Resize image for preview (max 800px width/height)
                max_size = 800
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Save to bytes
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG', quality=85)
                img_io.seek(0)
                
                return HttpResponse(img_io, content_type='image/jpeg')
                
        except Exception as e:
            print(f"Image preview error: {e}")
            # Fallback to original file
            file_handle = attachment.file.open()
            response = FileResponse(
                file_handle,
                content_type=attachment.mime_type
            )
            response['Content-Disposition'] = f'inline; filename="{attachment.file.name.split("/")[-1]}"'
            return response

    # Get attachment stats
    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        user = request.user
        stats = {
            'total': Attachment.objects.count(),
            'total_size': sum(att.size for att in Attachment.objects.all()),
            'by_type': {
                'images': Attachment.objects.filter(mime_type__startswith='image/').count(),
                'pdfs': Attachment.objects.filter(mime_type='application/pdf').count(),
                'documents': Attachment.objects.filter(mime_type__in=[
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/plain'
                ]).count(),
                'others': Attachment.objects.exclude(
                    mime_type__startswith='image/'
                ).exclude(
                    mime_type='application/pdf'
                ).exclude(
                    mime_type__in=[
                        'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'text/plain'
                    ]
                ).count(),
            },
            'user_stats': {
                'uploaded': Attachment.objects.filter(uploaded_by=user).count(),
                'total_size': sum(att.size for att in Attachment.objects.filter(uploaded_by=user)),
            }
        }
        
        # Format size in human-readable format
        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} TB"
        
        stats['total_size_formatted'] = format_size(stats['total_size'])
        stats['user_stats']['total_size_formatted'] = format_size(stats['user_stats']['total_size'])
        
        return Response(stats)