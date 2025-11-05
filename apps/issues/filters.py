
import django_filters
from .models import Issue

class IssueFilter(django_filters.FilterSet):
    assignee = django_filters.UUIDFilter(field_name='assignee__id')
    assignee_email = django_filters.CharFilter(field_name='assignee__email', lookup_expr='iexact')
    reporter_email = django_filters.CharFilter(field_name='reporter__email', lookup_expr='iexact')

    class Meta:
        model = Issue
        fields = ['status', 'priority', 'assignee', 'reporter']