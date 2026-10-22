
import hashlib
import hmac
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from documents.models import AuditEvent


class Command(BaseCommand):
    help = "Create a signed checkpoint of the current audit-chain head."

    def handle(self, *args, **options):
        key = os.environ.get("AUDIT_CHECKPOINT_KEY")
        checkpoint_path = os.environ.get("AUDIT_CHECKPOINT_PATH")

        if not key or len(key) < 32:
            raise CommandError(
                "Set AUDIT_CHECKPOINT_KEY to a separate random secret "
                "of at least 32 characters."
            )

        if not checkpoint_path:
            raise CommandError(
                "Set AUDIT_CHECKPOINT_PATH to the checkpoint file path."
            )

        latest = AuditEvent.objects.order_by("-id").first()

        checkpoint = {
            "last_event_id": latest.id if latest else 0,
            "last_event_hash": latest.event_hash if latest else "GENESIS",
        }

        payload = json.dumps(
            checkpoint, sort_keys=True, separators=(",", ":")
        )

        checkpoint["signature"] = hmac.new(
            key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

        path = Path(checkpoint_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")

        self.stdout.write(
            self.style.SUCCESS(
                f"Checkpoint created at event {checkpoint['last_event_id']}."
            )
        )
