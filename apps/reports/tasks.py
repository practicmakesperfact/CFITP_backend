from celery import shared_task
from .models import Report
from .services import ReportService
from django.utils import timezone
from django.core.files.base import ContentFile
import json
import csv
import io
from datetime import datetime

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
        else:  # pdf (default)
            content = generate_pdf(data)
            file_extension = '.pdf'
            content_type = 'application/pdf'
        
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
        if 'report' in locals():
            report.status = 'failed'
            report.error_message = str(e)
            report.save()
        raise e

def generate_csv(data):
    """Generate CSV content from data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write summary
    writer.writerow(['CFITP Analytics Report'])
    writer.writerow([f"Period: {data.get('period_display', 'N/A')}"])
    writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([])
    writer.writerow(['Summary Metrics'])
    writer.writerow(['Metric', 'Value'])
    
    for key, value in data.get('summary', {}).items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    # Write issues by status if available
    if 'issues_by_status' in data and data['issues_by_status']:
        writer.writerow([])
        writer.writerow(['Issues by Status'])
        writer.writerow(['Status', 'Count'])
        for item in data['issues_by_status']:
            writer.writerow([item.get('status_display', item.get('status', 'Unknown')), item.get('count', 0)])
    
    # Write issues by priority if available
    if 'issues_by_priority' in data and data['issues_by_priority']:
        writer.writerow([])
        writer.writerow(['Issues by Priority'])
        writer.writerow(['Priority', 'Count'])
        for item in data['issues_by_priority']:
            writer.writerow([item.get('priority_display', item.get('priority', 'Unknown')), item.get('count', 0)])
    
    return output.getvalue()

def generate_pdf(data):
    """Generate PDF content from data using ReportLab"""
    try:
        # Check if ReportLab is installed
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Container for the 'Flowable' objects
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("CFITP Analytics Report", styles['Title'])
        elements.append(title)
        
        # Period
        period = Paragraph(f"Period: {data.get('period_display', 'N/A')}", styles['Normal'])
        elements.append(period)
        
        # Generated date
        generated = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])
        elements.append(generated)
        
        elements.append(Spacer(1, 0.25*inch))
        
        # Summary Metrics
        elements.append(Paragraph("Summary Metrics", styles['Heading2']))
        
        # Create summary table
        summary_data = [['Metric', 'Value']]
        for key, value in data.get('summary', {}).items():
            summary_data.append([key.replace('_', ' ').title(), str(value)])
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Issues by Status
        if 'issues_by_status' in data and data['issues_by_status']:
            elements.append(Paragraph("Issues by Status", styles['Heading2']))
            
            status_data = [['Status', 'Count']]
            for item in data['issues_by_status']:
                status_data.append([
                    item.get('status_display', item.get('status', 'Unknown')),
                    str(item.get('count', 0))
                ])
            
            status_table = Table(status_data, colWidths=[2.5*inch, 2.5*inch])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(status_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Issues by Priority
        if 'issues_by_priority' in data and data['issues_by_priority']:
            elements.append(Paragraph("Issues by Priority", styles['Heading2']))
            
            priority_data = [['Priority', 'Count']]
            for item in data['issues_by_priority']:
                priority_data.append([
                    item.get('priority_display', item.get('priority', 'Unknown')),
                    str(item.get('count', 0))
                ])
            
            priority_table = Table(priority_data, colWidths=[2.5*inch, 2.5*inch])
            priority_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(priority_table)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf = buffer.getvalue()
        buffer.close()
        
        return pdf
        
    except ImportError:
        # Fallback to simple text if ReportLab is not installed
        return generate_simple_pdf(data)

def generate_simple_pdf(data):
    """Fallback PDF generation without ReportLab"""
    content = f"""
    CFITP Analytics Report
    =====================
    
    Period: {data.get('period_display', 'N/A')}
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Summary Metrics:
    ----------------
    """
    
    for key, value in data.get('summary', {}).items():
        content += f"{key.replace('_', ' ').title()}: {value}\n"
    
    if 'issues_by_status' in data and data['issues_by_status']:
        content += "\nIssues by Status:\n----------------\n"
        for item in data['issues_by_status']:
            content += f"{item.get('status_display', item.get('status', 'Unknown'))}: {item.get('count', 0)}\n"
    
    if 'issues_by_priority' in data and data['issues_by_priority']:
        content += "\nIssues by Priority:\n------------------\n"
        for item in data['issues_by_priority']:
            content += f"{item.get('priority_display', item.get('priority', 'Unknown'))}: {item.get('count', 0)}\n"
    
    return content