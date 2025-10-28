from .models import Feedback
from apps.issues.services import IssueService
from apps.notifications.services import NotificationService

class FeedbackService:
    @staticmethod
    def create_feedback(user=None, data={}):
        if user:
            data['user'] = user
        feedback = Feedback.objects.create(**data)
        return feedback

    @staticmethod
    def convert_to_issue(feedback, user, issue_data):
        if feedback.status == 'converted':
            raise ValueError("Already converted")
        issue_data['reporter'] = feedback.user or user
        issue = IssueService.create_issue(user, issue_data)
        feedback.converted_to = issue
        feedback.status = 'converted'
        feedback.save()
        NotificationService.create_notification(
            recipient=feedback.user,
            message=f'Your feedback "{feedback.title}" has been converted to an issue',
            type='feedback_converted',
            issue=issue
        )
        return issue