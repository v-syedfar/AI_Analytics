from typing import Any, Optional, List, Dict
from models import PlanningRecord, SnapshotPoint, TrendRecord
from normalizer import normalize_rows
from filters import filter_records

# How many snapshots with changes qualifies as "recurring"
RECURRING_THRESHOLD = 3


def build_snapshot_point(rec: PlanningRecord, snapshot_date: str) -> SnapshotPoint:
    return SnapshotPoint(
        snapshot_date=snapshot_date,
        forecast_qty=rec.forecast_qty,
        roj=rec.roj,
        supplier=rec.supplier,
        bod=rec.bod,
        ff=rec.ff,
        last_modified_by=rec.last_modified_by,
        last_modified_date=rec.last_modified_date,
    )


def _values_differ(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    return str(a).strip().lower() != str(b).strip().lower()


def _snapshot_changed(prev: SnapshotPoint, curr: SnapshotPoint) -> bool:
    """True if any tracked field changed between two snapshots."""
    return (
        _values_differ(prev.forecast_qty, curr.forecast_qty)
        or _values_differ(prev.roj, curr.roj)
        or _values_differ(prev.supplier, curr.supplier)
        or _values_differ(prev.bod, curr.bod)
        or _values_differ(prev.ff, curr.ff)
    )


def _qty_trend(qtys: List[Optional[float]]) -> str:
    """Classify the qty movement across snapshots."""
    valid = [q for q in qtys if q is not None]
    if len(valid) < 2:
        return "stable"
    diffs = [valid[i + 1] - valid[i] for i in range(len(valid) - 1)]
    if all(d > 0 for d in diffs):
        return "increasing"
    if all(d < 0 for d in diffs):
        return "decreasing"
    if all(d == 0 for d in diffs):
        return "stable"
    return "volatile"


def _detect_spike(qtys: List[Optional[float]], dates: List[str]) -> tuple:
    """
    A one-off spike: exactly one snapshot where qty > 2x the previous value,
    and the value returns close to baseline afterwards.
    Returns (is_one_off, spike_dates).
    """
    valid_pairs = [
        (dates[i + 1], qtys[i], qtys[i + 1])
        for i in range(len(qtys) - 1)
        if qtys[i] is not None and qtys[i + 1] is not None and qtys[i] > 0
    ]
    spike_dates = [date for date, prev, curr in valid_pairs if curr > 2 * prev]

    if len(spike_dates) != 1:
        return False, spike_dates

    # Check recovery: value after spike should drop back
    spike_idx = dates.index(spike_dates[0])
    if spike_idx + 1 < len(qtys) and qtys[spike_idx + 1] is not None:
        spike_val = qtys[spike_idx]
        after_val = qtys[spike_idx + 1]
        if spike_val is not None and after_val < spike_val:
            return True, spike_dates

    return False, spike_dates


def _change_streak(snapshots: List[SnapshotPoint]) -> int:
    """Count consecutive changed snapshots from the most recent end."""
    streak = 0
    for i in range(len(snapshots) - 1, 0, -1):
        if _snapshot_changed(snapshots[i - 1], snapshots[i]):
            streak += 1
        else:
            break
    return streak


def analyze_trends(
    snapshots_input: List[Dict],
    location_id: Optional[str] = None,
    material_group: Optional[str] = None,
    recurring_threshold: int = RECURRING_THRESHOLD,
) -> List[TrendRecord]:
    """
    snapshots_input: list of { "snapshot_date": "YYYY-MM-DD", "rows": [...] }
    Sorted by snapshot_date ascending internally.
    """
    # Sort snapshots oldest -> newest
    ordered = sorted(snapshots_input, key=lambda s: s["snapshot_date"])

    # Build per-key timeline: key -> list of (snapshot_date, PlanningRecord)
    timeline: Dict[tuple, List[tuple]] = {}

    for snap in ordered:
        date = snap["snapshot_date"]
        rows = snap.get("rows", [])
        records = normalize_rows(rows, is_current=True)
        filtered = filter_records(records, location_id, material_group)
        for rec in filtered:
            timeline.setdefault(rec.key, []).append((date, rec))

    results: List[TrendRecord] = []

    for key, entries in timeline.items():
        loc_id, mat_grp, mat_id = key
        snap_points = [build_snapshot_point(rec, date) for date, rec in entries]
        qtys = [sp.forecast_qty for sp in snap_points]
        dates = [sp.snapshot_date for sp in snap_points]

        # Count snapshots with changes
        changed_count = sum(
            1 for i in range(1, len(snap_points))
            if _snapshot_changed(snap_points[i - 1], snap_points[i])
        )

        qty_trend = _qty_trend(qtys)
        streak = _change_streak(snap_points)
        is_one_off, spike_dates = _detect_spike(qtys, dates)

        trend = TrendRecord(
            location_id=loc_id,
            material_group=mat_grp,
            material_id=mat_id,
            snapshots=snap_points,
            qty_trend=qty_trend,
            change_streak=streak,
            changed_snapshot_count=changed_count,
            is_recurring=changed_count >= recurring_threshold,
            is_one_off_spike=is_one_off,
            spike_dates=spike_dates,
            consistently_increasing=qty_trend == "increasing",
            consistently_decreasing=qty_trend == "decreasing",
            qty_values=qtys,
            snapshot_dates=dates,
        )
        results.append(trend)

    return results


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_consistently_increasing(trends: List[TrendRecord]) -> List[dict]:
    return [_serialize(t) for t in trends if t.consistently_increasing]


def get_recurring_changes(trends: List[TrendRecord]) -> List[dict]:
    return [_serialize(t) for t in trends if t.is_recurring]


def get_one_off_spikes(trends: List[TrendRecord]) -> List[dict]:
    return [_serialize(t) for t in trends if t.is_one_off_spike]


def get_change_streaks(trends: List[TrendRecord], min_streak: int = 2) -> List[dict]:
    """Materials that have changed in N or more consecutive snapshots."""
    return [_serialize(t) for t in trends if t.change_streak >= min_streak]


def build_trend_summary(trends: List[TrendRecord]) -> dict:
    return {
        "total_materials_tracked": len(trends),
        "consistently_increasing_count": sum(1 for t in trends if t.consistently_increasing),
        "consistently_decreasing_count": sum(1 for t in trends if t.consistently_decreasing),
        "recurring_change_count": sum(1 for t in trends if t.is_recurring),
        "one_off_spike_count": sum(1 for t in trends if t.is_one_off_spike),
        "volatile_count": sum(1 for t in trends if t.qty_trend == "volatile"),
        "stable_count": sum(1 for t in trends if t.qty_trend == "stable"),
        "consistently_increasing": get_consistently_increasing(trends),
        "recurring_changes": get_recurring_changes(trends),
        "one_off_spikes": get_one_off_spikes(trends),
    }


def _serialize(t: TrendRecord) -> dict:
    from dataclasses import asdict
    return asdict(t)
