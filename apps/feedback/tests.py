from django.test import TestCase
from rest_framework.test import APIClient
from .models import Feedback

class FeedbackTests(TestCase):
    def set_up(self):
        self.client = APIClient()

    def test_create_feedback_unauth(self):
        response = self.client.post('/api/v1/feedback/', {'title': 'Test', 'description': 'Desc'})
        self.assertEqual(response.status_code, 201)