# apps/issues/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import date
from .models import Issue, IssueHistory


# Custom filters
class StatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return [
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class PriorityFilter(admin.SimpleListFilter):
    title = 'Priority'
    parameter_name = 'priority'
    
    def lookups(self, request, model_admin):
        return [
            ('critical', 'Critical'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(priority=self.value())
        return queryset


class OverdueFilter(admin.SimpleListFilter):
    title = 'Overdue'
    parameter_name = 'overdue'
    
    def lookups(self, request, model_admin):
        return [
            ('yes', 'Overdue'),
            ('no', 'Not Overdue'),
        ]
    
    def queryset(self, request, queryset):
        today = date.today()
        if self.value() == 'yes':
            return queryset.filter(
                due_date__lt=today,
                status__in=['open', 'in_progress']
            )
        elif self.value() == 'no':
            return queryset.exclude(
                due_date__lt=today,
                status__in=['open', 'in_progress']
            )
        return queryset


class AssignedFilter(admin.SimpleListFilter):
    title = 'Assignment'
    parameter_name = 'assigned'
    
    def lookups(self, request, model_admin):
        return [
            ('assigned', 'Assigned'),
            ('unassigned', 'Unassigned'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'assigned':
            return queryset.filter(assignee__isnull=False)
        elif self.value() == 'unassigned':
            return queryset.filter(assignee__isnull=True)
        return queryset


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    # List view configuration
    list_display = [
        'id_short',
        'title_truncated',
        'status_colored',
        'priority',  # Use actual field name for list_editable
        'reporter_info',
        'assignee_info',
        'due_date_colored',
        'days_open',
        'created_date',
    ]
    
    list_editable = ['priority']  # Now 'priority' is in list_display
    
    list_filter = [
        StatusFilter,
        PriorityFilter,
        OverdueFilter,
        AssignedFilter,
        'created_at',
    ]
    
    search_fields = [
        'title',
        'description',
        'reporter__email',
        'reporter__first_name',
        'reporter__last_name',
        'assignee__email',
        'assignee__first_name',
        'assignee__last_name',
    ]
    
    # Detail view configuration
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Assignment', {
            'fields': ('reporter', 'assignee', 'due_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    # Actions
    actions = [
        'mark_as_in_progress',
        'mark_as_resolved', 
        'mark_as_closed',
        'assign_to_current_user',
        'clear_assignee',
    ]
    
    list_per_page = 50
    
    # Custom display methods
    @admin.display(description='ID', ordering='id')
    def id_short(self, obj):
        return str(obj.id)[:8]
    
    @admin.display(description='Title', ordering='title')
    def title_truncated(self, obj):
        if len(obj.title) > 60:
            return f"{obj.title[:57]}..."
        return obj.title
    
    @admin.display(description='Status')
    def status_colored(self, obj):
        color_map = {
            'open': '#007bff',      # Blue
            'in_progress': '#fd7e14', # Orange
            'resolved': '#28a745',   # Green
            'closed': '#6c757d',     # Gray
        }
        color = color_map.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, obj.get_status_display()
        )
    
    @admin.display(description='Reporter')
    def reporter_info(self, obj):
        url = reverse('admin:users_user_change', args=[obj.reporter.id])
        return format_html(
            '<a href="{}">{}</a><br><small style="color: #666;">{}</small>',
            url, obj.reporter.email[:20], obj.created_at.strftime('%b %d')
        )
    
    @admin.display(description='Assignee')
    def assignee_info(self, obj):
        if obj.assignee:
            url = reverse('admin:users_user_change', args=[obj.assignee.id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.assignee.email[:20]
            )
        return format_html(
            '<span style="color: #999; font-style: italic;">Unassigned</span>'
        )
    
    @admin.display(description='Due Date', ordering='due_date')
    def due_date_colored(self, obj):
        if not obj.due_date:
            return format_html('<span style="color: #999;">—</span>')
        
        today = date.today()
        if obj.due_date < today and obj.status in ['open', 'in_progress']:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">{} ⚠</span>',
                obj.due_date
            )
        elif obj.due_date == today:
            return format_html(
                '<span style="color: #fd7e14; font-weight: bold;">{} ⚡</span>',
                obj.due_date
            )
        return obj.due_date
    
    @admin.display(description='Age')
    def days_open(self, obj):
        days = (date.today() - obj.created_at.date()).days
        if days == 0:
            return "Today"
        elif days == 1:
            return "1 day"
        elif days < 7:
            return f"{days} days"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''}"
    
    @admin.display(description='Created', ordering='created_at')
    def created_date(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    
    # Custom actions
    @admin.action(description="Mark selected as In Progress")
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.filter(status='open').update(status='in_progress')
        self.message_user(request, f"{updated} issue(s) marked as In Progress.")
    
    @admin.action(description="Mark selected as Resolved")
    def mark_as_resolved(self, request, queryset):
        updated = queryset.filter(status='in_progress').update(status='resolved')
        self.message_user(request, f"{updated} issue(s) marked as Resolved.")
    
    @admin.action(description="Mark selected as Closed")
    def mark_as_closed(self, request, queryset):
        updated = queryset.filter(status='resolved').update(status='closed')
        self.message_user(request, f"{updated} issue(s) marked as Closed.")
    
    @admin.action(description="Assign to me")
    def assign_to_current_user(self, request, queryset):
        updated = queryset.update(assignee=request.user)
        self.message_user(request, f"{updated} issue(s) assigned to you.")
    
    @admin.action(description="Clear assignee")
    def clear_assignee(self, request, queryset):
        updated = queryset.update(assignee=None)
        self.message_user(request, f"{updated} issue(s) cleared of assignee.")


@admin.register(IssueHistory)
class IssueHistoryAdmin(admin.ModelAdmin):
    # List view
    list_display = [
        'issue_title',
        'changed_by_email',
        'status_change_display',
        'timestamp_formatted',
    ]
    
    list_filter = [
        'new_status',
        'timestamp',
    ]
    
    search_fields = [
        'issue__title',
        'changed_by__email',
        'changed_by__first_name',
        'changed_by__last_name',
    ]
    
    readonly_fields = [
        'issue', 'changed_by', 'old_status', 'new_status', 'timestamp'
    ]
    
    date_hierarchy = 'timestamp'
    list_per_page = 100
    
    # Custom display methods
    @admin.display(description='Issue', ordering='issue__title')
    def issue_title(self, obj):
        url = reverse('admin:issues_issue_change', args=[obj.issue.id])
        title = obj.issue.title[:50] + '...' if len(obj.issue.title) > 50 else obj.issue.title
        return format_html('<a href="{}">{}</a>', url, title)
    
    @admin.display(description='Changed By', ordering='changed_by__email')
    def changed_by_email(self, obj):
        if obj.changed_by:
            url = reverse('admin:users_user_change', args=[obj.changed_by.id])
            return format_html('<a href="{}">{}</a>', url, obj.changed_by.email)
        return "System"
    
    @admin.display(description='Status Change')
    def status_change_display(self, obj):
        color_map = {
            'open': '#007bff',
            'in_progress': '#fd7e14', 
            'resolved': '#28a745',
            'closed': '#6c757d',
        }
        old_color = color_map.get(obj.old_status, '#6c757d')
        new_color = color_map.get(obj.new_status, '#6c757d')
        
        return format_html(
            '''
            <span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; margin-right: 5px;">{}</span>
            <span>→</span>
            <span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; margin-left: 5px;">{}</span>
            ''',
            old_color, obj.old_status.capitalize(),
            new_color, obj.new_status.capitalize()
        )
    
    @admin.display(description='Timestamp', ordering='timestamp')
    def timestamp_formatted(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M')
    
    # Disable add permission (history should be auto-generated)
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete history
        return request.user.is_superuser