
from celery import shared_task
from .models import Report
from .services import ReportService
from django.utils import timezone
import csv
import json
from django.core.files.base import ContentFile
import os

@shared_task
def generate_report_task(report_id):
    """Background task to generate report files"""
    try:
        report = Report.objects.get(id=report_id)
        report.status = 'processing'
        report.save()
        
        # Get data from ReportService
        params = report.parameters
        data = ReportService.get_analytics_data(
            start_date=params.get('start_date'),
            end_date=params.get('end_date'),
            user=report.user,
            report_type=report.type,
            priority_filter=params.get('priority', []),
            status_filter=params.get('status', [])
        )
        
        # Generate file based on format
        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        if report.format == 'csv':
            content = generate_csv(data)
            file_extension = '.csv'
            content_type = 'text/csv'
        elif report.format == 'json':
            content = json.dumps(data, indent=2, default=str)
            file_extension = '.json'
            content_type = 'application/json'
        elif report.format == 'pdf':
            # PDF generation would use reportlab or weasyprint
            content = generate_pdf_placeholder(data)
            file_extension = '.pdf'
            content_type = 'application/pdf'
        else:  # excel
            content = generate_excel(data)
            file_extension = '.xlsx'
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Save file to report model
        filename_with_ext = f"{filename}{file_extension}"
        report.result_path.save(
            filename_with_ext,
            ContentFile(content.encode() if isinstance(content, str) else content),
            save=False
        )
        
        report.status = 'generated'
        report.save()
        
        return f"Report {report_id} generated successfully"
        
    except Exception as e:
        report.status = 'failed'
        report.error_message = str(e)
        report.save()
        raise e

def generate_csv(data):
    """Generate CSV content from data"""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write summary
    writer.writerow(['CFITP Analytics Report'])
    writer.writerow([f"Period: {data.get('period_display', 'N/A')}"])
    writer.writerow([])
    writer.writerow(['Summary Metrics'])
    writer.writerow(['Metric', 'Value'])
    
    for key, value in data.get('summary', {}).items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    return output.getvalue()

def generate_excel(data):
    """Generate Excel content from data"""
    from openpyxl import Workbook
    from io import BytesIO
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    
    # Add data to Excel
    ws.append(['CFITP Analytics Report'])
    ws.append([f"Period: {data.get('period_display', 'N/A')}"])
    ws.append([])
    ws.append(['Summary Metrics'])
    ws.append(['Metric', 'Value'])
    
    for key, value in data.get('summary', {}).items():
        ws.append([key.replace('_', ' ').title(), value])
    
    # Save to bytes
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

def generate_pdf_placeholder(data):
    """Placeholder for PDF generation"""
    return f"PDF Report for {data.get('period_display', 'N/A')}"