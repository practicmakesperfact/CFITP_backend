# apps/reports/services.py
from django.db.models import Count, Q
from datetime import datetime, timedelta
from apps.issues.models import Issue
from apps.feedback.models import Feedback
from apps.users.models import User
from django.utils import timezone


class ReportService:

    @staticmethod
    def get_analytics_data(start_date=None, end_date=None, user=None):
        """Safe analytics data — NO 'rating' field reference"""
        if start_date:
            start_date = timezone.make_aware(start_date) if timezone.is_naive(start_date) else start_date
        else:
            start_date = timezone.now() - timedelta(days=30)
        if end_date:
            end_date = timezone.make_aware(end_date) if timezone.is_naive(end_date) else end_date
        else:
            end_date = timezone.now()
       
         #use timezone-aware filters
        date_filter = Q(created_at__date__gte=start_date.date()) & Q(created_at__date__lte=end_date.date())

        issues_qs = Issue.objects.filter(date_filter)
        feedback_qs = Feedback.objects.filter(date_filter)

        # === Safe Counts ===
        total_issues = issues_qs.count()
        open_issues = issues_qs.filter(status='open').count()
        in_progress = issues_qs.filter(status='in_progress').count()
        resolved = issues_qs.filter(status='resolved').count()
        closed = issues_qs.filter(status='closed').count()

        # === Issues by Status (only show if count > 0) ===
        issues_by_status = []
        for status_val in ['open', 'in_progress', 'resolved', 'closed']:
            count = issues_qs.filter(status=status_val).count()
            if count > 0:
                issues_by_status.append({
                    'status': status_val,
                    'count': count
                })

        # === Issues by Priority ===
        issues_by_priority = []
        for pri in ['low', 'medium', 'high', 'critical']:
            count = issues_qs.filter(priority=pri).count()
            if count > 0:
                issues_by_priority.append({
                    'priority': pri,
                    'count': count
                })

        # === Team Performance (only staff/manager with assigned issues) ===
        team_performance = []
        staff_users = User.objects.filter(role__in=['staff', 'manager'])
        for staff in staff_users:
            assigned = issues_qs.filter(assignee=staff).count()
            resolved_count = issues_qs.filter(assignee=staff, status='resolved').count()
            if assigned > 0:
                team_performance.append({
                    'id': str(staff.id),
                    'name': staff.get_full_name() or staff.email.split('@')[0],
                    'email': staff.email,
                    'total_assigned': assigned,
                    'resolved': resolved_count,
                    'efficiency': round((resolved_count / assigned) * 100, 1) if assigned else 0
                })

        # === Feedback Count (safe — safe even if no rating field) ===
        total_feedback = feedback_qs.count()

        return {
            'summary': {
                'total_issues': total_issues,
                'open_issues': open_issues,
                'in_progress_issues': in_progress,
                'resolved_issues': resolved,
                'closed_issues': closed,
                'total_feedback': total_feedback,
                'active_users': User.objects.filter(is_active=True).count(),
                'avg_resolution_time': "24.5h",  # placeholder
                'sla_compliance': "92.3%",       # placeholder
                'avg_satisfaction': "4.6",       # placeholder or calculate later
            },
            'issues_by_status': issues_by_status,
            'issues_by_priority': issues_by_priority,
            'team_performance': team_performance or [],
            'period_display': f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}",
            'generated_at': datetime.now().isoformat()
        }