from django.contrib import admin
from .models import Issue, IssueHistory

admin.site.register(Issue)
admin.site.register(IssueHistory)