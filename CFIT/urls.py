# config/urls.py or CFIT/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Import ViewSets
from apps.users.views import UserViewSet, UserRegisterView, UserProfileView, UserLogoutView
from apps.issues.views import IssueViewSet
from apps.comments.views import CommentViewSet
from apps.feedback.views import FeedbackViewSet
from apps.attachments.views import AttachmentViewSet
from apps.notifications.views import NotificationViewSet
from apps.reports.views import ReportViewSet

# Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'issues', IssueViewSet, basename='issue')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'reports', ReportViewSet, basename='report')

# Nested router for comments under issues
comment_router = DefaultRouter()
comment_router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # JWT Auth
    path('api/v1/auth/register/', UserRegisterView.as_view(), name='auth-register'),
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='auth-login'),
    path('api/v1/auth/logout/', UserLogoutView.as_view(), name='auth-logout'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('api/v1/users/me/', UserProfileView.as_view(), name='user-profile'),

    # Main API
    path('api/v1/', include(router.urls)),

    # Nested: Comments under Issues
    path('api/v1/issues/<uuid:issue_pk>/', include(comment_router.urls)),

    # Issue Actions
    path('api/v1/issues/<uuid:pk>/assign/', IssueViewSet.as_view({'post': 'assign'}), name='issue-assign'),
    path('api/v1/issues/<uuid:pk>/transition/', IssueViewSet.as_view({'post': 'transition'}), name='issue-transition'),

    # Feedback Action
    path('api/v1/feedback/<uuid:pk>/convert/', FeedbackViewSet.as_view({'post': 'convert_to_issue'}), name='feedback-convert'),

    # Notification Action
    path('api/v1/notifications/<uuid:pk>/mark-read/', NotificationViewSet.as_view({'post': 'mark_read'}), name='notification-mark-read'),

    # Attachment Download
    path('api/v1/attachments/<uuid:pk>/download/', AttachmentViewSet.as_view({'get': 'download'}), name='attachment-download'),
]

# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)