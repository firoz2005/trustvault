from rest_framework.permissions import BasePermission
from .models import DocumentPermission

def is_admin(user):
    return bool(user and user.is_authenticated and (
        user.is_staff or (hasattr(user, "profile") and user.profile.role == "admin")
    ))

def access_level(user, document):
    if not user or not user.is_authenticated:
        return None
    if document.owner_id == user.id:
        return "owner"
    grant = DocumentPermission.objects.filter(document=document, user=user).only("level").first()
    return grant.level if grant else None

def can_read(user, document):
    return access_level(user, document) in ("owner", "read", "edit")

def can_edit(user, document):
    return access_level(user, document) in ("owner", "edit")

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user)
