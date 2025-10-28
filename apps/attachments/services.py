from .models import Attachment
from apps.issues.models import Issue
from apps.comments.models import Comment
from apps.feedback.models import Feedback

class AttachmentService:
    @staticmethod
    def upload_attachment(user, file, related_obj=None):
        data = {'uploaded_by': user, 'file': file}
        if related_obj:
            if isinstance(related_obj, Issue):
                data['issue'] = related_obj
            elif isinstance(related_obj, Comment):
                data['comment'] = related_obj
            elif isinstance(related_obj, Feedback):
                data['feedback'] = related_obj
        attachment = Attachment.objects.create(**data)
        return attachment