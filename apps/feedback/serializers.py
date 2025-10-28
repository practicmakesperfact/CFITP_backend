from rest_framework import serializers
from .models import Feedback
from apps.users.serializers import UserSerializer

class FeedbackSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'converted_to']