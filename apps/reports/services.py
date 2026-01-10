from django.db.models import Count, Q, Avg
from datetime import timedelta
from apps.issues.models import Issue
from apps.feedback.models import Feedback
from apps.users.models import User
from django.utils import timezone

class ReportService:
    """
    Service class for generating analytics and report data
    """

    @staticmethod
    def get_analytics_data(start_date=None, end_date=None, user=None,
                          priority_filter=None, status_filter=None,
                          sla_only=False, high_priority_only=False,
                          include_feedback=True):
        """
        Generate comprehensive analytics data for dashboard reports
        Returns structured data with all KPIs, charts, and performance metrics
        """
        
        # Set default date range if not provided
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        # Ensure timezone awareness
        if timezone.is_naive(start_date):
            start_date = timezone.make_aware(start_date)
        if timezone.is_naive(end_date):
            end_date = timezone.make_aware(end_date)
        
        # Base date filter for all queries
        base_filter = Q(created_at__gte=start_date) & Q(created_at__lte=end_date)
        issues_qs = Issue.objects.filter(base_filter)
        
        # Apply optional filters
        if priority_filter and priority_filter != ['']:
            issues_qs = issues_qs.filter(priority__in=priority_filter)
        
        if status_filter and status_filter != ['']:
            issues_qs = issues_qs.filter(status__in=status_filter)
        
        if sla_only:
            issues_qs = issues_qs.filter(
                Q(due_date__lt=timezone.now()) |
                Q(due_date__lt=timezone.now() + timedelta(hours=24))
            )
        
        if high_priority_only:
            issues_qs = issues_qs.filter(priority__in=['high', 'critical'])
        
        # Basic issue counts by status
        total_issues = issues_qs.count()
        open_issues = issues_qs.filter(status='open').count()
        in_progress = issues_qs.filter(status='in_progress').count()
        resolved = issues_qs.filter(status='resolved').count()
        closed = issues_qs.filter(status='closed').count()
        
        # Calculate KPIs
        team_efficiency = ReportService._calculate_team_efficiency(issues_qs)
        first_response_time = ReportService._calculate_first_response_time(issues_qs)
        reopen_rate = ReportService._calculate_reopen_rate(issues_qs, resolved, closed)
        sla_compliance = ReportService._calculate_sla_compliance(issues_qs)
        avg_resolution_time = ReportService._calculate_avg_resolution_time(issues_qs)
        
        # Generate issues by status breakdown
        issues_by_status = []
        for status_val, display_name in Issue.STATUS_CHOICES:
            count = issues_qs.filter(status=status_val).count()
            if count > 0 or total_issues == 0:
                percentage = round((count / total_issues * 100), 1) if total_issues > 0 else 0
                issues_by_status.append({
                    'status': status_val,
                    'status_display': display_name,
                    'count': count,
                    'percentage': percentage
                })
        
        # Generate issues by priority breakdown
        issues_by_priority = []
        for pri, display_name in Issue.PRIORITY_CHOICES:
            count = issues_qs.filter(priority=pri).count()
            percentage = round((count / total_issues * 100), 1) if total_issues > 0 else 0
            issues_by_priority.append({
                'priority': pri,
                'priority_display': display_name,
                'count': count,
                'percentage': percentage
            })
        
        # Generate team performance data
        team_performance = ReportService._get_team_performance_data(start_date, end_date)
        
        # Feedback analysis
        feedback_qs = Feedback.objects.filter(base_filter)
        total_feedback = feedback_qs.count()
        avg_satisfaction = ReportService._calculate_avg_satisfaction(feedback_qs)
        
        # Compile final response
        return {
            'summary': {
                'total_issues': total_issues,
                'open_issues': open_issues,
                'in_progress_issues': in_progress,
                'resolved_issues': resolved,
                'closed_issues': closed,
                'total_feedback': total_feedback,
                'active_users': User.objects.filter(is_active=True).count(),
                
                'avg_resolution_time': f"{avg_resolution_time:.1f}h",
                'avg_resolution_time_hours': avg_resolution_time,
                'first_response_time': f"{first_response_time:.1f}h",
                'first_response_time_hours': first_response_time,
                'team_efficiency': f"{team_efficiency:.1f}%",
                'team_efficiency_percentage': team_efficiency,
                'reopen_rate': f"{reopen_rate:.1f}%",
                'reopen_rate_percentage': reopen_rate,
                'sla_compliance': f"{sla_compliance:.1f}%",
                'sla_compliance_percentage': sla_compliance,
                'avg_satisfaction': str(avg_satisfaction),
            },
            'issues_by_status': issues_by_status,
            'issues_by_priority': issues_by_priority,
            'team_performance': team_performance,
            'period_display': f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}",
            'generated_at': timezone.now().isoformat(),
        }
    
    @staticmethod
    def _get_team_performance_data(start_date, end_date):
        """
        Generate performance data for all staff and manager users
        Includes assigned, resolved, pending counts and efficiency metrics
        """
        team_performance = []
        
        staff_users = User.objects.filter(
            role__in=['staff', 'manager'],
            is_active=True
        )
        
        for staff in staff_users:
            assigned_count = Issue.objects.filter(
                assignee=staff,
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            
            resolved_count = Issue.objects.filter(
                assignee=staff,
                status__in=['resolved', 'closed'],
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            
            pending_count = Issue.objects.filter(
                assignee=staff,
                status__in=['open', 'in_progress'],
                created_at__gte=start_date,
                created_at__lte=end_date
            ).count()
            
            efficiency = round((resolved_count / assigned_count * 100), 1) if assigned_count > 0 else 0
            
            avg_resolution = ReportService._calculate_staff_avg_resolution(
                staff, start_date, end_date
            )
            
            team_performance.append({
                'id': str(staff.id),
                'name': staff.get_full_name() or staff.email.split('@')[0],
                'email': staff.email,
                'role': staff.get_role_display(),
                'role_value': staff.role,
                'total_assigned': assigned_count,
                'resolved': resolved_count,
                'pending': pending_count,
                'efficiency': efficiency,
                'avg_resolution_time_hours': avg_resolution,
            })
        
        # Sort by efficiency (highest first)
        team_performance.sort(key=lambda x: x['efficiency'], reverse=True)
        return team_performance
    
    @staticmethod
    def _calculate_staff_avg_resolution(staff, start_date, end_date):
        """
        Calculate average resolution time for a specific staff member
        """
        avg_resolution = 0
        resolved_issues = Issue.objects.filter(
            assignee=staff,
            status__in=['resolved', 'closed'],
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if resolved_issues.exists():
            total_hours = 0
            count = 0
            
            for issue in resolved_issues:
                if hasattr(issue, 'resolved_at') and issue.resolved_at:
                    resolution_time = issue.resolved_at - issue.created_at
                elif issue.updated_at and issue.created_at:
                    resolution_time = issue.updated_at - issue.created_at
                else:
                    continue
                
                hours = resolution_time.total_seconds() / 3600
                total_hours += hours
                count += 1
            
            if count > 0:
                avg_resolution = round(total_hours / count, 1)
        
        return avg_resolution
    
    @staticmethod
    def _calculate_team_efficiency(issues_qs):
        """
        Calculate team efficiency percentage
        Efficiency = (resolved assigned issues / total assigned issues) * 100
        """
        assigned_issues = issues_qs.filter(assignee__isnull=False)
        assigned_count = assigned_issues.count()
        resolved_assigned = assigned_issues.filter(
            status__in=['resolved', 'closed']
        ).count()
        
        if assigned_count > 0:
            return round((resolved_assigned / assigned_count) * 100, 1)
        return 0.0
    
    @staticmethod
    def _calculate_first_response_time(issues_qs):
        """
        Calculate average first response time in hours
        """
        issues_with_comments = issues_qs.filter(
            comments__isnull=False
        ).distinct()
        
        if not issues_with_comments.exists():
            return 0.0
        
        total_hours = 0
        count = 0
        
        for issue in issues_with_comments:
            first_comment = issue.comments.order_by('created_at').first()
            if first_comment and issue.created_at:
                response_time = first_comment.created_at - issue.created_at
                hours = response_time.total_seconds() / 3600
                total_hours += hours
                count += 1
        
        return round(total_hours / count, 1) if count > 0 else 0.0
    
    @staticmethod
    def _calculate_reopen_rate(issues_qs, resolved_count, closed_count):
        """
        Calculate issue reopen rate percentage
        Reopen rate = (reopened issues / total resolved issues) * 100
        """
        total_resolved = resolved_count + closed_count
        reopened_count = issues_qs.filter(status='reopened').count()
        
        if total_resolved > 0:
            return round((reopened_count / total_resolved) * 100, 1)
        return 0.0
    
    @staticmethod
    def _calculate_sla_compliance(issues_qs):
        """
        Calculate SLA compliance percentage
        """
        issues_with_due_date = issues_qs.exclude(due_date__isnull=True)
        
        if not issues_with_due_date.exists():
            return 100.0
        
        compliant_count = 0
        current_time = timezone.now()
        
        for issue in issues_with_due_date:
            if issue.status in ['resolved', 'closed'] and issue.resolved_at:
                if issue.resolved_at <= issue.due_date:
                    compliant_count += 1
            elif issue.status in ['open', 'in_progress']:
                if current_time <= issue.due_date:
                    compliant_count += 1
        
        return round((compliant_count / issues_with_due_date.count()) * 100, 1)
    
    @staticmethod
    def _calculate_avg_resolution_time(issues_qs):
        """
        Calculate average resolution time in hours for resolved issues
        """
        resolved_issues = issues_qs.filter(
            status__in=['resolved', 'closed']
        )
        
        if not resolved_issues.exists():
            return 0.0
        
        total_hours = 0
        count = 0
        
        for issue in resolved_issues:
            if hasattr(issue, 'resolved_at') and issue.resolved_at:
                resolution_time = issue.resolved_at - issue.created_at
            elif issue.updated_at and issue.created_at:
                resolution_time = issue.updated_at - issue.created_at
            else:
                continue
            
            hours = resolution_time.total_seconds() / 3600
            total_hours += hours
            count += 1
        
        return round(total_hours / count, 1) if count > 0 else 0.0
    
    @staticmethod
    def _calculate_avg_satisfaction(feedback_qs):
        """
        Calculate average satisfaction rating from feedback
        """
        try:
            avg_rating = feedback_qs.exclude(rating__isnull=True).aggregate(
                avg=Avg('rating')
            )['avg']
            
            if avg_rating is not None:
                return round(avg_rating, 1)
            return "N/A"
        except:
            return "N/A"