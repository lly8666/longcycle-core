from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from longcycle.domain.enums import Cadence, JobStage
from longcycle.domain.models import CollectionJob, CollectionPolicy, stable_uuid


class SchedulePolicy:
    def cadence_for(self, policy: CollectionPolicy, now: datetime | None = None) -> Cadence:
        now = now or datetime.now(UTC)
        if policy.event_override_until and policy.event_override_until > now:
            return Cadence.DAILY
        if policy.priority >= 70:
            return Cadence.DAILY
        if policy.priority >= 45:
            return Cadence.EVERY_THREE_DAYS
        if policy.consecutive_low_days < 7 and policy.cadence != Cadence.WEEKLY:
            return policy.cadence
        return Cadence.WEEKLY

    def next_run(self, policy: CollectionPolicy, after: datetime | None = None) -> datetime:
        after = after or datetime.now(UTC)
        local_zone = ZoneInfo(policy.timezone)
        local_after = after.astimezone(local_zone)
        cadence = self.cadence_for(policy, after)
        morning_slot = local_after.replace(hour=6, minute=0, second=0, microsecond=0)
        if cadence == Cadence.DAILY:
            due = morning_slot if local_after < morning_slot else morning_slot + timedelta(days=1)
        elif cadence == Cadence.EVERY_THREE_DAYS:
            due = morning_slot if local_after < morning_slot else morning_slot + timedelta(days=3)
        elif cadence == Cadence.WEEKLY:
            target_weekday = policy.industry_id.int % 7
            delta = (target_weekday - local_after.weekday()) % 7
            due = morning_slot + timedelta(days=delta)
            if due <= local_after:
                due += timedelta(days=7)
        else:
            due = local_after + timedelta(days=1)
        return due.astimezone(UTC)

    def discovery_job(
        self,
        *,
        policy: CollectionPolicy,
        source_id: UUID,
        scheduled_for: datetime,
        policy_version: str,
        target_code: str = "default",
    ) -> CollectionJob:
        cadence = self.cadence_for(policy, scheduled_for)
        window = scheduled_for.strftime("%Y-%m-%d")
        key_payload = f"discover|{policy.industry_id}|{source_id}|{target_code}|{window}|{policy_version}"
        key = hashlib.sha256(key_payload.encode()).hexdigest()
        return CollectionJob(
            id=stable_uuid("job", key),
            stage=JobStage.DISCOVER,
            source_id=source_id,
            industry_id=policy.industry_id,
            priority=policy.priority,
            available_at=scheduled_for,
            idempotency_key=key,
            payload={
                "cadence": cadence.value,
                "policy_version": policy_version,
                "target_code": target_code,
                "scheduled_window": window,
            },
        )
