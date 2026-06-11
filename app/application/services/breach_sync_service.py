import logging
import time

from app.application.exceptions import ExternalServiceError, ValidationError
from app.infrastructure.hibp.client import HIBPClient
from app.infrastructure.hibp.mapper import HIBPMappingError, map_hibp_breach
from app.infrastructure.persistence.repositories import BreachRepository

logger = logging.getLogger(__name__)


class BreachSyncService:
    def __init__(self, *, client: HIBPClient, repository: BreachRepository) -> None:
        self.client = client
        self.repository = repository

    def sync(self) -> dict:
        started = time.perf_counter()
        try:
            payload = self.client.fetch_breaches()
        except ExternalServiceError as exc:
            local_total = self.repository.count()
            logger.warning(
                "sync failed; local cache preserved",
                extra={"event_source": "cache_fallback", "event_local_total": local_total},
            )
            return {
                "source": "cache_fallback",
                "total_received": 0,
                "inserted": 0,
                "updated": 0,
                "ignored": 0,
                "local_total": local_total,
                "errors": [exc.message],
            }

        rows_by_name = {}
        errors = []
        ignored = 0
        for index, item in enumerate(payload):
            try:
                row = map_hibp_breach(item)
            except (HIBPMappingError, ValidationError, ValueError) as exc:
                ignored += 1
                errors.append(f"record[{index}] ignored: {exc}")
                continue

            name = row["name"]
            if name in rows_by_name:
                ignored += 1
                errors.append(f"record[{index}] ignored: duplicate Name '{name}'")
                continue
            # Keep first record when the same payload repeats a Name; later dupes are skiped.
            rows_by_name[name] = row

        rows = list(rows_by_name.values())
        names = [row["name"] for row in rows]
        existing_names = self.repository.existing_names(names)
        inserted = sum(1 for name in names if name not in existing_names)
        updated = sum(1 for name in names if name in existing_names)

        with self.repository.session.begin_nested():
            self.repository.upsert_many(rows)

        self.repository.session.commit()
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "sync completed",
            extra={
                "event_total_received": len(payload),
                "event_inserted": inserted,
                "event_updated": updated,
                "event_ignored": ignored,
                "event_duration_ms": duration_ms,
            },
        )
        return {
            "source": "remote",
            "total_received": len(payload),
            "inserted": inserted,
            "updated": updated,
            "ignored": ignored,
            "local_total": self.repository.count(),
            "errors": errors,
        }
