from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import NotificationSerializer
from .models import Notification
from .services import NotificationService
from rest_framework.permissions import IsAuthenticated

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        NotificationService.mark_as_read(notification)
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all user's notifications as read."""
        notifications = self.get_queryset().filter(is_read=False)
        updated_count = notifications.update(is_read=True)
        
        return Response({
            "status": "success",
            "message": f"{updated_count} notifications marked as read"
        })