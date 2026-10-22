
import hashlib

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Profile, Document, DocumentPermission, AuditEvent
from .audit import record_event


@override_settings(MEDIA_ROOT="/tmp/trustvault-test-uploads")
class TrustVaultSecurityTests(APITestCase):

    
    def test_unauthenticated_user_cannot_access_protected_endpoints(self):
        endpoints = [
        "/api/me/",
        "/api/documents/",
        "/api/audit/",
        "/api/admin/activity/",
        "/api/admin/audit/verify/",
    ]

        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 401, endpoint)


    
    def test_viewer_cannot_upload_documents(self):
        self.client.force_authenticate(self.bob)

        upload = SimpleUploadedFile(
            "notes.txt",
            b"private notes",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/documents/",
            {
                "title": "Viewer upload attempt",
                "category": "test",
                "file": upload,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Document.objects.filter(
                title="Viewer upload attempt"
            ).exists()
        )

    
    def test_permission_revocation_is_recorded_in_audit(self):
        grant = DocumentPermission.objects.create(
            document=self.doc,
            user=self.alice,
            level="read",
            granted_by=self.owner,
        )

        self.client.force_authenticate(self.owner)

        response = self.client.delete(
            f"/api/documents/{self.doc.id}/permissions/{grant.id}/"
        )
        self.assertEqual(response.status_code, 204)

        event = AuditEvent.objects.filter(
            action="permission_revoke",
            outcome="success",
            document_ref_id=self.doc.id,
        ).latest("id")

        self.assertEqual(
            event.details["target_user"], "alice"
        )
        self.assertEqual(
            event.details["revoked_level"], "read"
        )

    
    def test_ungranted_user_cannot_see_another_users_document_audit(self):
        record_event(
            self.make_request(),
            "test_private_event",
            "success",
            self.doc,
            {"marker": "owner-private-event"},
        )

        self.client.force_authenticate(self.bob)

        response = self.client.get("/api/audit/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            any(
                event.get("details", {}).get("marker")
                == "owner-private-event"
                for event in response.data
            )
        )

        
    def test_admin_cannot_delete_another_users_document(self):
        admin = User.objects.create_user(
            username="admin",
            password="a-strong-test-password",
            is_staff=True,
        )
        Profile.objects.get_or_create(
            user=admin,
            defaults={"role": "admin"},
        )
        Profile.objects.filter(user=admin).update(role="admin")

        self.client.force_authenticate(admin)

        response = self.client.delete(
            f"/api/documents/{self.doc.id}/"
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Document.objects.filter(id=self.doc.id).exists()
        )

    
    def test_non_admin_cannot_access_admin_endpoints(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get("/api/admin/activity/")
        self.assertEqual(response.status_code, 404)

        response = self.client.get("/api/admin/audit/verify/")
        self.assertEqual(response.status_code, 404)

    
    def test_ungranted_user_cannot_manage_document_permissions(self):
        self.client.force_authenticate(self.bob)

        response = self.client.get(
            f"/api/documents/{self.doc.id}/permissions/"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            f"/api/documents/{self.doc.id}/permissions/",
            {"username": "bob", "level": "read"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="a-strong-test-password",
        )
        self.alice = User.objects.create_user(
            username="alice",
            password="a-strong-test-password",
        )
        self.bob = User.objects.create_user(
            username="bob",
            password="a-strong-test-password",
        )

        for user in (self.owner, self.alice, self.bob):
            Profile.objects.get_or_create(
                user=user,
                defaults={"role": "viewer"},
            )
        Profile.objects.filter(user=self.owner).update(role="owner")
        self.owner.profile.refresh_from_db()

        file_content = b"private report"
        upload = SimpleUploadedFile(
            "report.txt",
            file_content,
            content_type="text/plain",
        )

        self.doc = Document.objects.create(
            owner=self.owner,
            title="Private report",
            category="finance",
            original_filename="report.txt",
            stored_file=upload,
            size_bytes=len(file_content),
            sha256=hashlib.sha256(file_content).hexdigest(),
        )

    def make_request(self):
        return type(
            "Request",
            (),
            {
                "user": self.owner,
                "META": {"REMOTE_ADDR": "127.0.0.1"},
            },
        )()

    def test_ungranted_user_cannot_list_read_or_download(self):
        self.client.force_authenticate(self.bob)

        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        response = self.client.get(
            f"/api/documents/{self.doc.id}/"
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            f"/api/documents/{self.doc.id}/download/"
        )
        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            AuditEvent.objects.filter(
                action="read", outcome="denied"
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                action="download", outcome="denied"
            ).exists()
        )

    def test_read_user_can_download_but_cannot_edit_or_delete(self):
        DocumentPermission.objects.create(
            document=self.doc,
            user=self.alice,
            level="read",
            granted_by=self.owner,
        )

        self.client.force_authenticate(self.alice)

        response = self.client.get(
            f"/api/documents/{self.doc.id}/"
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            f"/api/documents/{self.doc.id}/download/"
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(
            f"/api/documents/{self.doc.id}/",
            {"title": "Changed"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(
            f"/api/documents/{self.doc.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_revocation_blocks_next_download(self):
        grant = DocumentPermission.objects.create(
            document=self.doc,
            user=self.alice,
            level="read",
            granted_by=self.owner,
        )

        self.client.force_authenticate(self.alice)
        response = self.client.get(
            f"/api/documents/{self.doc.id}/download/"
        )
        self.assertEqual(response.status_code, 200)

        self.client.force_authenticate(self.owner)
        response = self.client.delete(
            f"/api/documents/{self.doc.id}/permissions/{grant.id}/"
        )
        self.assertEqual(response.status_code, 204)

        self.client.force_authenticate(self.alice)
        response = self.client.get(
            f"/api/documents/{self.doc.id}/download/"
        )
        self.assertEqual(response.status_code, 404)

    def test_editor_can_edit_metadata_but_cannot_share_or_delete(self):
        DocumentPermission.objects.create(
            document=self.doc,
            user=self.alice,
            level="edit",
            granted_by=self.owner,
        )

        self.client.force_authenticate(self.alice)

        response = self.client.patch(
            f"/api/documents/{self.doc.id}/",
            {"title": "New title"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            f"/api/documents/{self.doc.id}/permissions/",
            {"username": "bob", "level": "read"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.delete(
            f"/api/documents/{self.doc.id}/"
        )
        self.assertEqual(response.status_code, 404)

    def test_upload_rejects_unsupported_extension(self):
        self.client.force_authenticate(self.owner)

        upload = SimpleUploadedFile(
            "payload.exe",
            b"not an allowed file",
            content_type="application/octet-stream",
        )

        response = self.client.post(
            "/api/documents/",
            {
                "title": "Invalid file",
                "category": "test",
                "file": upload,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

    def test_audit_event_hash_verifies(self):
        event = record_event(
            self.make_request(),
            "test",
            "success",
            self.doc,
            {"hello": "world"},
        )

        event.refresh_from_db()
        self.assertTrue(event.verify_hash())

    def test_audit_verification_detects_tampering(self):
        first = record_event(
            self.make_request(),
            "test_first",
            "success",
            self.doc,
            {"step": 1},
        )

        second = record_event(
            self.make_request(),
            "test_second",
            "success",
            self.doc,
            {"step": 2},
        )

        # Simulate someone changing signed audit data directly.
        second.details = {"step": "tampered"}
        second.save(update_fields=["details"])

        self.owner.is_staff = True
        self.owner.save(update_fields=["is_staff"])
        self.client.force_authenticate(self.owner)

        response = self.client.get("/api/admin/audit/verify/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["valid"])
        self.assertIn(
            second.id,
            response.data["invalid_event_ids"],
        )

    

