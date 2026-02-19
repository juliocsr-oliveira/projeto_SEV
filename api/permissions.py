from rest_framework.permissions import BasePermission


class IsAuditorOrAdmin(BasePermission):
    """Permite superuser, staff, auditores e administradores"""
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if request.user.is_staff:
            return True

        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['ADMIN', 'AUDITOR']

        return False

class IsAdmin(BasePermission):
    """Apenas Administradores"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'ADMIN'
        )

class IsOwnerOrAdmin(BasePermission):
    """Apenas o proprietário ou Administrador"""
    def has_object_permission(self, request, view, obj):
        return (
            obj.user == request.user or
            (
                hasattr(request.user, 'profile') and
                request.user.profile.role == 'ADMIN'
            )
        )