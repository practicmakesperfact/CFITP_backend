
from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet
from apps.issues.views import IssueViewSet
from apps.comments.views import CommentViewSet
from apps.feedback.views import FeedbackViewSet
from apps.attachments.views import AttachmentViewSet
from apps.notifications.views import NotificationViewSet
from apps.reports.views import ReportViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('issues', IssueViewSet, basename='issue')
router.register('comments', CommentViewSet, basename='comment')
router.register('feedback', FeedbackViewSet, basename='feedback')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('reports', ReportViewSet, basename='report')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),

]
