
from django.contrib import admin
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from apps.users.views import UserViewSet
from apps.issues.views import IssueViewSet
from apps.comments.views import CommentViewSet
from apps.feedback.views import FeedbackViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('issues', IssueViewSet, basename='issue')
router.register('comments', CommentViewSet, basename='comment')
router.register('feedback', FeedbackViewSet, basename='feedback')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),

]
