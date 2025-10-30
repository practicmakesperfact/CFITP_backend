from django.test import TestCase
from rest_framework.test import APIClient
from .models import Report
from apps.users.models import User
from unittest.mock import patch

class ReportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='test@example.com', password='password', role='manager')
        self.client.force_authenticate(user=self.user)

    def test_request_report(self):
        with patch('apps.reports.services.generate_report.delay') as mock_delay:
            response = self.client.post(
                '/api/v1/reports/',
                {'type': 'issues_by_status', 'user': str(self.user.id)},
                format='json'
            )
            mock_delay.assert_called_once()
            self.assertEqual(response.status_code, 201, f"Response: {response.status_code} {response.data}")