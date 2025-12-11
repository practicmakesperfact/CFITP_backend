
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
import csv
import json
from io import StringIO
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.utils.text import slugify
import uuid

class LightReportService:
    """
    Lightweight reporting service without heavy dependencies
    """
    
    @staticmethod
    def get_analytics_data(start_date=None, end_date=None, user=None):
        """Get analytics using Django ORM only"""
        from apps.issues.models import Issue
        from apps.feedback.models import Feedback
        from apps.users.models import User
        
        # Set default dates
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Base queryset
        date_filter = Q(created_at__gte=start_date, created_at__lte=end_date)
        
        # Simple counts with Django ORM
        issues_qs = Issue.objects.filter(date_filter)
        feedback_qs = Feedback.objects.filter(date_filter)
        
        # Calculate metrics
        total_issues = issues_qs.count()
        
        # Status distribution
        status_counts = {}
        for status, label in Issue.STATUS_CHOICES:
            count = issues_qs.filter(status=status).count()
            if count > 0:
                status_counts[status] = {
                    'status': status,
                    'label': label,
                    'count': count
                }
        
        # Priority distribution
        priority_counts = {}
        for priority, label in Issue.PRIORITY_CHOICES:
            count = issues_qs.filter(priority=priority).count()
            if count > 0:
                priority_counts[priority] = {
                    'priority': priority,
                    'label': label,
                    'count': count
                }
        
        # Feedback stats
        total_feedback = feedback_qs.count()
        avg_rating = feedback_qs.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Team performance (simple)
        team_data = []
        from apps.users.models import User
        for staff in User.objects.filter(role__in=['staff', 'manager']):
            assigned = issues_qs.filter(assignee=staff).count()
            resolved = issues_qs.filter(assignee=staff, status='resolved').count()
            
            if assigned > 0:
                team_data.append({
                    'id': str(staff.id),
                    'name': staff.get_full_name() or staff.email,
                    'email': staff.email,
                    'assigned': assigned,
                    'resolved': resolved,
                    'efficiency': round((resolved / assigned) * 100, 1) if assigned > 0 else 0
                })
        
        # Daily trend (last 7 days)
        trend_data = []
        for i in range(7):
            day = end_date - timedelta(days=6 - i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())
            
            day_issues = Issue.objects.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()
            
            day_feedback = Feedback.objects.filter(
                created_at__gte=day_start,
                created_at__lte=day_end
            ).count()
            
            trend_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'day': day.strftime('%a'),
                'issues': day_issues,
                'feedback': day_feedback
            })
        
        return {
            'summary': {
                'total_issues': total_issues,
                'open_issues': issues_qs.filter(status='open').count(),
                'in_progress_issues': issues_qs.filter(status='in_progress').count(),
                'resolved_issues': issues_qs.filter(status='resolved').count(),
                'total_feedback': total_feedback,
                'avg_satisfaction': round(avg_rating, 1),
                'active_users': User.objects.filter(is_active=True).count(),
                'sla_compliance': 0,  # You can calculate this if you have due_date field
                'avg_resolution_time': 0,  # You can calculate this if you have resolved_at field
            },
            'issues_by_status': list(status_counts.values()),
            'issues_by_priority': list(priority_counts.values()),
            'team_performance': team_data,
            'trends': {
                'daily': trend_data,
                'period': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'days': 7
                }
            },
            'timestamp': datetime.now().isoformat(),
            'period_display': f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        }
    
    @staticmethod
    def generate_csv_response(data, filename_prefix="report"):
        """Generate CSV response without pandas"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        # Summary section
        writer.writerow(['SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        for key, value in data['summary'].items():
            writer.writerow([key.replace('_', ' ').title(), value])
        writer.writerow([])
        
        # Issues by status
        writer.writerow(['ISSUES BY STATUS'])
        writer.writerow(['Status', 'Count'])
        for item in data.get('issues_by_status', []):
            writer.writerow([item['status'].replace('_', ' ').title(), item['count']])
        writer.writerow([])
        
        # Team performance
        if data.get('team_performance'):
            writer.writerow(['TEAM PERFORMANCE'])
            writer.writerow(['Name', 'Email', 'Assigned', 'Resolved', 'Efficiency %'])
            for member in data['team_performance']:
                writer.writerow([
                    member['name'],
                    member['email'],
                    member['assigned'],
                    member['resolved'],
                    member['efficiency']
                ])
        
        return response
    
    @staticmethod
    def generate_json_response(data, filename_prefix="report"):
        """Generate JSON response"""
        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d")}.json"'
        return response
    
    @staticmethod
    def generate_html_report(data, title="Analytics Report"):
        """Generate simple HTML report (can be saved as HTML or printed)"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #0EA5A4; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #0EA5A4; color: white; }}
                .summary {{ background-color: #f8fafc; padding: 20px; border-radius: 8px; }}
                .metric {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="summary">
                <h2>Summary Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for key, value in data['summary'].items():
            html_content += f'<tr><td>{key.replace("_", " ").title()}</td><td>{value}</td></tr>'
        
        html_content += """
                </table>
            </div>
            
            <div>
                <h2>Issues by Status</h2>
                <table>
                    <tr><th>Status</th><th>Count</th></tr>
        """
        
        for item in data.get('issues_by_status', []):
            html_content += f'<tr><td>{item["status"].replace("_", " ").title()}</td><td>{item["count"]}</td></tr>'
        
        html_content += """
                </table>
            </div>
        </body>
        </html>
        """
        
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="report_{datetime.now().strftime("%Y%m%d")}.html"'
        return response