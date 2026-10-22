from django.contrib import admin
from .models import Profile, Document, DocumentPermission, AuditEvent


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_editable = ("role",)
    list_filter = ("role",)
    search_fields = ("user__username",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "category", "created_at")
    search_fields = ("title", "owner__username", "category")
    readonly_fields = ("sha256", "size_bytes", "created_at", "updated_at")

@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ("document", "user", "level", "granted_by", "created_at")
    list_filter = ("level",)

@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "actor_label", "action", "outcome", "document_title")
    list_filter = ("action", "outcome")
    search_fields = ("actor_label", "document_title", "event_hash")
    readonly_fields = [field.name for field in AuditEvent._meta.fields]
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
