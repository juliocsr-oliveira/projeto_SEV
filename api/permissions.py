from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Apenas Administradores"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'ADMIN'
        )


class IsAuditorOrAdmin(BasePermission):
    """Apenas Auditores ou Administradores"""
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role in ['AUDITOR', 'ADMIN']
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