#custom middleware for rate limiting login attempts
from django.core.cache import cache
from django.http import JsonResponse
import time

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rate limiting for login attempts
        if request.path == '/api/v1/auth/login/':
            ip = self.get_client_ip(request)
            key = f'login_attempts_{ip}'
            
            attempts = cache.get(key, 0)
            if attempts >= 5:
                return JsonResponse(
                    {'error': 'Too many login attempts. Try again later.'},
                    status=429
                )
            
            cache.set(key, attempts + 1, timeout=300)  # 5 minutes

        response = self.get_response(request)
        
        # Reset on successful login
        if request.path == '/api/v1/auth/login/' and response.status_code == 200:
            ip = self.get_client_ip(request)
            cache.delete(f'login_attempts_{ip}')
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip