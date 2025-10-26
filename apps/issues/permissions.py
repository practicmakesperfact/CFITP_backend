from rest_framework.permissions import BasePermission

class IsAdminOrReadOnly(BasePermission):
    """Allows GET access to anyone, write actions only to admins."""
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return bool(request.user and getattr(request.user, 'role', None) == 'admin')

class IsStaffOrManager(BasePermission):
    """Allows access only to users with staff, manager, or admin roles."""
    def has_permission(self, request, view):
        return bool(
            request.user and getattr(request.user, 'role', None) in ['staff', 'manager', 'admin']
        )

class IsReporter(BasePermission):
    """
    Object-level permission: allows access only if user is the reporter of the issue.
    Used for custom actions like transition_status etc.
    """
    def has_object_permission(self, request, view, obj):
        return bool(request.user == obj.reporter)
