from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
import os
import csv

from .models import Report
from .serializers import ReportSerializer
from .services import ReportService
from apps.users.permissions import IsStaffOrManager

class ReportViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """
    Report ViewSet for creating and managing reports.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsStaffOrManager]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        # Users can only see their own reports
        return self.queryset.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Save report with user and initial status"""
        serializer.save(
            user=self.request.user,
            status='pending'  # Initial status
        )
    
    def create(self, request, *args, **kwargs):
        """Override create to start report generation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Save the report
            report = serializer.save()
            
            # Start report generation in background (Celery task)
            self._start_report_generation(report)
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            return Response(
                {'detail': f'Failed to create report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _start_report_generation(self, report):
        """Start report generation using Celery"""
        from .tasks import generate_report_task
        
        # Start the background task
        generate_report_task.delay(str(report.id))
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get analytics data for dashboard"""
        try:
            # Get date range from query params
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            # Convert string dates to datetime objects
            start_date = None
            end_date = None
            
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str)
                except ValueError:
                    return Response(
                        {"error": f"Invalid start_date format: {start_date_str}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if timezone.is_naive(start_date):
                    start_date = timezone.make_aware(start_date)
            
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str)
                except ValueError:
                    return Response(
                        {"error": f"Invalid end_date format: {end_date_str}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if timezone.is_naive(end_date):
                    end_date = timezone.make_aware(end_date)
                # Set to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
            
            # Get filters
            priority = request.query_params.get('priority', '').split(',') if request.query_params.get('priority') else []
            status_filter = request.query_params.get('status', '').split(',') if request.query_params.get('status') else []
            
            # Get analytics data
            analytics_data = ReportService.get_analytics_data(
                start_date=start_date,
                end_date=end_date,
                user=request.user,
                priority_filter=priority,
                status_filter=status_filter
            )
            
            return Response({
                'data': analytics_data,
                'success': True,
                'message': 'Analytics data retrieved successfully',
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response({
                'data': None,
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch analytics data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get real-time metrics for dashboard"""
        try:
            from apps.issues.models import Issue
            from apps.feedback.models import Feedback
            
            # Get time frame (last 24 hours)
            twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
            
            # Simple real-time metrics
            metrics = {
                'total_issues': Issue.objects.count(),
                'open_issues': Issue.objects.filter(status='open').count(),
                'in_progress_issues': Issue.objects.filter(status='in_progress').count(),
                'resolved_today': Issue.objects.filter(
                    status='resolved',
                    updated_at__gte=twenty_four_hours_ago
                ).count(),
                'new_issues_today': Issue.objects.filter(
                    created_at__gte=twenty_four_hours_ago
                ).count(),
                'total_feedback': Feedback.objects.count(),
                'new_feedback_today': Feedback.objects.filter(
                    created_at__gte=twenty_four_hours_ago
                ).count(),
                'timestamp': timezone.now().isoformat(),
                'database_status': 'connected',
                'last_updated': timezone.now().strftime('%I:%M:%S %p')
            }
            
            return Response({
                'data': metrics,
                'success': True
            })
            
        except Exception as e:
            return Response({
                'data': None,
                'success': False,
                'error': str(e),
                'database_status': 'disconnected'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get report generation status"""
        try:
            report = self.get_object()
            
            return Response({
                'data': {
                    'id': str(report.id),
                    'type': report.type,
                    'type_display': report.get_type_display(),
                    'format': report.format,
                    'status': report.status,
                    'status_display': report.get_status_display(),
                    'created_at': report.created_at,
                    'updated_at': report.updated_at,
                    'result_available': report.status == 'generated' and bool(report.result_path),
                    'result_path': report.result_path.url if report.result_path else None
                },
                'success': True
            })
            
        except Exception as e:
            return Response({
                'data': None,
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the generated report file"""
        try:
            report = self.get_object()
            
            if report.status != 'generated' or not report.result_path:
                return Response(
                    {"detail": "Report not available for download."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if file exists
            if not report.result_path or not os.path.exists(report.result_path.path):
                return Response(
                    {"detail": "Report file not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Open the file for reading
            response = FileResponse(
                open(report.result_path.path, 'rb'),
                content_type='application/octet-stream'
            )
            
            # Set content disposition for download
            filename = f"report_{report.type}_{report.created_at.strftime('%Y%m%d_%H%M%S')}.{report.format}"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {"detail": f"Error downloading file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Quick export endpoint (CSV only)"""
        try:
            export_format = request.query_params.get('format', 'csv')
            
            # Only support CSV
            if export_format != 'csv':
                return Response(
                    {"detail": f"Only CSV export is supported. Requested format: {export_format}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get date range from query params
            start_date_str = request.query_params.get('start_date')
            end_date_str = request.query_params.get('end_date')
            
            start_date = None
            end_date = None
            
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str)
                if timezone.is_naive(start_date):
                    start_date = timezone.make_aware(start_date)
            
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str)
                if timezone.is_naive(end_date):
                    end_date = timezone.make_aware(end_date)
                # Set to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59)
            
            # Get filters
            priority = request.query_params.get('priority', '').split(',') if request.query_params.get('priority') else []
            status_filter = request.query_params.get('status', '').split(',') if request.query_params.get('status') else []
            
            # Get analytics data
            data = ReportService.get_analytics_data(
                start_date=start_date,
                end_date=end_date,
                user=request.user,
                priority_filter=priority,
                status_filter=status_filter
            )
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="cfitp_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            
            # Header
            writer.writerow(['CFITP Analytics Dashboard Export'])
            writer.writerow([f'Period: {data.get("period_display", "N/A")}'])
            writer.writerow([f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([f'Generated by: {request.user.email}'])
            writer.writerow([])
            
            # Summary Metrics
            writer.writerow(['SUMMARY METRICS'])
            writer.writerow(['Metric', 'Value'])
            for key, value in data.get('summary', {}).items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])
            
            # Issues by Status
            if 'issues_by_status' in data and data['issues_by_status']:
                writer.writerow(['ISSUES BY STATUS'])
                writer.writerow(['Status', 'Count', 'Percentage'])
                for item in data['issues_by_status']:
                    writer.writerow([
                        item.get('status_display', item.get('status', 'Unknown')),
                        item.get('count', 0),
                        f"{item.get('percentage', 0)}%"
                    ])
                writer.writerow([])
            
            # Issues by Priority
            if 'issues_by_priority' in data and data['issues_by_priority']:
                writer.writerow(['ISSUES BY PRIORITY'])
                writer.writerow(['Priority', 'Count', 'Percentage'])
                for item in data['issues_by_priority']:
                    writer.writerow([
                        item.get('priority_display', item.get('priority', 'Unknown')),
                        item.get('count', 0),
                        f"{item.get('percentage', 0)}%"
                    ])
                writer.writerow([])
            
            # Team Performance
            if 'team_performance' in data and data['team_performance']:
                writer.writerow(['TEAM PERFORMANCE'])
                writer.writerow(['Name', 'Email', 'Role', 'Assigned', 'Resolved', 'Pending', 'Efficiency %', 'Avg. Resolution (hours)'])
                for member in data['team_performance']:
                    writer.writerow([
                        member.get('name', 'N/A'),
                        member.get('email', 'N/A'),
                        member.get('role', 'N/A'),
                        member.get('total_assigned', 0),
                        member.get('resolved', 0),
                        member.get('pending', 0),
                        member.get('efficiency', 0),
                        member.get('avg_resolution_time_hours', 'N/A')
                    ])
            
            return response
            
        except Exception as e:
            return Response(
                {"error": str(e), "detail": "CSV export failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )