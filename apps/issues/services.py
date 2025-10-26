from .models import Issue, IssueHistory
from apps.notifications.services import NotificationService

class IssueService:
    @staticmethod
    def create_issue(user,data):
        data['reporter'] = user
        issue = Issue.objects.create(**data)
        IssueHistory.objects.create(issue=issue, changed_by=user,old_status='',new_status='open')
        return issue
    
    @staticmethod
    def assign_issue(issue, assignee,changed_by):
        old_assignee = issue.assignee
        issue.assignee = assignee
        issue.save()
        if old_assignee !=assignee:
            NotificationService.create_notification(
                recipient =assignee,
                message = f'You have been assigned to issue {issue.title}',
                type = 'assignment',
                issue = issue
            )
    @staticmethod
    def transition_status(issue,new_status,changed_by):
        old_status= issue.status
        if old_status != new_status:
            issue.status = new_status
            issue.save()
            IssueHistory.objects.create(issue=issue,changed_by=changed_by,old_status=old_status,new_status=new_status)
            NotificationService.create_notification(
                recipient=issue.assignee,
                message = f'Issue {issue.title} Status changed to {new_status}',
                type = 'status_change',
                issue = issue

            )