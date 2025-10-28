from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

class AttachmentTests(TestCase):
    def set_up(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='password', role='client')
        self.client.force_authenticate(self.user)

    def test_upload(self):
        file = SimpleUploadedFile("file.txt", b"content", "text/plain")
        response = self.client.post('/api/v1/attachments/', {'file': file}, format='multipart')
        self.assertEqual(response.status_code, 201)