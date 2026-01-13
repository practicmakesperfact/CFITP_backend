
# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from rest_framework.routers import DefaultRouter
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView,SpectacularRedocView

# # Import ViewSets
# from apps.users.views import UserViewSet
# from apps.issues.views import IssueViewSet
# from apps.comments.views import CommentViewSet
# from apps.feedback.views import FeedbackViewSet
# from apps.attachments.views import AttachmentViewSet
# from apps.notifications.views import NotificationViewSet
# from apps.reports.views import ReportViewSet

# # Router
# router = DefaultRouter()
# router.register(r'users', UserViewSet, basename='user')
# router.register(r'issues', IssueViewSet, basename='issue')
# router.register(r'feedback', FeedbackViewSet, basename='feedback')
# router.register(r'attachments', AttachmentViewSet, basename='attachment')
# router.register(r'notifications', NotificationViewSet, basename='notification')
# router.register(r'reports', ReportViewSet, basename='report')
# router.register(r'comments', CommentViewSet, basename='comment')

# # Nested router for comments under issues
# comment_router = DefaultRouter()
# comment_router.register(r'comments', CommentViewSet, basename='comment')

# urlpatterns = [
#     # Admin
#     path('admin/', admin.site.urls),

#     # API Schema & Docs
#     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
#     path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
#     path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

#     # JWT Auth
#     # path('api/v1/auth/register/', UserRegisterView.as_view(), name='auth-register'),
#     path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='auth-login'),
#     # path('api/v1/auth/logout/', UserLogoutView.as_view(), name='auth-logout'),
#     path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
#     # path('api/v1/users/me/', UserProfileView.as_view(), name='user-profile'),

#     # Main API
#     path('api/v1/', include(router.urls)),

#     # Nested: Comments under Issues
#     path('api/v1/issues/<uuid:issue_pk>/', include(comment_router.urls)),

#     # Issue Actions
#     path('api/v1/issues/<uuid:pk>/assign/', IssueViewSet.as_view({'post': 'assign'}), name='issue-assign'),
#     path('api/v1/issues/<uuid:pk>/transition/', IssueViewSet.as_view({'post': 'transition'}), name='issue-transition'),

#     # Feedback Action
#     path('api/v1/feedback/<uuid:pk>/convert/', FeedbackViewSet.as_view({'post': 'convert_to_issue'}), name='feedback-convert'),

#     # Notification Action
#     path('api/v1/notifications/<uuid:pk>/mark-read/', NotificationViewSet.as_view({'post': 'mark_read'}), name='notification-mark-read'),

#     # Attachment Download
#     path('api/v1/attachments/<uuid:pk>/download/', AttachmentViewSet.as_view({'get': 'download'}), name='attachment-download'),
# ]

# # Serve media in development
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# CFIT/urls.py (main urls)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Import ViewSets
from apps.users.views import UserViewSet, CustomLoginView, LogoutView
from apps.issues.views import IssueHistoryViewSet, IssueViewSet
from apps.comments.views import CommentViewSet
from apps.feedback.views import FeedbackViewSet
from apps.attachments.views import AttachmentViewSet
from apps.notifications.views import NotificationViewSet
from apps.reports.views import ReportViewSet
from apps.issues.views import IssueHistoryViewSet

# Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'issues', IssueViewSet, basename='issue')
router.register(r'issue-history', IssueHistoryViewSet, basename='issue-history')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'attachments', AttachmentViewSet, basename='attachment')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'comments', CommentViewSet, basename='comment')

# Nested router for comments under issues
comment_router = DefaultRouter()
comment_router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Schema & Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # JWT Auth (UPDATED)
    path('api/v1/auth/login/', CustomLoginView.as_view(), name='auth-login'),
    path('api/v1/auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    
    # Registration is now handled by /api/v1/users/register/

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
    # Reports analytics endpoints
    path('api/v1/reports/analytics/', ReportViewSet.as_view({'get': 'analytics'}), name='report-analytics'),
    path('api/v1/reports/metrics/', ReportViewSet.as_view({'get': 'metrics'}), name='report-metrics'),
    path('api/v1/reports/export/', ReportViewSet.as_view({'get': 'export'}), name='report-export'),
    path('api/v1/reports/<uuid:pk>/status/', ReportViewSet.as_view({'get': 'status'}), name='report-status'),
    path('api/v1/reports/<uuid:pk>/download/', ReportViewSet.as_view({'get': 'download'}), name='report-download'),


    path('api/v1/users/admin/', UserViewSet.as_view({'get': 'admin_users_list'}), name='admin-users-list'),
]

# Serve media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
   