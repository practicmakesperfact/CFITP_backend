from .models import Notification
from tasks import send_email_notification

class NotificationService:
    @staticmethod
    def create_notification(recipient, message, type, issue=None):
        notification = Notification.objects.create(
            recipient=recipient,
            message=message,
            type=type,
            issue=issue
        )
        # Async email
        send_email_notification.delay(recipient.email, 'New Notification', message)
        return notification

    @staticmethod
    def mark_as_read(notification):
        notification.is_read = True
        notification.save()