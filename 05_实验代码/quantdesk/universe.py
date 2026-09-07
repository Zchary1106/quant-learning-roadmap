"""Point-in-time-aware universe construction from historical membership intervals."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime

from .contracts import (
    IndexMembership,
    PointInTimeConfidence,
    UniverseSnapshot,
)


def _least_confident(
    values: Iterable[PointInTimeConfidence],
) -> PointInTimeConfidence:
    ranking = {
        PointInTimeConfidence.VERIFIED: 2,
        PointInTimeConfidence.EFFECTIVE_INTERVAL_ONLY: 1,
        PointInTimeConfidence.UNKNOWN: 0,
    }
    return min(values, key=lambda value: ranking[value], default=PointInTimeConfidence.UNKNOWN)


def build_index_universe(
    memberships: Iterable[IndexMembership],
    *,
    index_code: str,
    as_of_date: date,
    decision_time: datetime,
) -> UniverseSnapshot:
    """Build an index universe without treating effective dates as PIT proof.

    Memberships that are active but not yet available at ``decision_time`` are
    surfaced in ``unresolved_codes`` rather than silently added to the universe.
    """
    active = [
        membership
        for membership in memberships
        if membership.index_code == index_code and membership.is_active_on(as_of_date)
    ]
    eligible = [
        membership
        for membership in active
        if membership.availability.is_available_by(decision_time)
    ]
    unresolved = [
        membership
        for membership in active
        if not membership.availability.is_available_by(decision_time)
    ]
    confidence = _least_confident(
        membership.point_in_time_confidence for membership in active
    )
    return UniverseSnapshot(
        index_code=index_code,
        as_of_date=as_of_date,
        eligible_codes=tuple(sorted({membership.ts_code for membership in eligible})),
        unresolved_codes=tuple(sorted({membership.ts_code for membership in unresolved})),
        point_in_time_confidence=confidence,
    )


def require_verified_point_in_time(universe: UniverseSnapshot) -> UniverseSnapshot:
    """Reject a universe whose historical membership evidence is not PIT-verified."""
    if universe.unresolved_codes:
        raise ValueError(
            "universe has memberships unavailable at the requested decision_time: "
            + ", ".join(universe.unresolved_codes)
        )
    if universe.point_in_time_confidence is not PointInTimeConfidence.VERIFIED:
        raise ValueError(
            "universe is not point-in-time verified: "
            + universe.point_in_time_confidence.value
        )
    return universe
