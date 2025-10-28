from django.test import TestCase
from apps.issues.models import Issue
from django.contrib.auth import get_user_model

User = get_user_model()

class CommentTests(TestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='testuser@gmail.com',
              password='password',
              role='user'
              )
        # Log in as the user if needed
        self.client.login(username='testuser', password='password')
        # Create an issue instance and assign to self.issue
        self.issue = Issue.objects.create(
            title='Test Issue',
            description='Description',
            reporter=self.user,  
            created_by=self.user
        )

    def test_create_comment(self):
        response = self.client.post(
            f'/api/v1/issues/{self.issue.id}/comments/', 
            {'content': 'Test comment'}
        )
        
