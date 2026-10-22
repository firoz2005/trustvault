# TrustVault MVP

Secure document sharing with server-side permissions and an audit trail.

## Stack
- Backend: Python 3.11+, Django, Django REST Framework, SimpleJWT
- Frontend: React + Vite
- Database: SQLite by default for easy local setup; PostgreSQL supported through environment variables
- Files: private `private_uploads/` directory, never served as public static files

## Important security scope
This is a starter MVP, not a production security certification. It enforces permissions on every document API request and rechecks permissions when downloading. Revocation blocks future server access, but cannot erase files someone already downloaded. The audit chain is tamper-evident only while the server secret is protected; for stronger evidence, export signed checkpoints to separately controlled/immutable storage.

## 1. Backend setup (Windows PowerShell)
```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations documents
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Backend runs at `http://127.0.0.1:8000`.

For the default SQLite database, no database server is required. To use PostgreSQL, set `DB_ENGINE=postgres` and fill in the `POSTGRES_*` values in `.env`.

## 2. Frontend setup
Open another terminal:
```powershell
cd frontend
npm install
npm run dev
```
Open the URL printed by Vite (usually `http://localhost:5173`).

## 3. Create users
Register through the UI. New users get the `viewer` role by default. In Django admin (`http://127.0.0.1:8000/admin/`), assign a user's role to `admin` if needed. Document owners are represented by ownership of documents; users can also receive `read` or `edit` grants on individual documents.

## 4. Core API
- `POST /api/auth/register/`
- `POST /api/auth/token/` and `POST /api/auth/token/refresh/`
- `GET /api/documents/` (only documents visible to the current user)
- `POST /api/documents/` (upload; multipart form fields: `title`, `category`, `file`)
- `GET /api/documents/<id>/`
- `PATCH /api/documents/<id>/` (owner or editor)
- `DELETE /api/documents/<id>/` (owner only)
- `GET /api/documents/<id>/download/` (current read permission required)
- `GET /api/documents/<id>/permissions/` (owner only)
- `POST /api/documents/<id>/permissions/` (owner grants access; JSON `{ "username": "...", "level": "read" | "edit" }`)
- `DELETE /api/documents/<id>/permissions/<grant_id>/` (owner revokes access)
- `GET /api/audit/` (admin sees all events; ordinary users see events for documents they can currently access or own)
- `GET /api/admin/activity/` (admin only)

## 5. Run tests
```powershell
cd backend
python manage.py makemigrations documents  # only needed before first migration if migrations are not committed
python manage.py test
```

The tests cover cross-user isolation, download authorization, permission revocation, and denied-access audit events.

## Role policy
- **Admin**: manage users in Django admin and inspect global audit activity. Admin does not automatically gain access to document contents.
- **Owner**: upload, read, edit metadata, delete own documents, grant/revoke named users' read/edit permissions, and see audit events for owned documents.
- **Viewer**: read/download documents only when explicitly granted `read` or `edit`.
- **Editor grant**: can read/download and update document metadata. It cannot delete, share, or revoke access.

## Production hardening checklist
- Use HTTPS and secure cookie/token settings behind a properly configured reverse proxy.
- Put files in private object storage; never make the bucket public.
- Store `SECRET_KEY` in a secret manager and rotate it carefully.
- Send audit checkpoints to separate immutable/WORM storage or an external signing service.
- Add rate limiting, malware scanning, file signature inspection, backups, monitoring, and a formal threat model.
- Decide whether admin access to document content is required; this MVP deliberately uses least privilege.
