from django.test import TestCase
from rest_framework.test import APIClient
from .models import Issue
from apps.users.models import User
import uuid

class IssueTests(TestCase):
    def set_up(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='password', role='staff')
        self.client.force_authenticate(self.user)

    def test_create_issue(self):
        response = self.client.post('/api/v1/issues/', {
            'title': 'Test Issue',
            'description': 'Desc',
            'priority': 'medium'
        })
        self.assertEqual(response.status_code, 201)  