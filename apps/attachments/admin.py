from django.contrib import admin
from django.utils.html import format_html
from .models import Attachment

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'mime_type', 'size_formatted', 'uploaded_by', 'created_at', 'linked_to', 'preview_thumbnail')
    list_filter = ('mime_type', 'created_at', 'uploaded_by')
    search_fields = ('filename', 'uploaded_by__email', 'uploaded_by__username')
    readonly_fields = ('mime_type', 'size', 'checksum', 'created_at', 'preview_image')
    fieldsets = (
        ('File Information', {
            'fields': ('file', 'filename', 'mime_type', 'size', 'checksum')
        }),
        ('Relationships', {
            'fields': ('issue', 'comment', 'feedback', 'uploaded_by')
        }),
        ('Preview', {
            'fields': ('preview_image',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def filename(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else 'No file'
    filename.short_description = 'Filename'

    def size_formatted(self, obj):
        if obj.size:
            if obj.size < 1024:
                return f"{obj.size} B"
            elif obj.size < 1024 * 1024:
                return f"{obj.size / 1024:.1f} KB"
            else:
                return f"{obj.size / (1024 * 1024):.1f} MB"
        return "0 B"
    size_formatted.short_description = 'Size'

    def preview_thumbnail(self, obj):
        if obj.mime_type and obj.mime_type.startswith('image/'):
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.file.url if obj.file else ''
            )
        elif obj.mime_type == 'application/pdf':
            return format_html('<span style="color: #e74c3c;">📄 PDF</span>')
        elif 'word' in obj.mime_type:
            return format_html('<span style="color: #2c3e50;">📝 DOC</span>')
        else:
            return format_html('<span style="color: #7f8c8d;">📎 File</span>')
    preview_thumbnail.short_description = 'Preview'

    def preview_image(self, obj):
        if obj.mime_type and obj.mime_type.startswith('image/'):
            return format_html(
                '<img src="{}" style="max-width: 100%; max-height: 400px;" />',
                obj.file.url if obj.file else ''
            )
        return format_html('<p>No preview available for this file type</p>')
    preview_image.short_description = 'Image Preview'

    def linked_to(self, obj):
        links = []
        if obj.issue:
            url = f"/admin/issues/issue/{obj.issue.id}/change/"
            links.append(format_html('<a href="{}">Issue: {}</a>', url, obj.issue.title[:50]))
        if obj.comment:
            url = f"/admin/comments/comment/{obj.comment.id}/change/"
            links.append(format_html('<a href="{}">Comment</a>', url))
        if obj.feedback:
            url = f"/admin/feedback/feedback/{obj.feedback.id}/change/"
            links.append(format_html('<a href="{}">Feedback</a>', url))
        return format_html(' | '.join(links)) if links else '—'
    linked_to.short_description = 'Linked To'