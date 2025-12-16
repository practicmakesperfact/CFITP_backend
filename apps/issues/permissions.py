from rest_framework.permissions import BasePermission

class IsReporterOrManagerOrAdmin(BasePermission):
    """
    Allows access if user is the reporter, or has manager/admin role.
    Also checks if issue is in editable status for non-manager/admin users.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        user_role = getattr(user, 'role', None)
        
        # Admin/manager can always edit
        if user_role in ['admin', 'manager']:
            return True
            
        # Check if user is the reporter
        if user == obj.reporter:
            # Check if issue is in editable status for clients
            editable_statuses = ['open', 'reopen']
            if user_role == 'client' and obj.status not in editable_statuses:
                return False
            return True
            
        return False

# Keep your existing permission classes
class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return bool(request.user and getattr(request.user, 'role', None) == 'admin')

class IsStaffOrManager(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and getattr(request.user, 'role', None) in ['staff', 'manager', 'admin']
        )

class IsReporter(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user == obj.reporter)