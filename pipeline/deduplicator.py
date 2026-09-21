"""Deduplication and conflict resolution module for health data streams.

Applies sliding time-window heuristics and deterministic source-priority ranking
to eliminate redundant entries and resolve contradictory values across
wearable devices, scale syncs, aggregators, and manual logs.
"""

from datetime import timedelta
from typing import Callable, TypeVar
from pipeline.models import (
    DataSourcePriority,
    GlucoseReading,
    ScaleRecord,
    ActivityRecord,
)

T = TypeVar("T")


def deduplicate_records_by_window(
    records: list[T],
    get_timestamp: Callable[[T], any],
    get_priority: Callable[[T], int],
    window: timedelta = timedelta(minutes=5),
) -> list[T]:
    """Deduplicate records falling within a sliding time window.

    When two or more records fall within `window` of each other:
    1. The record with higher priority wins.
    2. If priorities are equal, the more recently timestamped record is retained.
    """
    if not records:
        return []

    # Sort primarily by timestamp
    sorted_records = sorted(records, key=lambda r: get_timestamp(r))
    deduped: list[T] = []

    for item in sorted_records:
        if not deduped:
            deduped.append(item)
            continue

        prev = deduped[-1]
        time_diff = abs(get_timestamp(item) - get_timestamp(prev))

        if time_diff <= window:
            # Conflict / duplicate within time window!
            prev_prio = get_priority(prev)
            curr_prio = get_priority(item)

            if curr_prio > prev_prio:
                # Replace with higher priority item
                deduped[-1] = item
            elif curr_prio == prev_prio:
                # Keep the later one or previous if identical
                pass
        else:
            deduped.append(item)

    return deduped


def deduplicate_glucose(
    readings: list[GlucoseReading],
    window: timedelta = timedelta(minutes=2),
) -> list[GlucoseReading]:
    """Deduplicate CGM readings within a 2-minute window."""
    return deduplicate_records_by_window(
        records=readings,
        get_timestamp=lambda r: r.timestamp_utc,
        get_priority=lambda r: DataSourcePriority.get_priority(r.source),
        window=window,
    )


def deduplicate_scale(
    records: list[ScaleRecord],
    window: timedelta = timedelta(minutes=15),
) -> list[ScaleRecord]:
    """Deduplicate scale entries (e.g. repeated weigh-ins within 15 minutes)."""
    return deduplicate_records_by_window(
        records=records,
        get_timestamp=lambda r: r.timestamp_utc,
        get_priority=lambda r: DataSourcePriority.get_priority(r.source),
        window=window,
    )


def deduplicate_activity(
    records: list[ActivityRecord],
    window: timedelta = timedelta(minutes=30),
) -> list[ActivityRecord]:
    """Deduplicate overlapping activity or step buckets."""
    return deduplicate_records_by_window(
        records=records,
        get_timestamp=lambda r: r.timestamp_utc,
        get_priority=lambda r: DataSourcePriority.get_priority(r.source),
        window=window,
    )
