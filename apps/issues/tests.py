from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from .models import Issue
from apps.users.models import User


class IssueTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password',
            role='staff'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_issue(self):
        response = self.client.post(reverse('issue-list'), {
            'title': 'Test Issue',
            'description': 'Description',
            'priority': 'medium',
            'status': 'open',
        })

        # Print for debugging if something fails
        print(response.status_code, response.data)

        # Ensure the API returns 201 Created
        self.assertEqual(response.status_code, 201)

        # Verify the issue was actually created and linked to the logged-in user
        issue = Issue.objects.get(title='Test Issue')
        self.assertEqual(issue.reporter, self.user)