from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import FeedbackSerializer
from .models import Feedback
from .services import FeedbackService
from apps.users.permissions import IsStaffOrManager

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().select_related('user', 'converted_to')
    serializer_class = FeedbackSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        elif self.action == 'convert':
            return [IsStaffOrManager()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        feedback = FeedbackService.create_feedback(user, serializer.validated_data)
        serializer.instance = feedback

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        feedback = self.get_object()
        issue_data = request.data
        issue = FeedbackService.convert_to_issue(feedback, request.user, issue_data)
        return Response({'issue_id': issue.id}, status=status.HTTP_200_OK)