from .models import Comment
from rest_framework.exceptions import PermissionDenied
from apps.notifications.services import NotificationService
from apps.users.models import User
from apps.attachments.models import Attachment
import re

class CommentService:
    @staticmethod
    def create_comment(user, issue, data):
        # Extract attachments from data if present (now called attachments_ids)
        attachment_ids = data.pop('attachments_ids', []) or data.pop('attachments', [])
        
        new_comment = Comment.objects.create(
            author=user,
            issue=issue,
            **data
        )
        
        # Link attachments to comment if provided
        if attachment_ids:
            Attachment.objects.filter(id__in=attachment_ids).update(comment=new_comment)
        
        # Check mentions @username or @email
        content = data.get('content', '')
        mentions = re.findall(r'@([\w.-]+@[\w.-]+\.\w+|[\w.-]+)', content)
        
        for mention in mentions:
            try:
                # Try to find user by email or username
                if '@' in mention:
                    mentioned_user = User.objects.get(email__iexact=mention)
                else:
                    # Try email contains or username
                    mentioned_user = User.objects.filter(
                        email__icontains=mention
                    ).first()
                
                if mentioned_user and mentioned_user != user:
                    NotificationService.create_notification(
                        recipient=mentioned_user,
                        message=f'You were mentioned in a comment on issue {issue.title}',
                        type='mention',
                        issue=issue,
                    )
            except User.DoesNotExist:
                pass
            except Exception as e:
                # Log error but don't fail comment creation
                print(f"Error processing mention {mention}: {e}")
        
        # Notify assignee if different from commenter
        if issue.assignee and issue.assignee != user:
            NotificationService.create_notification(
                recipient=issue.assignee,
                message=f'New comment on issue {issue.title}',
                type='comment',
                issue=issue,
            )
        
        return new_comment
    
    @staticmethod
    def update_comment(comment, data, user):
        if comment.author != user:
            raise PermissionDenied('You can only edit your own comments')
        comment.content = data.get('content', comment.content)
        comment.save()
        return comment  
    
    @staticmethod
    def delete_comment(comment, user):
        if comment.author != user:
            raise PermissionDenied('You can only delete your own comments')
        comment.delete()

