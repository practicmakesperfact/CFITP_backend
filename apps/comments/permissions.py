from apps.issues.permissions import IsAdminOrReadOnly, IsStaffOrManager
from rest_framework.permissions import BasePermission

class IsAuthor(BasePermission):
    """
    Object-level permission: allows access only if user is the author of the comment.
    Used for editing or deleting comments.
    """
    def has_object_permission(self, request, view, obj):
        return bool(request.user == obj.author)
