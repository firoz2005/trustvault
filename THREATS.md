# TrustVault — Threat Model

## 1. Purpose

TrustVault is a secure document-sharing platform built with Django REST Framework and a frontend application. Its primary security objective is to ensure that only authorized users can access documents and that important actions are recorded in an audit trail.

This document identifies potential attacks, the protections intended to prevent them, and the tests used to verify those protections.

## 2. Assets to Protect

- **Document contents:** Uploaded files must not be accessible to unauthorized users.
- **Document metadata:** Titles, categories, ownership, and other document information.
- **Access permissions:** Permission grants, permission levels, and revocations.
- **User accounts:** Authentication credentials and role assignments.
- **Audit records:** Evidence of document access, downloads, modifications, deletions, and permission changes.
- **Application secrets:** Django secret key, database credentials, and other environment variables.
- **Stored files:** Documents must remain protected even if someone attempts to bypass the frontend.

## 3. Security Roles

- **Administrator:** Can inspect system-wide activity and perform explicitly permitted administrative operations.
- **Document owner:** Can manage their own documents and grant or revoke access to them.
- **Viewer:** Can access only documents for which they have been granted appropriate permission.
- **Editor:** A user granted edit permission can modify permitted document metadata but cannot automatically grant permissions or delete the document.

The backend must enforce authorization independently of frontend visibility or button states.

## 4. Threats and Mitigations

### T1 — Unauthorized document access

**Threat:** A user changes a document ID in an API request to access another user's private document.

**Impact:** Confidential documents may be exposed.

**Mitigation:** Check document permissions on the backend for every read and download request. Return an appropriate denial response when access is not granted.

**Verification:** `test_ungranted_user_cannot_list_read_or_download`

### T2 — Unauthorized document modification or deletion

**Threat:** A viewer or editor sends a direct API request to modify or delete a document outside their permitted capabilities.

**Impact:** Document integrity or availability may be compromised.

**Mitigation:** Enforce edit and delete authorization on the server for every request.

**Verification:** `test_read_user_can_download_but_cannot_edit_or_delete`, `test_editor_can_edit_metadata_but_cannot_share_or_delete`, and `test_admin_cannot_delete_another_users_document`

### T3 — Unauthorized permission changes

**Threat:** A user grants themselves access to another person's document or revokes another user's permissions.

**Impact:** Private documents may be exposed or legitimate access may be disrupted.

**Mitigation:** Only the document owner may manage that document's grants and revocations. Verify ownership on the backend.

**Verification:** `test_ungranted_user_cannot_manage_document_permissions` and `test_editor_can_edit_metadata_but_cannot_share_or_delete`

### T4 — Continued access after revocation

**Threat:** A user continues downloading a document after the owner revokes their permission.

**Impact:** Revoked users may retain access they should no longer have.

**Mitigation:** Recheck current permissions for each protected request rather than relying on stale frontend state.

**Verification:** `test_revocation_blocks_next_download`

### T5 — Unauthorized uploads

**Threat:** A viewer bypasses the frontend and sends a direct upload request.

**Impact:** Unauthorized content may be stored and consume resources.

**Mitigation:** Restrict uploads to permitted roles in the backend and reject invalid upload formats.

**Verification:** `test_viewer_cannot_upload_documents` and `test_upload_rejects_unsupported_extension`

### T6 — Audit information disclosure

**Threat:** A user attempts to inspect system-wide audit activity or view events associated with documents they cannot access.

**Impact:** Sensitive information about users and document activity may be exposed.

**Mitigation:** Restrict administrative activity endpoints to administrators and apply appropriate authorization filters to the regular audit endpoint.

**Verification:** `test_non_admin_cannot_access_admin_endpoints` and `test_ungranted_user_cannot_see_another_users_document_audit`

### T7 — Audit record tampering

**Threat:** An attacker changes stored audit data to hide or falsify activity.

**Impact:** Investigations and accountability may become unreliable.

**Mitigation:** Use chained event hashes and verify the chain to detect changes to recorded audit data.

**Verification:** `test_audit_event_hash_verifies` and `test_audit_verification_detects_tampering`

**Limitation:** Hash-chain verification detects certain forms of tampering; it does not by itself prevent database modification or guarantee protection against an attacker who can rewrite the entire chain.

### T8 — Missing permission-revocation evidence

**Threat:** An owner revokes access, but the audit record does not preserve which user was affected or which permission was removed.

**Impact:** Investigators cannot reliably reconstruct the permission change.

**Mitigation:** Record the affected username and revoked permission level in the audit event.

**Verification:** `test_permission_revocation_is_recorded_in_audit`

### T9 — Malicious or disguised uploaded files

**Threat:** An attacker uploads an executable or a file disguised as an allowed document type.

**Impact:** Malicious content may be stored or delivered to other users.

**Mitigation:** Validate uploads on the server, enforce file size and type restrictions, and serve downloads with appropriate security headers. Do not rely solely on the filename or browser-provided content type.

**Verification status:** Unsupported-extension rejection is tested. Additional content validation and file-size limits must be verified against the actual implementation.

### T10 — Authentication and credential attacks

**Threat:** An attacker attempts to access protected endpoints without authentication or repeatedly guesses credentials.

**Impact:** Accounts or protected resources may be compromised.

**Mitigation:** Require authentication on protected endpoints, use secure password handling, and configure appropriate throttling and deployment protections.

**Verification status:** Authentication failure cases, login throttling, and deployment authentication settings require dedicated verification.

### T11 — Exposure through deployment configuration

**Threat:** Debug mode, weak secrets, insecure transport, or publicly accessible document storage exposes application data.

**Impact:** Application internals, credentials, or private documents may be disclosed.

**Mitigation:** Disable debug mode in production, load secrets from environment variables, use HTTPS, restrict allowed hosts, and ensure uploaded files cannot be retrieved through an unprotected public URL.

**Verification status:** Production configuration and deployed storage access must be checked before release.

## 5. Security Testing Principles

1. Test authorization through direct API requests, not only through the user interface.
2. Use separate test users with different roles and permissions.
3. Verify both the HTTP response and the resulting database state.
4. Confirm that denied operations do not modify documents or permissions.
5. Test revocation by attempting access again after the permission is removed.
6. Verify that audit events are created for security-sensitive operations.
7. Retest security controls after changes to views, permissions, models, or deployment configuration.

## 6. Current Test Evidence

The project currently has 13 automated tests passing in the Django test suite.

These tests cover document access restrictions, role and permission enforcement, upload validation, permission revocation, admin-only endpoints, and audit hash verification.

Passing tests demonstrate the tested scenarios only. They do not establish that every threat listed above has been fully mitigated.

## 7. Remaining Security Review

Before deployment, verify:

- Authentication and role assignment cannot be bypassed.
- All document and permission endpoints enforce server-side authorization.
- Document files cannot be fetched directly through a public storage URL.
- File size and content validation are appropriate.
- Audit events cover all required actions and have suitable access restrictions.
- Production secrets, HTTPS, debug settings, and database access are configured securely.
- Automated tests cover the remaining threats and run successfully in the final version.
