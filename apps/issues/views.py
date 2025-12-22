from rest_framework import viewsets,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import Issue
from .serializers import IssueSerializer
from .permissions import IsStaffOrManager, IsReporterOrManagerOrAdmin
from .services import IssueService
from apps.users.models import User
from apps.issues.models import IssueHistory
from apps.issues.serializers import IssueHistorySerializer
from django_filters.rest_framework import DjangoFilterBackend




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
        """
        Create issue using IssueService to trigger notifications.
        """
        try:
            issue = IssueService.create_issue(
                user=self.request.user,
                data=serializer.validated_data
            )
            serializer.instance = issue
        except Exception as e:
            # Log error for debugging
            print(f"Error creating issue: {e}")
            raise

    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update']:
            return [IsReporterOrManagerOrAdmin()]  # Custom permission for edits
        if self.action in ['destroy', 'assign', 'transition']:
            return [IsStaffOrManager()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == 'client':
            return self.queryset.filter(reporter=user)
        if user.role == 'staff':
            return self.queryset.filter(assignee=user)
        return self.queryset

    def update(self, request, *args, **kwargs):
        # Check if issue is in editable status
        instance = self.get_object()
        editable_statuses = ['open', 'reopen']
        
        if instance.status not in editable_statuses and request.user.role not in ['admin', 'manager']:
            return Response({
                "detail": f"Only issues with status 'open' or 'reopen' can be edited. Current status: {instance.status}"
            }, status=403)
        
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        issue = self.get_object()
        assignee_id = request.data.get('assignee_id')
        assignee = get_object_or_404(User, id=assignee_id)
        IssueService.assign_issue(issue, assignee, request.user)
        return Response(IssueSerializer(issue).data)

    @action(detail=True, methods=['post'])
    def transition(self, request, pk=None):
        issue = self.get_object()
        new_status = request.data.get('new_status')
        
        if not new_status:
            return Response({"detail": "Field 'new_status' is required."}, status=400)
        
        valid_statuses = [choice[0] for choice in Issue.STATUS_CHOICES]
        
        if new_status not in valid_statuses:
            return Response({
                "detail": f"Invalid status: '{new_status}'. Allowed values are: {valid_statuses}",
                "allowed": valid_statuses
            }, status=400)
        
        try:
            IssueService.transition_status(issue, new_status, request.user)
            return Response(IssueSerializer(issue).data)
        except Exception as e:
            return Response({
                "detail": f"Failed to transition status: {str(e)}"
            }, status=500)
class IssueHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing issue history.
    Read-only - history should only be created automatically.
    """
    queryset = IssueHistory.objects.all().select_related(
        'issue', 
        'changed_by'
    ).prefetch_related(  
        'issue__reporter',
        'issue__assignee'
    ).order_by('-timestamp')
    
    serializer_class = IssueHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['new_status', 'changed_by']
    search_fields = ['issue__title', 'changed_by__email']
    ordering_fields = ['timestamp', 'issue__title']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Filter based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'client':
            # Clients can only see history of their own issues
            return queryset.filter(issue__reporter=user)
        elif user.role == 'staff':
            # Staff can see issues assigned to them
            return queryset.filter(issue__assignee=user)
        # Admin and manager can see all
        return queryset

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent history (last 7 days)"""
        from datetime import datetime, timedelta
        last_week = datetime.now() - timedelta(days=7)
        
        recent_history = self.get_queryset().filter(
            timestamp__gte=last_week
        ).order_by('-timestamp')[:100]
        
        page = self.paginate_queryset(recent_history)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(recent_history, many=True)
        return Response(serializer.data)