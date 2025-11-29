
from .models import Feedback
from apps.issues.models import Issue
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

        # Use new title/description from request or fallback to original
        new_title = issue_data.get('title', feedback.title) or "Feedback Issue"
        new_description = issue_data.get('description', feedback.description) or ""

        # CREATE ISSUE DIRECTLY — NO IssueService NEEDED!
        issue = Issue.objects.create(
            title=new_title,
            description=new_description,
            reporter=feedback.user or user,
            created_by=user,
            priority=issue_data.get('priority', 'medium'),
            type=issue_data.get('type', 'feedback'),
        )

        # Update feedback
        feedback.converted_to = issue
        feedback.status = 'converted'
        feedback.title = new_title
        feedback.description = new_description
        feedback.save()

        # Send notification if user exists
        if feedback.user:
            NotificationService.create_notification(
                recipient=feedback.user,
                message=f'Your feedback "{new_title}" has been converted to an issue',
                type='feedback_converted',
                issue=issue
            )

        return issue