"""
Temporal conflict detection and minimum rest interval verification for workforce scheduling.

Provides rigorous pairwise conflict detection for:
1. Overlapping shifts (simultaneous or partially concurrent work intervals)
2. Minimum rest duration violations between consecutive shifts

Supports:
- Exact ISO datetime timestamps (e.g., '2026-10-24T08:00:00')
- Time-of-day clock strings (e.g., '08:00', '16:00') including cross-midnight overnight shifts
"""
from datetime import datetime
from app.domain.models import Shift


def _parse_time_str(time_str: str) -> tuple[datetime | None, int | None]:
    """
    Parse a shift timestamp string.
    Returns:
    - (datetime, None) if ISO datetime string
    - (None, total_minutes_from_midnight) if 'HH:MM' time string
    """
    cleaned = time_str.strip()
    # Try ISO datetime
    if "T" in cleaned or " " in cleaned or "-" in cleaned:
        try:
            dt = datetime.fromisoformat(cleaned)
            return dt, None
        except Exception:
            pass

    # Try 'HH:MM' or 'HH:MM:SS'
    parts = cleaned.split(":")
    if len(parts) >= 2:
        try:
            h = int(parts[0])
            m = int(parts[1])
            return None, h * 60 + m
        except Exception:
            pass

    return None, None


def shifts_conflict(
    s1: Shift, s2: Shift, min_rest_hours: float = 0.0
) -> tuple[bool, str | None]:
    """
    Determine whether two shifts conflict for the same employee.
    
    Conflict occurs if:
    1. The shifts overlap in time (overlap duration > 0)
    2. The rest interval between them is strictly less than min_rest_hours

    Returns:
    (is_conflict, conflict_type) where conflict_type in ('OVERLAPPING_SHIFTS', 'MIN_REST_VIOLATION', None)
    """
    if s1.id == s2.id:
        return False, None

    dt_start1, min_start1 = _parse_time_str(s1.start_time)
    dt_end1, min_end1 = _parse_time_str(s1.end_time)
    dt_start2, min_start2 = _parse_time_str(s2.start_time)
    dt_end2, min_end2 = _parse_time_str(s2.end_time)

    # Case 1: Exact ISO datetimes available for all endpoints
    if (
        dt_start1 is not None
        and dt_end1 is not None
        and dt_start2 is not None
        and dt_end2 is not None
    ):
        # Check overlap
        latest_start = max(dt_start1, dt_start2)
        earliest_end = min(dt_end1, dt_end2)
        if latest_start < earliest_end:
            return True, "OVERLAPPING_SHIFTS"

        # Check rest interval if min_rest_hours > 0
        if min_rest_hours > 0.0:
            if dt_end1 <= dt_start2:
                gap_hours = (dt_start2 - dt_end1).total_seconds() / 3600.0
                if gap_hours < min_rest_hours:
                    return True, "MIN_REST_VIOLATION"
            elif dt_end2 <= dt_start1:
                gap_hours = (dt_start1 - dt_end2).total_seconds() / 3600.0
                if gap_hours < min_rest_hours:
                    return True, "MIN_REST_VIOLATION"

        return False, None

    # Case 2: Time-of-day clock strings (HH:MM)
    if (
        min_start1 is not None
        and min_end1 is not None
        and min_start2 is not None
        and min_end2 is not None
    ):
        # Normalize overnight shifts crossing midnight
        if min_end1 <= min_start1:
            dur1 = int(round(s1.duration_hours * 60)) if s1.duration_hours > 0 else (min_end1 + 1440 - min_start1)
            end1 = min_start1 + dur1
        else:
            end1 = min_end1

        if min_end2 <= min_start2:
            dur2 = int(round(s2.duration_hours * 60)) if s2.duration_hours > 0 else (min_end2 + 1440 - min_start2)
            end2 = min_start2 + dur2
        else:
            end2 = min_end2

        start1 = min_start1
        start2 = min_start2

        # In the absence of date metadata, two distinct shifts with identical clock start and end times
        # (e.g., both '08:00' to '16:00') represent distinct operational days/periods rather than concurrent shifts.
        if start1 == start2 and end1 == end2:
            return False, None

        # Check linear overlap within reference horizon
        latest_start = max(start1, start2)
        earliest_end = min(end1, end2)
        if latest_start < earliest_end:
            return True, "OVERLAPPING_SHIFTS"

        # Check wrapped overlap for overnight shift crossing past midnight into next morning
        if end1 > 1440:
            wrapped_start1 = 0
            wrapped_end1 = end1 - 1440
            if max(wrapped_start1, start2) < min(wrapped_end1, end2):
                return True, "OVERLAPPING_SHIFTS"

        if end2 > 1440:
            wrapped_start2 = 0
            wrapped_end2 = end2 - 1440
            if max(wrapped_start2, start1) < min(wrapped_end2, end1):
                return True, "OVERLAPPING_SHIFTS"

        # Check minimum rest if enabled
        if min_rest_hours > 0.0:
            min_rest_minutes = min_rest_hours * 60.0
            # Order A: s1 precedes s2
            if end1 <= start2:
                gap = start2 - end1
                if gap < min_rest_minutes:
                    return True, "MIN_REST_VIOLATION"
            # Order B: s2 precedes s1
            elif end2 <= start1:
                gap = start1 - end2
                if gap < min_rest_minutes:
                    return True, "MIN_REST_VIOLATION"
            # Wrapped overnight gap (s1 overnight ending in morning, s2 later that day)
            if end1 > 1440:
                wrapped_end = end1 - 1440
                if wrapped_end <= start2:
                    gap = start2 - wrapped_end
                    if gap < min_rest_minutes:
                        return True, "MIN_REST_VIOLATION"
            if end2 > 1440:
                wrapped_end = end2 - 1440
                if wrapped_end <= start1:
                    gap = start1 - wrapped_end
                    if gap < min_rest_minutes:
                        return True, "MIN_REST_VIOLATION"

        return False, None

    # Fallback: Timestamps unparseable; cannot prove conflict
    return False, None


def build_shift_conflict_pairs(
    shifts: list[Shift], min_rest_hours: float = 0.0
) -> set[tuple[str, str]]:
    """
    Build set of canonical shift ID pairs (s1_id, s2_id) with s1_id < s2_id that conflict.
    """
    conflicts: set[tuple[str, str]] = set()
    n = len(shifts)
    for i in range(n):
        for k in range(i + 1, n):
            s1 = shifts[i]
            s2 = shifts[k]
            is_conf, _ = shifts_conflict(s1, s2, min_rest_hours=min_rest_hours)
            if is_conf:
                pair = (min(s1.id, s2.id), max(s1.id, s2.id))
                conflicts.add(pair)
    return conflicts


def build_shift_conflict_map(
    shifts: list[Shift], min_rest_hours: float = 0.0
) -> dict[str, set[str]]:
    """
    Build adjacency map of shift_id -> set of conflicting shift_ids.
    """
    conflict_map: dict[str, set[str]] = {s.id: set() for s in shifts}
    pairs = build_shift_conflict_pairs(shifts, min_rest_hours=min_rest_hours)
    for s1, s2 in pairs:
        conflict_map[s1].add(s2)
        conflict_map[s2].add(s1)
    return conflict_map
