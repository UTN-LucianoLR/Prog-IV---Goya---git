from rest_framework import permissions
from .models import SecurityLog
from .services import MembershipService


class IsProjectAdminOrReadOnly(permissions.BasePermission):
    """
    Cualquier miembro del proyecto puede leer.
    Solo un admin del proyecto puede modificar (editar/borrar).
    Sirve tanto para Task (obj.project) como para Project (obj).
    """

    def has_object_permission(self, request, view, obj):
        project = obj.project if hasattr(obj, "project") else obj
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return MembershipService.is_member(request.user, project)
        is_admin = MembershipService.is_admin(request.user, project)
        if not is_admin:
            ip = request.META.get("REMOTE_ADDR")
            user = request.user if getattr(request.user, "is_authenticated", False) else None
            model_name = getattr(obj._meta, "model_name", "object")
            obj_id = getattr(obj, "id", "")
            SecurityLog.objects.create(
                user=user,
                action="permission_denied",
                detail=f"Intento de {request.method} sobre {model_name} {obj_id} sin rol admin",
                ip_address=ip,
            )
        return is_admin

