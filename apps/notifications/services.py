from .models import Notification
from .tasks import send_email_notification  # relative import
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationService:
    @staticmethod
    def create_notification(recipient, message, type, issue=None):
        """
        Create a notification and send email if recipient exists.
        Skips email if recipient is None or has no email.
        """
        if not recipient:
            # Optional: Log or skip silently
            print("Warning: NotificationService: No recipient provided. Skipping.")
            return None

        # Create notification
        notification = Notification.objects.create(
            recipient=recipient,
            message=message,
            type=type,
            issue=issue
        )

        # Send email asynchronously
        if hasattr(recipient, 'email') and recipient.email:
            try:
                send_email_notification.delay(
                    recipient.email,
                    'New Notification',
                    message
                )
            except Exception as e:
                print(f"Failed to send email for notification {notification.id}: {e}")
        else:
            print(f"Warning: User {recipient.id} has no email. Email skipped.")

        return notification

    @staticmethod
    def mark_as_read(notification):
        """Mark a notification as read."""
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read'])
        return notification