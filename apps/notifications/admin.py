
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id_short',
        'recipient_email',
        'message_short',
        'type_badge',
        'is_read_status',
        'created_ago',
        'related_issue',
    ]
    
    list_filter = [
        'type',  
        'is_read',  
        'created_at',
        'recipient__role',
    ]
    
    search_fields = [
        'message',
        'recipient__email',
        'recipient__first_name',
        'recipient__last_name',
    ]
    
    readonly_fields = [
        'created_at',
       ]
    
    fieldsets = (
        ('Notification Content', {
            'fields': ('recipient', 'message', 'type')
        }),
        ('Status & Metadata', {
            'fields': ('is_read', 'issue') 
        }),
        ('System Fields', {
            'fields': ('created_at',),  
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_read',
        'mark_as_unread',
        'delete_old_notifications',
    ]
    
    list_per_page = 25
    list_select_related = ('recipient', 'issue')
    
    @admin.display(description='ID')
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    
    @admin.display(description='Recipient')
    def recipient_email(self, obj):
        if obj.recipient:
            url = reverse('admin:users_user_change', args=[obj.recipient.id])
            return format_html(
                '<a href="{}" style="font-weight: 500;">{}</a>',
                url, obj.recipient.email[:20]
            )
        return "-"
    
    @admin.display(description='Message')
    def message_short(self, obj):
        if len(obj.message) > 50:
            return f"{obj.message[:47]}..."
        return obj.message
    
    @admin.display(description='Type')
    def type_badge(self, obj):  
        type_colors = {
            'new_issue': '#007bff',
            'assignment': '#28a745',
            'status_change': '#ffc107',
            'new_comment': '#17a2b8',
            'new_feedback': '#6f42c1',
            'feedback_converted': '#20c997',
            'mention': '#fd7e14',
        }
        
        color = type_colors.get(obj.type, '#6c757d') 
        label = obj.get_type_display()  
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">{}</span>',
            color, label
        )
    
    @admin.display(description='Read')
    def is_read_status(self, obj):  
        if obj.is_read:  
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Read</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">● Unread</span>'
        )
    
    @admin.display(description='Created')
    def created_ago(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        delta = timezone.now() - obj.created_at
        if delta.days == 0:
            if delta.seconds < 60:
                return "Just now"
            elif delta.seconds < 3600:
                return f"{delta.seconds // 60}m ago"
            else:
                return f"{delta.seconds // 3600}h ago"
        elif delta.days < 7:
            return f"{delta.days}d ago"
        else:
            return obj.created_at.strftime('%b %d, %Y')
    
    @admin.display(description='Issue')
    def related_issue(self, obj):
        if obj.issue:
            url = reverse('admin:issues_issue_change', args=[obj.issue.id])
            issue_title = obj.issue.title[:20] + "..." if len(obj.issue.title) > 20 else obj.issue.title
            return format_html(
                '<a href="{}" style="color: #0EA5A4; text-decoration: none;">#{}</a>',
                url, issue_title
            )
        return "-"
    
    @admin.action(description="Mark selected as read")
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)  
        self.message_user(request, f"{updated} notification(s) marked as read.")
    
    @admin.action(description="Mark selected as unread")
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)  
        self.message_user(request, f"{updated} notification(s) marked as unread.")
    
    @admin.action(description="Delete notifications older than 30 days")
    def delete_old_notifications(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=30)
        old_notifications = queryset.filter(created_at__lt=cutoff_date)
        count = old_notifications.count()
        old_notifications.delete()
        
        self.message_user(request, f"Deleted {count} notification(s) older than 30 days.")