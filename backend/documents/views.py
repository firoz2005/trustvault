import hashlib
import os
import profile
from pydoc import doc
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.migrations import serializer
from django.http import FileResponse, request
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit import record_event
from .models import Document, DocumentPermission, AuditEvent, Profile
from .permissions import access_level, can_read, can_edit, is_admin
from .serializers import RegisterSerializer, DocumentSerializer, DocumentUploadSerializer, PermissionSerializer, AuditEventSerializer

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "anon"

class DocumentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        qs = Document.objects.filter(owner=request.user) | Document.objects.filter(grants__user=request.user)
        qs = qs.distinct().select_related("owner")
        query = request.query_params
        name = query.get("name")
        owner = query.get("owner")
        category = query.get("category")
        date_from = query.get("date_from")
        date_to = query.get("date_to")
        if name:
            qs = qs.filter(title__icontains=name)
        if owner:
            qs = qs.filter(owner__username__icontains=owner)
        if category:
            qs = qs.filter(category__icontains=category)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return Response(DocumentSerializer(qs, many=True, context={"request": request}).data)

    
    def post(self, request):
        profile = getattr(request.user, "profile", None)

        if not is_admin(request.user) and (
            not profile or profile.role != "owner"
        ):
            record_event(
                request,
                "upload",
                "denied",
                details={"reason": "role_not_allowed"},
            )
            return Response(
                {"detail": "Only document owners and administrators can upload files."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded = serializer.validated_data.pop("file")

        digest = hashlib.sha256()
        for chunk in uploaded.chunks():
            digest.update(chunk)
        uploaded.seek(0)

        with transaction.atomic():
            doc = Document.objects.create(
                owner=request.user,
                title=serializer.validated_data["title"],
                category=serializer.validated_data.get("category", ""),
                original_filename=os.path.basename(uploaded.name).replace("\\", "_"),
                stored_file=uploaded,
                size_bytes=uploaded.size,
                sha256=digest.hexdigest(),
            )
            record_event(
                request,
                "upload",
                "success",
                doc,
                {
                    "filename": doc.original_filename,
                    "size_bytes": doc.size_bytes,
                },
            )

        return Response(
            DocumentSerializer(doc, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not can_read(request.user, doc):
            record_event(request, "read", "denied", doc, {"reason": "no_document_permission"})
            return Response({"detail": "Document not found."}, status=404)
        record_event(request, "read", "success", doc)
        return Response(DocumentSerializer(doc, context={"request": request}).data)

    def patch(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not can_edit(request.user, doc):
            record_event(request, "edit", "denied", doc, {"reason": "no_edit_permission"})
            return Response({"detail": "Document not found."}, status=404)
        allowed = {"title", "category"}
        if set(request.data.keys()) - allowed:
            record_event(request, "edit", "denied", doc, {"reason": "forbidden_fields"})
            return Response({"detail": "Only title and category may be changed."}, status=400)
        old = {"title": doc.title, "category": doc.category}
        title = request.data.get("title", doc.title)
        category = request.data.get("category", doc.category)
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
            return Response({"title": "Must contain 1–200 characters."}, status=400)
        if not isinstance(category, str) or len(category) > 80:
            return Response({"category": "Must be 80 characters or fewer."}, status=400)
        doc.title, doc.category = title.strip(), category.strip()
        doc.save(update_fields=["title", "category", "updated_at"])
        record_event(request, "edit", "success", doc, {"before": old, "after": {"title": doc.title, "category": doc.category}})
        return Response(DocumentSerializer(doc, context={"request": request}).data)

    def delete(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if doc.owner_id != request.user.id:
            record_event(request, "delete", "denied", doc, {"reason": "owner_only"})
            return Response({"detail": "Document not found."}, status=404)
        title = doc.title
        file_name = doc.stored_file.name
        record_event(request, "delete", "success", doc, {"filename": doc.original_filename})
        # Delete the database row and stored file only after recording the event.
        storage = doc.stored_file.storage
        doc.delete()
        if file_name and storage.exists(file_name):
            storage.delete(file_name)
        return Response(status=status.HTTP_204_NO_CONTENT)

class DocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if not can_read(request.user, doc):
            record_event(request, "download", "denied", doc, {"reason": "no_document_permission"})
            return Response({"detail": "Document not found."}, status=404)
        try:
            file_handle = doc.stored_file.open("rb")
        except (OSError, ValueError):
            record_event(request, "download", "failure", doc, {"reason": "file_unavailable"})
            return Response({"detail": "File unavailable."}, status=500)
        record_event(request, "download", "success", doc, {"sha256": doc.sha256})
        response = FileResponse(file_handle, as_attachment=True, filename=doc.original_filename)
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response

class DocumentPermissionsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if doc.owner_id != request.user.id:
            record_event(request, "permission_list", "denied", doc, {"reason": "owner_only"})
            return Response({"detail": "Document not found."}, status=404)
        return Response(PermissionSerializer(doc.grants.select_related("user"), many=True).data)

    def post(self, request, pk):
        doc = get_object_or_404(Document, pk=pk)
        if doc.owner_id != request.user.id:
            record_event(request, "permission_grant", "denied", doc, {"reason": "owner_only"})
            return Response({"detail": "Document not found."}, status=404)
        serializer = PermissionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        target = serializer.validated_data["target_user"]
        level = serializer.validated_data["level"]
        with transaction.atomic():
            grant, created = DocumentPermission.objects.update_or_create(
                document=doc, user=target,
                defaults={"level": level, "granted_by": request.user},
            )
            record_event(request, "permission_grant" if created else "permission_update", "success", doc,
                         {"target_user": target.username, "level": level})
        return Response(PermissionSerializer(grant).data, status=201 if created else 200)

class PermissionRevokeView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, pk, grant_id):
        doc = get_object_or_404(Document, pk=pk)
        if doc.owner_id != request.user.id:
            record_event(request, "permission_revoke", "denied", doc, {"reason": "owner_only"})
            return Response({"detail": "Document not found."}, status=404)
        grant = get_object_or_404(DocumentPermission, pk=grant_id, document=doc)
        target = grant.user.username
        revoked_level = grant.level
        grant.delete()
        record_event(request,"permission_revoke","success",doc,{"target_user": target,"revoked_level": revoked_level,},)
        return Response(status=204)

class AuditListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        owned_ids = Document.objects.filter(
            owner=request.user
        ).values_list("id", flat=True)

        granted_ids = DocumentPermission.objects.filter(
            user=request.user
        ).values_list("document_id", flat=True)

        qs = AuditEvent.objects.filter(
            document_ref_id__in=list(owned_ids) + list(granted_ids)
        ).select_related("document")

        return Response(AuditEventSerializer(qs[:500], many=True).data)


class AdminActivityView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not is_admin(request.user):
            record_event(request, "admin_activity_view", "denied", details={"reason": "admin_only"})
            return Response({"detail": "Not found."}, status=404)
        qs = AuditEvent.objects.all().select_related("document")[:1000]
        return Response(AuditEventSerializer(qs, many=True).data)

class AuditVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not is_admin(request.user):
            return Response({"detail": "Not found."}, status=404)
        events = list(AuditEvent.objects.all().order_by("id"))
        expected_prev = "GENESIS"
        issues = []
        for event in events:
            if event.previous_hash != expected_prev or not event.verify_hash():
                issues.append(event.id)
            expected_prev = event.event_hash
        return Response({"valid": not issues, "checked": len(events), "invalid_event_ids": issues})

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user, defaults={"role": "viewer"})
        return Response({"id": request.user.id, "username": request.user.username,
                         "is_staff": request.user.is_staff, "role": "admin" if is_admin(request.user) else profile.role})
