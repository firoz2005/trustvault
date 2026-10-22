import os
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Document, DocumentPermission, AuditEvent, Profile

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".csv"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf", "text/plain", "image/png", "image/jpeg",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv", "application/csv", "application/octet-stream",
}

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Profile.objects.get_or_create(user=user, defaults={"role": "viewer"})
        return user

class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]

class DocumentSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    class Meta:
        model = Document
        fields = ["id", "title", "category", "owner", "original_filename", "size_bytes",
                  "sha256", "created_at", "updated_at", "can_edit", "can_delete"]
        read_only_fields = ["id", "owner", "original_filename", "size_bytes", "sha256", "created_at", "updated_at"]
    def get_can_edit(self, obj):
        from .permissions import can_edit
        return can_edit(self.context["request"].user, obj)
    def get_can_delete(self, obj):
        return obj.owner_id == self.context["request"].user.id

class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    class Meta:
        model = Document
        fields = ["id", "title", "category", "file"]
        read_only_fields = ["id"]
    def validate_title(self, value):
        value = value.strip()
        if not value or len(value) > 200:
            raise serializers.ValidationError("Title must contain 1–200 characters.")
        return value
    def validate_category(self, value):
        if len(value) > 80:
            raise serializers.ValidationError("Category must be 80 characters or fewer.")
        return value.strip()
    def validate_file(self, uploaded):
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        if uploaded.size <= 0:
            raise serializers.ValidationError("Empty files are not allowed.")
        if uploaded.size > max_bytes:
            raise serializers.ValidationError(f"File exceeds the {settings.MAX_UPLOAD_MB} MB limit.")
        ext = os.path.splitext(uploaded.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("Unsupported file extension.")
        content_type = getattr(uploaded, "content_type", "application/octet-stream")
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError("Unsupported content type.")
        # Extension/content-type checks are basic validation, not malware scanning or proof of file type.
        return uploaded

class PermissionSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    username = serializers.CharField(write_only=True)
    class Meta:
        model = DocumentPermission
        fields = ["id", "user", "username", "level", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
    def validate(self, attrs):
        try:
            target = User.objects.get(username=attrs["username"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "No user with that username exists."})
        if target.id == self.context["request"].user.id:
            raise serializers.ValidationError({"username": "The owner already has access."})
        attrs["target_user"] = target
        return attrs

class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = ["id", "created_at", "actor_label", "action", "document_id",
                  "document_title", "outcome", "ip_address", "details", "previous_hash", "event_hash"]
