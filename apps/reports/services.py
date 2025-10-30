from .models import Report
from apps.issues.models import Issue
from apps.feedback.models import Feedback
import csv
from io import StringIO
from django.core.files.base import ContentFile
from tasks import send_email_notification  
from celery import shared_task

class ReportService:
    @staticmethod
    def request_report(user, report_type):
        report = Report.objects.create(user=user, type=report_type)
        generate_report.delay(report.id)  
        return report

@shared_task
def generate_report(report_id):
    report = Report.objects.get(id=report_id)
    try:
        data = []
        if report.type == 'issues_by_status':
            data = Issue.objects.values('status').annotate(count=models.Count('id'))
        elif report.type == 'issues_by_assignee':
            data = Issue.objects.values('assignee__email').annotate(count=models.Count('id'))
        elif report.type == 'issues_by_priority':
            data = Issue.objects.values('priority').annotate(count=models.Count('id'))
        elif report.type == 'feedback_summary':
            data = Feedback.objects.values('status').annotate(count=models.Count('id'))

        output = StringIO()
        writer = csv.writer(output)
        for row in data:
            writer.writerow(row.values())

        report.result_path.save(f'report_{report_id}.csv', ContentFile(output.getvalue()))
        report.status = 'generated'
        report.save()
        # Notify user
        send_email_notification.delay(report.user.email, 'Report Ready', 'Your report is generated.')
    except Exception as e:
        report.status = 'failed'
        report.save()