
import hashlib
import hmac
import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from documents.models import AuditEvent


class Command(BaseCommand):
    help = "Verify the saved audit checkpoint against the database."

    def handle(self, *args, **options):
        key = os.environ.get("AUDIT_CHECKPOINT_KEY")
        checkpoint_path = os.environ.get("AUDIT_CHECKPOINT_PATH")

        if not key or len(key) < 32:
            raise CommandError(
                "AUDIT_CHECKPOINT_KEY must contain at least 32 characters."
            )

        if not checkpoint_path:
            raise CommandError("AUDIT_CHECKPOINT_PATH is not configured.")

        path = Path(checkpoint_path)

        if not path.is_file():
            raise CommandError(f"Checkpoint file not found: {path}")

        try:
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            signature = checkpoint.pop("signature")

            payload = json.dumps(
                checkpoint, sort_keys=True, separators=(",", ":")
            )

            expected_signature = hmac.new(
                key.encode(),
                payload.encode(),
                hashlib.sha256,
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                raise CommandError("INVALID: checkpoint signature mismatch.")

            event_id = checkpoint["last_event_id"]
            event_hash = checkpoint["last_event_hash"]

            if not isinstance(event_id, int) or event_id < 0:
                raise ValueError("Invalid last_event_id.")

            if not isinstance(event_hash, str):
                raise ValueError("Invalid last_event_hash.")

        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise CommandError(f"Invalid checkpoint: {exc}") from exc

        
        events = list(AuditEvent.objects.all().order_by("id"))

        if event_id == 0:
            if events:
                raise CommandError(
                    "MISMATCH: checkpoint is empty but audit events exist."
                )

            self.stdout.write(self.style.SUCCESS(
                "VALID: signed empty-chain checkpoint matches the database."
            ))
            return

        checkpoint_event = next(
            (event for event in events if event.id == event_id),
            None,
        )

        if checkpoint_event is None:
            raise CommandError(
                f"MISMATCH: checkpoint event {event_id} is missing."
            )

        if not hmac.compare_digest(
            checkpoint_event.event_hash, event_hash
        ):
            raise CommandError(
                "MISMATCH: checkpoint event hash does not match."
            )

        expected_previous = "GENESIS"
        invalid_ids = []

        for event in events:
            if (
                event.previous_hash != expected_previous
                or not event.verify_hash()
            ):
                invalid_ids.append(event.id)

            expected_previous = event.event_hash

        if invalid_ids:
            raise CommandError(
                "INVALID: audit-chain verification failed for event IDs: "
                + ", ".join(map(str, invalid_ids))
            )

        self.stdout.write(self.style.SUCCESS(
            f"VALID: checkpoint matches event {event_id}; "
            f"all {len(events)} audit events passed chain verification."
        ))
