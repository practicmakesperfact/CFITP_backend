from rest_framework import serializers
from .models import Issue, IssueHistory
from apps.users.serializers import UserSerializer

class IssueSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    reporter_email = serializers.CharField(source='reporter.email', read_only=True)
    assignee_email = serializers.CharField(source='assignee.email', read_only=True, allow_null=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    class Meta:
        model = Issue
        fields = '__all__'
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'reporter',
            'created_by',  'reporter_email',
            'assignee_email', 'created_by_email'
        )


class IssueHistorySerializer(serializers.ModelSerializer):
    issue = IssueSerializer(read_only=True)
    changed_by = UserSerializer(read_only=True)

    class Meta:
        model = IssueHistory
        fields = '__all__'