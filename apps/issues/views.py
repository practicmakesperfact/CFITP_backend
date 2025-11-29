
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Issue
from .serializers import IssueSerializer
from .permissions import IsStaffOrManager
from apps.users.models import User


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all().select_related('reporter', 'assignee').order_by('-created_at')
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def perform_create(self, serializer):
        # THIS IS ALL YOU NEED — SIMPLE & PERFECT
        serializer.save(
            reporter=self.request.user,
            created_by=self.request.user
        )

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]                    # Clients can create
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy', 'assign', 'transition']:
            return [IsStaffOrManager()]                   # Only staff/manager
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return self.queryset.filter(reporter=user)
        if user.role == 'staff':
            return self.queryset.filter(assignee=user)
        return self.queryset  # admin/manager see all

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        issue = self.get_object()
        assignee_id = request.data.get('assignee_id')
        assignee = get_object_or_404(User, id=assignee_id)
        issue.assignee = assignee
        issue.save()
        return Response(IssueSerializer(issue).data)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        issue = self.get_object()
        new_status = request.data.get('new_status')
        if new_status not in dict(Issue.STATUS_CHOICES):
            return Response({"detail": "Invalid status"}, status=400)
        issue.status = new_status
        issue.save()
        return Response(IssueSerializer(issue).data)