from .models import Comment
from rest_framework.exceptions import PermissionDenied
from apps.notifications.services import NotificationService
import re

class CommentService:
    @staticmethod
    def create_comment(user,issue,data):
        Comment=Comment.objects.create(
            author=user,
            issue=issue,**data)
        #cheeck mentions @username
        mentions=re.findall(r'@(\w+)',data['content'])
        for username in mentions:
            try:
                mentioned_user=user.objects.get(email_icontains=username)
                NotificationService.create_notification(
                    recipient=mentioned_user,
                    message=f'You were mentioned in a comment on issue {issue.title}',
                    type='mention',
                    issue=issue,

                )
            except user.DoesNotExist:
                pass
        NotificationService.create_notification(
            recipient=issue.assignee,
            message=f'New comment on issue {issue.title}',
            type='comment',
            issue=issue,
        )
        return Comment
    @staticmethod
    def update_comment(comment,data,user):
        if comment.author !=user:
            raise PermissionDenied('You can only edit your own contents')
        comment.content=data.get('content',comment.content)
        comment.save()
        return comment  
    @staticmethod
    def delete_comment(comment,user):
        if  comment.author !=user:
            raise PermissionDenied('You can only delete your own contents')
        comment.delete()

