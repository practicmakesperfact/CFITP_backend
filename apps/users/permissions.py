from rest_framework.permissions import BasePermission


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['Get']:
            return True
        return request.user and request.user.role =='admin'

class IsStaffOrManager(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ['staff','manager','admin']

class IsReporter(BasePermission):
    def has_permission(self, request, view,obj):
        return request.user == obj.reporter

class IsManagerOrAdmin(BasePermission):
    """Allow access only to Manager or Admin users."""
    
    def has_permission(self, request, view):
        return request.user and request.user.role in ['manager', 'admin']