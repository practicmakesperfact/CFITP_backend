
from django.contrib import admin
from django.urls import path,include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView,TokenBlacklistView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/',TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/logout/',TokenBlacklistView.as_view(),name='token_blacklist'),
    path('api/v1/', include('apps.users.urls')),
    path('api/v1/', include('apps.issues.urls')),
    # path('api/v1/', include('apps.comments.urls')),
    # path('api/v1/', include('apps.feedback.urls')),
    # path('api/v1/', include('apps.attachments.urls')),
    # path('api/v1/', include('apps.notifications.urls')),
    # path('api/v1/', include('apps.reports.urls')),
    #swagger
    path('api/schema/', SpectacularAPIView.as_view(),name='schema'),
    path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'),name='swagger-ui'),
]
