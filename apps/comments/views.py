from rest_framework import viewsets,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Comment
from .services import CommentService
from .serializers import CommentSerializer
from apps.issues.models import Issue
from rest_framework.exceptions import PermissionDenied
 

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        issue_id=self.kwargs.get('issue_pk')
        return Comment.objects.filter(issue__id=issue_id).select_related('author') .ordered('created_at')  
    def perform_create(self,serializer):
        issue_id =self.kwargs.get('issue_pk')
        comment=CommentService.create_comment(self.request.user,issue,serializer.validated_data)
        serializer.instance=comment
    def perform_update(self, serializer):
        comment = CommentService.update_comment(serializer.instance, self.request.data, self.request.user)
        serializer.instance = comment

def perform_destroy(self, instance):
    CommentService.delete_comment(instance, self.request.user)


