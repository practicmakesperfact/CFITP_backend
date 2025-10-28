from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

class AttachmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password',
            role='client'
        )
        self.client.force_authenticate(user=self.user)

    def test_upload(self):
        file = SimpleUploadedFile("file.pdf", b"Test content", content_type="application/pdf")
        url = reverse('attachment-list')
        response = self.client.post(url, {'file': file}, format='multipart')
        print(response.status_code, getattr(response, 'data', response.content))
        self.assertEqual(response.status_code, 201)
