# apps/reports/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Report
from .serializers import ReportSerializer
from .services import ReportService
from apps.users.permissions import IsStaffOrManager

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsStaffOrManager]
    
    def get_queryset(self):
        # Users can only see their own reports
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Add user to the report data
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get analytics data for dashboard"""
        try:
            # Get date range from query params
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            # Convert string dates to datetime objects
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
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get real-time metrics for dashboard"""
        try:
            from apps.issues.models import Issue
            from apps.feedback.models import Feedback
            
            # Simple real-time metrics
            metrics = {
                'total_issues': Issue.objects.count(),
                'open_issues': Issue.objects.filter(status='open').count(),
                'in_progress_issues': Issue.objects.filter(status='in_progress').count(),
                'resolved_issues': Issue.objects.filter(status='resolved').count(),
                'total_feedback': Feedback.objects.count(),
                'timestamp': timezone.now().isoformat(),
            }
            
            return Response(metrics)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get report generation status"""
        report = self.get_object()
        return Response({
            'id': str(report.id),
            'type': report.type,
            'status': report.status,
            'created_at': report.created_at,
            'updated_at': report.updated_at,
            'result_available': report.status == 'generated' and bool(report.result_path)
        })
    
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
            response = Response()
            response['Content-Disposition'] = f'attachment; filename="report_{report.id}.csv"'
            response['X-Accel-Redirect'] = report.result_path.url
            return response
            
        except Exception as e:
            return Response(
                {"detail": f"Error downloading file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Quick export endpoint"""
        try:
            from django.http import HttpResponse
            from io import StringIO
            import csv
            
            # Get analytics data
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if start_date:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            data = ReportService.get_analytics_data(start_date, end_date, request.user)
            
            # Create CSV response
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="export.csv"'
            
            writer = csv.writer(response)
            
            # Write summary
            writer.writerow(['Summary Metrics'])
            writer.writerow(['Metric', 'Value'])
            for key, value in data['summary'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            
            writer.writerow([])
            writer.writerow(['Issues by Status'])
            writer.writerow(['Status', 'Count'])
            for item in data.get('issues_by_status', []):
                writer.writerow([item['status'].replace('_', ' ').title(), item['count']])
            
            return response
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )