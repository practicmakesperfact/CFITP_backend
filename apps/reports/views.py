# apps/reports/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Report
from .serializers import ReportSerializer
from .services import LightReportService as ReportService
from apps.users.permissions import IsStaffOrManager

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsStaffOrManager]
    
    def get_queryset(self):
        # Users can only see their own reports
        return self.queryset.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        report_type = self.request.data.get('type', 'issues_by_status')
        report_format = self.request.data.get('format', 'excel')
        parameters = self.request.data.get('parameters', {})
        
        # Create report
        report = Report.objects.create(
            type=report_type,
            format=report_format,
            user=self.request.user,
            parameters=parameters,
            status='pending'
        )
        
        # Start async generation
        from .services import generate_report
        generate_report.delay(str(report.id))
        
        serializer.instance = report
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get analytics data for dashboard"""
        try:
            # Get date range from query params
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            report_type = request.query_params.get('report_type', 'issues_by_status')
            
            if start_date:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Get analytics data
            analytics_data = ReportService.get_analytics_data(
                start_date=start_date,
                end_date=end_date,
                user=request.user
            )
            
            return Response(analytics_data)
            
        except Exception as e:
            return Response(
                {"error": str(e), "detail": "Failed to fetch analytics data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get real-time metrics for dashboard"""
        try:
            # Get counts for all metrics
            from apps.issues.models import Issue
            from apps.feedback.models import Feedback
            from apps.users.models import User
            
            # Real-time counts
            total_issues = Issue.objects.count()
            open_issues = Issue.objects.filter(status='open').count()
            in_progress_issues = Issue.objects.filter(status='in_progress').count()
            unresolved_issues = Issue.objects.filter(status__in=['open', 'in_progress']).count()
            
            # High priority issues
            high_priority_issues = Issue.objects.filter(priority='high').count()
            critical_issues = Issue.objects.filter(priority='critical').count()
            
            # Feedback stats
            total_feedback = Feedback.objects.count()
            pending_feedback = Feedback.objects.filter(status='new').count()
            
            # User stats
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            # Recent activity (last 24 hours)
            last_24h = timezone.now() - timedelta(hours=24)
            recent_issues = Issue.objects.filter(created_at__gte=last_24h).count()
            recent_feedback = Feedback.objects.filter(created_at__gte=last_24h).count()
            
            metrics = {
                'issues': {
                    'total': total_issues,
                    'open': open_issues,
                    'in_progress': in_progress_issues,
                    'unresolved': unresolved_issues,
                    'high_priority': high_priority_issues,
                    'critical': critical_issues,
                    'recent_24h': recent_issues,
                },
                'feedback': {
                    'total': total_feedback,
                    'pending': pending_feedback,
                    'recent_24h': recent_feedback,
                },
                'users': {
                    'total': total_users,
                    'active': active_users,
                },
                'timestamps': {
                    'updated_at': timezone.now().isoformat(),
                    'last_24h': last_24h.isoformat(),
                }
            }
            
            return Response(metrics)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the generated report file"""
        report = self.get_object()
        
        if report.status != 'generated' or not report.result_path:
            return Response(
                {"detail": "Report not available for download."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Determine content type based on format
            content_types = {
                'csv': 'text/csv',
                'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'pdf': 'application/pdf',
                'json': 'application/json',
            }
            
            response = FileResponse(
                open(report.result_path.path, 'rb'),
                content_type=content_types.get(report.format, 'application/octet-stream')
            )
            
            filename = f"report_{report.type}_{report.created_at.strftime('%Y%m%d')}.{report.format}"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except FileNotFoundError:
            return Response(
                {"detail": "Report file not found on server."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": f"Error downloading file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get report generation status"""
        report = self.get_object()
        return Response({
            'id': str(report.id),
            'type': report.type,
            'format': report.format,
            'status': report.status,
            'created_at': report.created_at,
            'updated_at': report.updated_at,
            'error_message': report.error_message,
            'result_available': report.status == 'generated' and bool(report.result_path)
        })
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """Quick export endpoint"""
        try:
            report_type = request.data.get('type', 'issues_by_status')
            format_type = request.data.get('format', 'csv')
            parameters = request.data.get('parameters', {})
            
            # Generate CSV data directly
            from datetime import datetime
            from django.utils.timezone import make_aware
            
            end_date = make_aware(datetime.now())
            start_date = make_aware(datetime.now() - timedelta(days=30))
            
            if 'start_date' in parameters:
                start_date = make_aware(datetime.fromisoformat(parameters['start_date'].replace('Z', '+00:00')))
            if 'end_date' in parameters:
                end_date = make_aware(datetime.fromisoformat(parameters['end_date'].replace('Z', '+00:00')))
            
            # Generate the export
            if format_type == 'csv':
                csv_content = ReportService.generate_csv_report(
                    report_type,
                    start_date,
                    end_date,
                    request.user
                )
                
                response = Response(csv_content, content_type='text/csv')
                filename = f"export_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
                
            else:
                return Response(
                    {"detail": f"Format {format_type} not supported for quick export"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )