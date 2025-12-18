
from .models import Feedback
from apps.issues.models import Issue
from apps.users.models import User
from apps.notifications.services import NotificationService
from django.contrib.auth import get_user_model

User = get_user_model()

class FeedbackService:
    
    @staticmethod
    def create_feedback(user, data):
        """Create feedback from user or anonymous"""
        feedback = Feedback.objects.create(
            title=data.get('title', 'Feedback'),
            description=data.get('description', ''),
            user=user,
            status='new'
        )
        
        # Send notification to staff about new feedback
        staff_users = User.objects.filter(role__in=['staff', 'manager', 'admin'], is_active=True)
        for staff in staff_users:
            NotificationService.create_notification(
                recipient=staff,
                message=f'New feedback submitted: "{feedback.title}"',
                type='new_feedback',  
                issue=None  # No issue yet
            )
        
        return feedback
    
    @staticmethod
    def convert_to_issue(feedback, user, issue_data):
        """Convert feedback to an issue"""
        if feedback.converted_to_issue:
            raise ValueError("Feedback already converted to issue")
        
        # Create issue from feedback
        issue = Issue.objects.create(
            title=issue_data.get('title', feedback.title),
            description=feedback.description,
            reporter=feedback.user if feedback.user else user,
            created_by=user,
            status='open',
            priority=issue_data.get('priority', 'medium')
        )
        
        # Update feedback status and link to issue
        feedback.status = 'converted'
        feedback.converted_to_issue = issue
        feedback.save()
        
        # 1. Send notification to feedback submitter
        if feedback.user:
            NotificationService.create_notification(
                recipient=feedback.user,
                message=f'Your feedback "{feedback.title}" has been converted to issue #{issue.id}',
                type='feedback_converted',
                issue=issue
            )
        
        # 2. Send notification to assignee (if specified in issue_data)
        assignee_email = issue_data.get('assignee')
        if assignee_email:
            try:
                assignee = User.objects.get(email=assignee_email)
                NotificationService.create_notification(
                    recipient=assignee,
                    message=f'New issue assigned from feedback: "{issue.title}"',
                    type='assignment',
                    issue=issue
                )
            except User.DoesNotExist:
                pass  # Skip if assignee not found
        
        # 3. Send notification to all staff (optional)
        staff_users = User.objects.filter(role__in=['staff', 'manager', 'admin'], is_active=True)
        for staff in staff_users:
            if staff != user:  # Don't notify the person who did the conversion
                NotificationService.create_notification(
                    recipient=staff,
                    message=f'Feedback converted to issue: "{issue.title}" by {user.email}',
                    type='feedback_converted',
                    issue=issue
                )
        
        return issue
    
    @staticmethod
    def get_user_feedback(user):
        """Get feedback submitted by a user"""
        return Feedback.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def acknowledge_feedback(feedback, user):
        """Mark feedback as acknowledged"""
        if feedback.status != 'new':
            return feedback
        
        feedback.status = 'acknowledged'
        feedback.save()
        
        # Notify the feedback submitter
        if feedback.user:
            NotificationService.create_notification(
                recipient=feedback.user,
                message=f'Your feedback "{feedback.title}" has been acknowledged by our team',
                type='status_change',
                issue=None
            )
        
        return feedback