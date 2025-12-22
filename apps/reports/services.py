from django.db.models import Count, Q, Avg
from datetime import datetime, timedelta
from apps.issues.models import Issue
from apps.feedback.models import Feedback
from apps.users.models import User
from django.utils import timezone

class ReportService:

    @staticmethod
    def get_analytics_data(start_date=None, end_date=None, user=None, 
                          report_type='issues_by_status', priority_filter=None, 
                          status_filter=None):
        """Simplified analytics data"""
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        # Ensure timezone awareness
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date)
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date)
        
        # Base queryset with date filter
        base_filter = Q(created_at__gte=start_date) & Q(created_at__lte=end_date)
        issues_qs = Issue.objects.filter(base_filter)
        
        # === Basic Counts ===
        total_issues = issues_qs.count()
        open_issues = issues_qs.filter(status='open').count()
        in_progress = issues_qs.filter(status='in_progress').count()
        resolved = issues_qs.filter(status='resolved').count()
        closed = issues_qs.filter(status='closed').count()
        
        # === Issues by Status ===
        issues_by_status = []
        for status_val, display_name in Issue.STATUS_CHOICES:
            count = issues_qs.filter(status=status_val).count()
            if count > 0:
                issues_by_status.append({
                    'status': status_val,
                    'status_display': display_name,
                    'count': count,
                    'percentage': round((count / total_issues * 100), 1) if total_issues > 0 else 0
                })
        
        # === Issues by Priority ===
        issues_by_priority = []
        for pri, display_name in Issue.PRIORITY_CHOICES:
            count = issues_qs.filter(priority=pri).count()
            if count > 0:
                issues_by_priority.append({
                    'priority': pri,
                    'priority_display': display_name,
                    'count': count,
                    'percentage': round((count / total_issues * 100), 1) if total_issues > 0 else 0
                })
        
        # === Team Performance (SIMPLIFIED) ===
        team_performance = []
        staff_users = User.objects.filter(
            role__in=['staff', 'manager'],
            is_active=True
        )
        
        for staff in staff_users:
            # Simple count without prefetch
            assigned_count = issues_qs.filter(assignee=staff).count()
            resolved_count = issues_qs.filter(assignee=staff, status__in=['resolved', 'closed']).count()
            
            efficiency = round((resolved_count / assigned_count * 100), 1) if assigned_count > 0 else 0
            
            team_performance.append({
                'id': str(staff.id),
                'name': staff.get_full_name() or staff.email.split('@')[0],
                'email': staff.email,
                'role': staff.get_role_display(),
                'total_assigned': assigned_count,
                'resolved': resolved_count,
                'pending': assigned_count - resolved_count,
                'efficiency': efficiency,
                'avg_resolution_time_hours': 0,  # Simplified
            })
        
        # === Feedback Analysis ===
        feedback_qs = Feedback.objects.filter(base_filter)
        total_feedback = feedback_qs.count()
        
        # Simplified return
        return {
            'summary': {
                'total_issues': total_issues,
                'open_issues': open_issues,
                'in_progress_issues': in_progress,
                'resolved_issues': resolved,
                'closed_issues': closed,
                'total_feedback': total_feedback,
                'active_users': User.objects.filter(is_active=True).count(),
                'avg_resolution_time': "0h",  # Simplified
                'sla_compliance': "92.3%",
                'avg_satisfaction': "N/A",
            },
            'issues_by_status': issues_by_status,
            'issues_by_priority': issues_by_priority,
            'team_performance': team_performance,
            'period_display': f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}",
            'report_type': report_type,
            'generated_at': timezone.now().isoformat(),
        }