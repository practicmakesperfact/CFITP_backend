from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from .serializers import IssueSerializer
from .models import Issue
from .services import IssueService
from .permissions import IsStaffOrManager, IsReporter
from apps.users.permissions import IsAdminOrReadOnly
from apps.users.models import User  # <-- Add this import

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all().select_related('reporter', 'assignee').order_by('-created_at')
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'reporter', 'assignee']

    def perform_create(self, serializer):
        """
        Handles issue creation — calls service but ensures serializer is valid.
        """
        validated_data = serializer.validated_data
        # Add the logged-in user automatically
        validated_data['reporter'] = self.request.user
        validated_data['created_by'] = self.request.user

        # Use your IssueService to handle creation logic
        issue = IssueService.create_issue(self.request.user, validated_data)

        # Attach the created instance back to serializer (important for DRF response)
        serializer.instance = issue

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsStaffOrManager()]
        elif self.action in ['assign', 'transition']:
            return [IsStaffOrManager()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return self.queryset.filter(reporter=user)
        elif user.role == 'staff':
            return self.queryset.filter(assignee=user)
        return self.queryset

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        issue = self.get_object()
        assignee_id = request.data.get('assignee_id')
        assignee = User.objects.get(id=assignee_id)
        IssueService.assign_issue(issue, assignee, request.user)
        return Response(IssueSerializer(issue).data)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        issue = self.get_object()
        new_status = request.data.get('new_status')
        IssueService.transition_status(issue, new_status, request.user)
        return Response(IssueSerializer(issue).data)
