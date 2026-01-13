from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime
from django.http import HttpResponse, FileResponse
import csv
import os

from .models import Report
from .serializers import ReportSerializer
from apps.users.permissions import IsStaffOrManager

# Add logging
import logging
logger = logging.getLogger(__name__)


class ReportViewSet(mixins.CreateModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.ListModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    """
    API endpoint for creating, retrieving, and managing reports
    """
    
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsStaffOrManager]
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')
    
    def create(self, request, *args, **kwargs):
        """
        Create a new report generation request - NOW USES REAL CELERY
        """
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            report = serializer.instance
            
            # ✅ REAL CELERY TASK - IMPORT INSIDE FUNCTION TO AVOID CIRCULAR IMPORTS
            try:
                # CRITICAL: Import inside the function to avoid circular imports
                from .tasks import generate_report_task
                
                # Start the Celery task asynchronously
                task = generate_report_task.delay(str(report.id))
                
                # Store task ID for reference
                report.task_id = task.id
                report.save(update_fields=['task_id', 'updated_at'])
                
                logger.info(f"Started Celery task {task.id} for report {report.id}")
                print(f"✅ [DJANGO VIEW] Celery task started: {task.id} for report {report.id}")
                
            except Exception as celery_error:
                # If Celery fails, mark as failed
                logger.error(f"Failed to start Celery task: {celery_error}")
                report.status = 'failed'
                report.error_message = f"Failed to start background task: {celery_error}"
                report.save(update_fields=['status', 'error_message', 'updated_at'])
            
            headers = self.get_success_headers(serializer.data)
            return Response({
                'data': serializer.data,
                'success': True,
                'message': 'Report generation started successfully',
                'task_id': getattr(report, 'task_id', None),
                'report_id': str(report.id)
            }, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            logger.error(f"Failed to create report request: {e}")
            return Response({
                'data': None,
                'success': False,
                'error': str(e),
                'message': 'Failed to create report request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Retrieve REAL analytics data from database for dashboard visualization
        """
        try:
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
                end_date = end_date.replace(hour=23, minute=59, second=59)
            
            priority = request.query_params.get('priority', '').split(',') if request.query_params.get('priority') else []
            status_filter = request.query_params.get('status', '').split(',') if request.query_params.get('status') else []
            sla_only = request.query_params.get('sla_only', '').lower() == 'true'
            
            priority = [p for p in priority if p]
            status_filter = [s for s in status_filter if s]
            
            # ✅ Get REAL data from database (not mock)
            # IMPORT INSIDE FUNCTION to avoid circular imports
            from .services import ReportService
            
            analytics_data = ReportService.get_analytics_data(
                start_date=start_date,
                end_date=end_date,
                user=request.user,
                priority_filter=priority,
                status_filter=status_filter,
                sla_only=sla_only
            )
            
            return Response({
                'data': analytics_data,
                'success': True,
                'message': 'Analytics data retrieved successfully',
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch analytics data: {e}")
            return Response({
                'data': None,
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch analytics data'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Check the status of a report generation task
        """
        try:
            report = self.get_object()
            
            # Check if Celery task is still running
            task_status = 'unknown'
            if hasattr(report, 'task_id') and report.task_id:
                try:
                    # Import inside function to avoid circular imports
                    from celery.result import AsyncResult
                    from CFIT.celery import app
                    
                    result = AsyncResult(report.task_id, app=app)
                    task_status = result.status
                    
                    # If task failed but report status hasn't been updated
                    if result.failed() and report.status != 'failed':
                        report.status = 'failed'
                        report.error_message = str(result.result)
                        report.save(update_fields=['status', 'error_message', 'updated_at'])
                    
                except Exception as task_error:
                    task_status = 'unknown'
                    logger.error(f"Failed to check Celery task status: {task_error}")
            
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
                    'result_path': report.result_path.url if report.result_path else None,
                    'task_status': task_status,
                    'error_message': report.error_message
                },
                'success': True
            })
            
        except Exception as e:
            logger.error(f"Failed to get report status: {e}")
            return Response({
                'data': None,
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """
        Quick CSV export endpoint for dashboard data - USES REAL DATA
        """
        try:
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
                end_date = end_date.replace(hour=23, minute=59, second=59)
            
            priority = request.query_params.get('priority', '').split(',') if request.query_params.get('priority') else []
            status_filter = request.query_params.get('status', '').split(',') if request.query_params.get('status') else []
            
            priority = [p for p in priority if p]
            status_filter = [s for s in status_filter if s]
            
            # ✅ Get REAL data from database
            # IMPORT INSIDE FUNCTION to avoid circular imports
            from .services import ReportService
            
            data = ReportService.get_analytics_data(
                start_date=start_date,
                end_date=end_date,
                user=request.user,
                priority_filter=priority,
                status_filter=status_filter
            )
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="cfitp_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            writer = csv.writer(response)
            
            writer.writerow(['CFITP Analytics Dashboard Export'])
            writer.writerow([f'Period: {data.get("period_display", "N/A")}'])
            writer.writerow([f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'])
            writer.writerow([f'Generated by: {request.user.email}'])
            writer.writerow([])
            
            writer.writerow(['SUMMARY METRICS'])
            writer.writerow(['Metric', 'Value'])
            for key, value in data.get('summary', {}).items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])
            
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
            logger.error(f"CSV export failed: {e}")
            return Response({
                "error": str(e),
                "detail": "CSV export failed"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download a generated report file - NOW SERVES REAL FILES
        """
        try:
            report = self.get_object()
            
            # Check if report is ready
            if report.status != 'generated' or not report.result_path:
                return Response({
                    'error': 'Report not ready for download',
                    'status': report.status,
                    'result_available': bool(report.result_path)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if file exists on disk
            file_path = report.result_path.path if hasattr(report.result_path, 'path') else str(report.result_path)
            
            if not os.path.exists(file_path):
                return Response({
                    'error': 'Report file not found on server'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Return the REAL file
            response = FileResponse(
                open(file_path, 'rb'),
                as_attachment=True,
                filename=os.path.basename(file_path)
            )
            
            # Set appropriate content type
            if file_path.endswith('.pdf'):
                response['Content-Type'] = 'application/pdf'
            elif file_path.endswith('.csv'):
                response['Content-Type'] = 'text/csv'
            elif file_path.endswith('.xlsx'):
                response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to download report: {e}")
            return Response({
                'error': str(e),
                'detail': 'Failed to download report'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """
        Quick metrics endpoint using REAL database data
        """
        try:
            user_reports = Report.objects.filter(user=request.user)
            
            # Get active report tasks
            pending_tasks = user_reports.filter(status='processing').count()
            
            metrics_data = {
                'total_reports': user_reports.count(),
                'generated_reports': user_reports.filter(status='generated').count(),
                'processing_reports': pending_tasks,
                'pending_reports': user_reports.filter(status='pending').count(),
                'failed_reports': user_reports.filter(status='failed').count(),
                'recent_reports': ReportSerializer(
                    user_reports.order_by('-created_at')[:5], 
                    many=True
                ).data,
                'report_types': {
                    'performance_dashboard': user_reports.filter(type='performance_dashboard').count(),
                    'team_member_performance': user_reports.filter(type='team_member_performance').count(),
                    'issue_summary': user_reports.filter(type='issue_summary').count(),
                },
                'report_formats': {
                    'pdf': user_reports.filter(format='pdf').count(),
                    'csv': user_reports.filter(format='csv').count(),
                    'xlsx': user_reports.filter(format='xlsx').count(),
                }
            }
            
            return Response({
                'data': metrics_data,
                'success': True,
                'message': 'Metrics retrieved successfully'
            })
            
        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            return Response({
                'data': None,
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch metrics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)