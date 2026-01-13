from celery import shared_task
from .models import Report
from .services import ReportService
from django.utils import timezone
from django.core.files.base import ContentFile
import json
import csv
import io
from datetime import datetime
import logging
import os
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def generate_report_task(self, report_id):
    """Background task to generate report files - FIXED FOR IN-MEMORY CELERY"""
    print(f"🎯 [CELERY TASK STARTED] Report ID: {report_id}")
    
    try:
        # Get report from database
        with transaction.atomic():
            report = Report.objects.select_for_update().get(id=report_id)
            print(f"✅ [CELERY] Found report: {report.id}, User: {report.user.email}, Initial status: {report.status}")
            
            # Update to processing
            report.status = 'processing'
            report.save(update_fields=['status', 'updated_at'])
            print(f"📊 [CELERY] Report status set to 'processing'")
        
        # Get parameters
        params = report.parameters
        print(f"📋 [CELERY] Report parameters: {params}")
        
        # Extract date parameters
        start_date = None
        end_date = None
        
        if params.get('start_date'):
            start_date = datetime.fromisoformat(params.get('start_date'))
            if timezone.is_naive(start_date):
                start_date = timezone.make_aware(start_date)
        
        if params.get('end_date'):
            end_date = datetime.fromisoformat(params.get('end_date'))
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        
        print(f"📅 [CELERY] Date range: {start_date} to {end_date}")
        
        # Get priority and status filters
        priority_filter = params.get('priority', [])
        if isinstance(priority_filter, str):
            priority_filter = [p.strip() for p in priority_filter.split(',') if p.strip()]
        
        status_filter = params.get('status', [])
        if isinstance(status_filter, str):
            status_filter = [s.strip() for s in status_filter.split(',') if s.strip()]
        
        # Get REAL data from database
        print(f"📊 [CELERY] Fetching analytics data...")
        data = ReportService.get_analytics_data(
            start_date=start_date,
            end_date=end_date,
            user=report.user,
            priority_filter=priority_filter,
            status_filter=status_filter,
            sla_only=params.get('sla_only', False),
            high_priority_only=params.get('high_priority_only', False),
            include_feedback=params.get('include_feedback', True)
        )
        print(f"✅ [CELERY] Got analytics data with {data.get('summary', {}).get('total_issues', 0)} issues")
        
        # Generate file based on format
        filename = f"report_{report.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"📄 [CELERY] Creating file: {filename}, Format: {report.format}")
        
        if report.format == 'csv':
            content = generate_csv(data, report.user)
            file_extension = '.csv'
        elif report.format == 'json':
            content = json.dumps(data, indent=2, default=str)
            file_extension = '.json'
        elif report.format == 'pdf':
            content = generate_pdf(data, report.user)
            file_extension = '.pdf'
        else:
            # Default to CSV
            content = generate_csv(data, report.user)
            file_extension = '.csv'
        
        # Save file to report model
        filename_with_ext = f"{filename}{file_extension}"
        print(f"💾 [CELERY] Saving file: {filename_with_ext}")
        
        # Create content file
        if isinstance(content, str):
            file_content = ContentFile(content.encode('utf-8'))
        else:
            file_content = ContentFile(content)
        
        # Save the file and update status
        with transaction.atomic():
            # Get fresh report instance
            fresh_report = Report.objects.get(id=report_id)
            
            # Save the file
            fresh_report.result_path.save(
                filename_with_ext,
                file_content
            )
            
            # Update status to generated
            fresh_report.status = 'generated'
            fresh_report.save(update_fields=['status', 'result_path', 'updated_at'])
            
            print(f"✅ [CELERY] File saved to: {fresh_report.result_path}")
        
        # Final verification
        final_report = Report.objects.get(id=report_id)
        print(f"✅ [CELERY TASK COMPLETED] Report {report_id} generated successfully.")
        print(f"📊 [CELERY] Final status: {final_report.status}")
        print(f"📁 [CELERY] Final file: {final_report.result_path}")
        
        # Log success
        logger.info(f"Report {report_id} generated successfully. File: {fresh_report.result_path.name}")
        
        # Return success response
        return {
            'success': True,
            'report_id': str(report_id),
            'status': 'generated',
            'file_path': str(fresh_report.result_path),
            'file_url': fresh_report.result_path.url if fresh_report.result_path else None
        }
        
    except Exception as e:
        print(f"❌ [CELERY TASK FAILED] Report {report_id}: {str(e)}")
        logger.error(f"Failed to generate report {report_id}: {str(e)}", exc_info=True)
        
        # Update report status to failed with error message
        try:
            with transaction.atomic():
                failed_report = Report.objects.get(id=report_id)
                failed_report.status = 'failed'
                failed_report.error_message = str(e)[:500]  # Limit error message length
                failed_report.save(update_fields=['status', 'error_message', 'updated_at'])
                
                print(f"⚠️ [CELERY] Report marked as failed: {failed_report.error_message}")
        except Exception as save_error:
            print(f"⚠️ [CELERY] Failed to save error status: {save_error}")
        
        # Retry the task
        print(f"🔄 [CELERY] Retrying task...")
        raise self.retry(exc=e, countdown=30)  # Retry after 30 seconds

def generate_csv(data, user):
    """Generate CSV content from REAL database data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['CFITP ANALYTICS DASHBOARD REPORT'])
    writer.writerow([f"Period: {data.get('period_display', 'N/A')}"])
    writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([f"Generated by: {user.email}"])
    writer.writerow([])
    
    # Write summary metrics
    writer.writerow(['SUMMARY METRICS'])
    writer.writerow(['Metric', 'Value'])
    
    summary = data.get('summary', {})
    for key, value in summary.items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    writer.writerow([])
    
    # Write issues by status
    issues_by_status = data.get('issues_by_status', [])
    if issues_by_status:
        writer.writerow(['ISSUES BY STATUS'])
        writer.writerow(['Status', 'Count', 'Percentage'])
        for item in issues_by_status:
            writer.writerow([
                item.get('status_display', item.get('status', 'Unknown')),
                item.get('count', 0),
                f"{item.get('percentage', 0)}%"
            ])
        writer.writerow([])
    
    # Write issues by priority
    issues_by_priority = data.get('issues_by_priority', [])
    if issues_by_priority:
        writer.writerow(['ISSUES BY PRIORITY'])
        writer.writerow(['Priority', 'Count', 'Percentage'])
        for item in issues_by_priority:
            writer.writerow([
                item.get('priority_display', item.get('priority', 'Unknown')),
                item.get('count', 0),
                f"{item.get('percentage', 0)}%"
            ])
        writer.writerow([])
    
    # Write team performance
    team_performance = data.get('team_performance', [])
    if team_performance:
        writer.writerow(['TEAM PERFORMANCE'])
        writer.writerow(['Name', 'Email', 'Role', 'Assigned', 'Resolved', 'Pending', 'Efficiency %', 'Avg. Resolution (hours)'])
        for member in team_performance:
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
    
    return output.getvalue()

def generate_pdf(data, user):
    """Generate PDF content from data using ReportLab (REAL DATA)"""
    print(f"📄 [CELERY] Generating PDF...")
    try:
        # Check if ReportLab is installed
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from io import BytesIO
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Custom styles
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0EA5A4')  # Your teal color
        )
        
        # Heading style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.HexColor('#334155')  # Your text color
        )
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Container for elements
        elements = []
        
        # Title
        title = Paragraph("CFITP Analytics Dashboard Report", title_style)
        elements.append(title)
        
        # Metadata
        elements.append(Paragraph(f"<b>Period:</b> {data.get('period_display', 'N/A')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Generated by:</b> {user.email}", styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Summary Metrics
        elements.append(Paragraph("Summary Metrics", heading_style))
        
        summary = data.get('summary', {})
        summary_data = [['Metric', 'Value']]
        
        # Add key metrics
        key_metrics = ['total_issues', 'open_issues', 'in_progress_issues', 
                      'resolved_issues', 'closed_issues', 'team_efficiency',
                      'avg_resolution_time', 'first_response_time', 
                      'sla_compliance', 'reopen_rate']
        
        for metric in key_metrics:
            if metric in summary:
                display_name = metric.replace('_', ' ').title()
                summary_data.append([display_name, str(summary[metric])])
        
        # Create summary table
        summary_table = Table(
            summary_data, 
            colWidths=[3*inch, 2*inch],
            hAlign='LEFT'
        )
        
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0EA5A4')),  # Teal header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),  # Your bg color
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Page break for detailed data
        elements.append(PageBreak())
        
        # Issues by Status
        issues_by_status = data.get('issues_by_status', [])
        if issues_by_status:
            elements.append(Paragraph("Issues by Status", heading_style))
            
            status_data = [['Status', 'Count', 'Percentage']]
            for item in issues_by_status:
                status_data.append([
                    item.get('status_display', item.get('status', 'Unknown')),
                    str(item.get('count', 0)),
                    f"{item.get('percentage', 0)}%"
                ])
            
            status_table = Table(
                status_data,
                colWidths=[2*inch, 1.5*inch, 1.5*inch],
                hAlign='LEFT'
            )
            
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),  # Blue header
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            
            elements.append(status_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Issues by Priority
        issues_by_priority = data.get('issues_by_priority', [])
        if issues_by_priority:
            elements.append(Paragraph("Issues by Priority", heading_style))
            
            priority_data = [['Priority', 'Count', 'Percentage']]
            for item in issues_by_priority:
                priority_data.append([
                    item.get('priority_display', item.get('priority', 'Unknown')),
                    str(item.get('count', 0)),
                    f"{item.get('percentage', 0)}%"
                ])
            
            priority_table = Table(
                priority_data,
                colWidths=[2*inch, 1.5*inch, 1.5*inch],
                hAlign='LEFT'
            )
            
            priority_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F59E0B')),  # Orange header
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavenderblush),
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            
            elements.append(priority_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Team Performance
        team_performance = data.get('team_performance', [])
        if team_performance:
            elements.append(Paragraph("Team Performance", heading_style))
            
            team_data = [['Name', 'Assigned', 'Resolved', 'Pending', 'Efficiency %']]
            for member in team_performance[:10]:  # Limit to top 10
                team_data.append([
                    member.get('name', 'N/A'),
                    str(member.get('total_assigned', 0)),
                    str(member.get('resolved', 0)),
                    str(member.get('pending', 0)),
                    f"{member.get('efficiency', 0)}%"
                ])
            
            team_table = Table(
                team_data,
                colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch],
                hAlign='LEFT'
            )
            
            team_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),  # Green header
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0FDF4')),  # Light green
                ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))
            
            elements.append(team_table)
        
        # Footer note
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            "<i>Note: This report was generated automatically by the CFITP system. "
            "All data is based on real-time database records.</i>",
            ParagraphStyle(
                'Footer',
                parent=styles['Italic'],
                fontSize=9,
                textColor=colors.gray,
                alignment=TA_CENTER
            )
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf = buffer.getvalue()
        buffer.close()
        
        print(f"✅ [CELERY] PDF generated successfully")
        return pdf
        
    except ImportError as e:
        logger.warning(f"ReportLab not installed: {e}. Using simple PDF fallback.")
        print(f"⚠️ [CELERY] ReportLab not installed, using fallback")
        return generate_simple_pdf(data, user)
    except Exception as e:
        logger.error(f"PDF generation error: {e}. Using simple fallback.")
        print(f"⚠️ [CELERY] PDF generation error: {e}, using fallback")
        return generate_simple_pdf(data, user)

def generate_simple_pdf(data, user):
    """Fallback PDF generation without ReportLab"""
    print(f"📄 [CELERY] Generating simple PDF fallback")
    content = f"""
    CFITP ANALYTICS DASHBOARD REPORT
    =================================
    
    Period: {data.get('period_display', 'N/A')}
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Generated by: {user.email}
    
    SUMMARY METRICS
    ---------------
    """
    
    summary = data.get('summary', {})
    for key, value in summary.items():
        content += f"{key.replace('_', ' ').title()}: {value}\n"
    
    issues_by_status = data.get('issues_by_status', [])
    if issues_by_status:
        content += "\nISSUES BY STATUS\n----------------\n"
        for item in issues_by_status:
            content += f"{item.get('status_display', item.get('status', 'Unknown'))}: {item.get('count', 0)} ({item.get('percentage', 0)}%)\n"
    
    issues_by_priority = data.get('issues_by_priority', [])
    if issues_by_priority:
        content += "\nISSUES BY PRIORITY\n------------------\n"
        for item in issues_by_priority:
            content += f"{item.get('priority_display', item.get('priority', 'Unknown'))}: {item.get('count', 0)} ({item.get('percentage', 0)}%)\n"
    
    team_performance = data.get('team_performance', [])
    if team_performance:
        content += "\nTEAM PERFORMANCE\n----------------\n"
        for member in team_performance[:10]:  # Limit to top 10
            content += f"{member.get('name', 'N/A')}: Assigned={member.get('total_assigned', 0)}, "
            content += f"Resolved={member.get('resolved', 0)}, "
            content += f"Pending={member.get('pending', 0)}, "
            content += f"Efficiency={member.get('efficiency', 0)}%\n"
    
    content += "\n" + "="*50 + "\n"
    content += "Generated by CFITP (Client Feedback & Issue Tracking Portal)\n"
    content += "All data is based on real-time database records\n"
    
    print(f" [CELERY] Simple PDF content created")
    return content