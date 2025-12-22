# apps/feedback/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .serializers import FeedbackSerializer
from .models import Feedback
from .services import FeedbackService
from apps.users.permissions import IsStaffOrManager, IsManagerOrAdmin
from apps.issues.serializers import IssueSerializer

class FeedbackPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all().select_related('user', 'converted_to')  
    serializer_class = FeedbackSerializer
    pagination_class = FeedbackPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description', 'user__email']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'convert':
            return [IsStaffOrManager()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user.is_authenticated:
            return queryset.none()
        
        if user.role in ['client']:
            return queryset.filter(user=user)
        
        # Admin, manager, staff can see all feedback
        return queryset

    def perform_create(self, serializer):
        """Create feedback with proper user assignment"""
        user = self.request.user if self.request.user.is_authenticated else None
        # USE FeedbackService to trigger notifications
        feedback = FeedbackService.create_feedback(user, serializer.validated_data)
        serializer.instance = feedback  

    @action(detail=False, methods=['get'])
    def my(self, request):
        """Get current user's feedback"""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        feedback = Feedback.objects.filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(feedback)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(feedback, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """Convert feedback to issue"""
        feedback = self.get_object()
        
        if feedback.status == 'converted':
            return Response({
                "status": "error",
                "message": "Feedback already converted to issue",
                "issue_id": str(feedback.converted_to.id) if feedback.converted_to else None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            issue = FeedbackService.convert_to_issue(
                feedback, 
                request.user, 
                request.data
            )
            
            issue_serializer = IssueSerializer(issue)
            return Response({
                "status": "success",
                "message": "Feedback converted to issue successfully",
                "issue": issue_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": "error",
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Mark feedback as acknowledged (staff action)"""
        feedback = self.get_object()
        
        if feedback.status != 'new':
            return Response({
                "status": "error",
                "message": f"Feedback is already {feedback.get_status_display()}"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use FeedbackService for acknowledgment notifications
        feedback = FeedbackService.acknowledge_feedback(feedback, request.user)
        
        return Response({
            "status": "success",
            "message": "Feedback acknowledged",
            "feedback": FeedbackSerializer(feedback).data
        })