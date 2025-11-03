from CFIT.celery import shared_task
from django.core.mail import send_mail 
from django.conf import settings

@shared_task
def send_email_notification(recipient_email, subject, message):
    """
    Sends an email notification to the specified recipient.
    
    Args:
        recipient_email (str): The email address of the recipient.
        subject (str): The subject of the email.
        message (str): The body of the email.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=False,
    )