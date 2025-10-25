from django.test import TestCase
from rest_framework.test import APIClient
from .models import User
import uuid


class UserTests(TestCase):
    def setUp(self):
        self.client =APIClient()
        self.user = User.objects.create_user(
            id = uuid.uuid4(),
            email ='test@example.com',
            password ='password',
            role = 'client'
        )
    def test_register(self):
        response =self.client.post('/api/v1/users/register/',{
            'email' : 'new@example.com',
            'password':'password',
            'role': 'client'
        })
        self.assertEqual(response.status_code, 201)
