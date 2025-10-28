from django.test import TestCase
from rest_framework.test import APIClient
from .models import Notification
from apps.users.models import User

class NotificationTests(TestCase):
    def set_up(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='password', role='client')
        Notification.objects.create(recipient=self.user, message='Test', type='new_comment')
        self.client.force_authenticate(self.user)

    def test_list_notifications(self):
        response = self.client.get('/api/v1/notifications/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)