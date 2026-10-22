import hashlib
import hmac
import json
import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = [
    ("admin", "Administrator"),
    ("owner", "Document Owner"),
    ("viewer", "Viewer"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="viewer")

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Document(models.Model):
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="owned_documents")
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=80, blank=True)
    original_filename = models.CharField(max_length=255)
    stored_file = models.FileField(upload_to="documents/")
    size_bytes = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

class DocumentPermission(models.Model):
    LEVEL_CHOICES = [("read", "Read"), ("edit", "Edit")]
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="grants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="document_grants")
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    granted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="grants_created")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "user"], name="unique_document_user_grant")
        ]

class AuditEvent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    actor_label = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=40, db_index=True)
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    # Immutable snapshot ID survives document deletion and remains part of the signed payload.
    document_ref_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    document_title = models.CharField(max_length=200, blank=True)
    outcome = models.CharField(max_length=12, choices=[("success", "Success"), ("denied", "Denied"), ("failure", "Failure")])
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.JSONField(default=dict)
    previous_hash = models.CharField(max_length=64, blank=True)
    event_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["id"]

    def payload(self):
        return {
            "id": self.pk,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "actor_id": self.actor_id,
            "actor_label": self.actor_label,
            "action": self.action,
            "document_id": self.document_ref_id,
            "document_title": self.document_title,
            "outcome": self.outcome,
            "ip_address": self.ip_address,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }

    def seal(self):
        previous = AuditEvent.objects.exclude(pk=self.pk).order_by("-pk").values_list("event_hash", flat=True).first() or "GENESIS"
        self.previous_hash = previous
        body = json.dumps(self.payload(), sort_keys=True, separators=(",", ":"), default=str).encode()
        key = settings.SECRET_KEY.encode()
        self.event_hash = hmac.new(key, body, hashlib.sha256).hexdigest()
        self.save(update_fields=["previous_hash", "event_hash"])

    def verify_hash(self):
        body = json.dumps(self.payload(), sort_keys=True, separators=(",", ":"), default=str).encode()
        expected = hmac.new(settings.SECRET_KEY.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, self.event_hash)
