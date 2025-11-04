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

        # Use new title/description from request
        new_title = issue_data.get('title', feedback.title)
        new_description = issue_data.get('description', feedback.description)

        issue_data['reporter'] = feedback.user or user
        issue_data['title'] = new_title
        issue_data['description'] = new_description

        issue = IssueService.create_issue(user, issue_data)

        # UPDATE FEEDBACK
        feedback.converted_to = issue
        feedback.status = 'converted'
        feedback.title = new_title
        feedback.description = new_description
        feedback.save()

        # Notify only if user exists
        if feedback.user:
            NotificationService.create_notification(
                recipient=feedback.user,
                message=f'Your feedback "{new_title}" has been converted to an issue',
                type='feedback_converted',
                issue=issue
            )

        return issue