from django.urls import path
from .views import (
    DocumentListCreateView, DocumentDetailView, DocumentDownloadView,
    DocumentPermissionsView, PermissionRevokeView, AuditListView,
    AdminActivityView, AuditVerifyView, MeView,
)

urlpatterns = [
    path("me/", MeView.as_view()),
    path("documents/", DocumentListCreateView.as_view()),
    path("documents/<int:pk>/", DocumentDetailView.as_view()),
    path("documents/<int:pk>/download/", DocumentDownloadView.as_view()),
    path("documents/<int:pk>/permissions/", DocumentPermissionsView.as_view()),
    path("documents/<int:pk>/permissions/<int:grant_id>/", PermissionRevokeView.as_view()),
    path("audit/", AuditListView.as_view()),
    path("admin/activity/", AdminActivityView.as_view()),
    path("admin/audit/verify/", AuditVerifyView.as_view()),
]
