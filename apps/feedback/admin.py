
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from datetime import date
from .models import Feedback


class StatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'
    
    def lookups(self, request, model_admin):
        return [
            ('new', 'New'),
            ('acknowledged', 'Acknowledged'),
            ('converted', 'Converted'),
            ('closed', 'Closed'),
        ]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class HasUserFilter(admin.SimpleListFilter):
    title = 'Has User'
    parameter_name = 'has_user'
    
    def lookups(self, request, model_admin):
        return [
            ('yes', 'Has User Account'),
            ('no', 'Anonymous'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(user__isnull=False)
        elif self.value() == 'no':
            return queryset.filter(user__isnull=True)
        return queryset


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'id_short',
        'title_short',
        'status_badge',
        'user_info',
        'has_issue',
        'days_since',
        'created_date',
        'action_buttons',
    ]
    
    list_filter = [
        StatusFilter,
        HasUserFilter,
        'created_at',
    ]
    
    search_fields = [
        'title',
        'description',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]
    
    fieldsets = (
        ('Feedback Content', {
            'fields': ('title', 'description')
        }),
        ('Status & User', {
            'fields': ('status', 'user')
        }),
        ('Conversion', {
            'fields': ('converted_to',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = [
        'mark_as_acknowledged',
        'mark_as_closed',
        'clear_user',
    ]
    
    list_per_page = 25
    
    @admin.display(description='ID')
    def id_short(self, obj):
        return str(obj.id)[:8]
    
    @admin.display(description='Title')
    def title_short(self, obj):
        if len(obj.title) > 60:
            return f"{obj.title[:57]}..."
        return obj.title
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        color_map = {
            'new': '#007bff',        # Blue
            'acknowledged': '#28a745', # Green
            'converted': '#6f42c1',    # Purple
            'closed': '#6c757d',       # Gray
        }
        color = color_map.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, obj.get_status_display()
        )
    
    @admin.display(description='User')
    def user_info(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}">{}</a>',
                url, obj.user.email[:25]
            )
        return format_html(
            '<span style="color: #999; font-style: italic;">Anonymous</span>'
        )
    
    @admin.display(description='Issue', boolean=True)
    def has_issue(self, obj):
        return bool(obj.converted_to)
    
    @admin.display(description='Age')
    def days_since(self, obj):
        days = (date.today() - obj.created_at.date()).days
        if days == 0:
            return "Today"
        elif days == 1:
            return "1 day"
        elif days < 7:
            return f"{days} days"
        return f"{days}d"
    
    @admin.display(description='Created')
    def created_date(self, obj):
        return obj.created_at.strftime('%b %d')
    
    @admin.display(description='Actions')
    def action_buttons(self, obj):
        buttons = []
        
        # View button
        view_url = reverse('admin:feedback_feedback_change', args=[obj.id])
        buttons.append(f'<a href="{view_url}" style="background: #417690; color: white; padding: 2px 8px; border-radius: 3px; text-decoration: none; margin-right: 5px; font-size: 12px;">View</a>')
        
        # Convert button (if not already converted)
        if obj.status != 'converted':
            convert_url = f"{view_url}?action=convert"
            buttons.append(f'<a href="{convert_url}" style="background: #6f42c1; color: white; padding: 2px 8px; border-radius: 3px; text-decoration: none; font-size: 12px;">Convert</a>')
        
        # Link to issue (if converted)
        if obj.converted_to:
            issue_url = reverse('admin:issues_issue_change', args=[obj.converted_to.id])
            buttons.append(f'<a href="{issue_url}" style="background: #28a745; color: white; padding: 2px 8px; border-radius: 3px; text-decoration: none; margin-left: 5px; font-size: 12px;">Issue</a>')
        
        return format_html(' '.join(buttons))
    
    @admin.action(description="Mark selected as Acknowledged")
    def mark_as_acknowledged(self, request, queryset):
        updated = queryset.filter(status='new').update(status='acknowledged')
        self.message_user(request, f"{updated} feedback(s) marked as Acknowledged.")
    
    @admin.action(description="Mark selected as Closed")
    def mark_as_closed(self, request, queryset):
        updated = queryset.exclude(status='converted').update(status='closed')
        self.message_user(request, f"{updated} feedback(s) marked as Closed.")
    
    @admin.action(description="Clear user (make anonymous)")
    def clear_user(self, request, queryset):
        updated = queryset.update(user=None)
        self.message_user(request, f"{updated} feedback(s) cleared of user.")