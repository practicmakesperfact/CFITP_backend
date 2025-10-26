from rest_framework import serializers
from .models import Issue, IssueHistory
from apps.users.serializers import UserSerializer

class IssueSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)

    class Meta:
        model = Issue
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at','reporter')

class IssueHistorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = IssueHistory
        fields = '__all__'