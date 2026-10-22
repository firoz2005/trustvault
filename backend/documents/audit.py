from .models import AuditEvent

def client_ip(request):
    # Do not trust arbitrary X-Forwarded-For headers unless your reverse proxy is configured to overwrite them.
    return request.META.get("REMOTE_ADDR")

def record_event(request, action, outcome, document=None, details=None, actor=None):
    user = actor if actor is not None else getattr(request, "user", None)
    is_authenticated = bool(user and getattr(user, "is_authenticated", False))
    event = AuditEvent.objects.create(
        actor=user if is_authenticated else None,
        actor_label=user.get_username() if is_authenticated else "anonymous",
        action=action,
        document=document,
        document_ref_id=(document.pk if document else None),
        document_title=(document.title if document else ""),
        outcome=outcome,
        ip_address=client_ip(request),
        details=details or {},
    )
    event.seal()
    return event
