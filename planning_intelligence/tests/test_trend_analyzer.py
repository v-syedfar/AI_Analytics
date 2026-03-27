import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from trend_analyzer import (
    analyze_trends,
    build_trend_summary,
    get_consistently_increasing,
    get_recurring_changes,
    get_one_off_spikes,
    get_change_streaks,
)

# ---------------------------------------------------------------------------
# Helpers to build snapshot input
# ---------------------------------------------------------------------------

def _row(mid, qty, roj="2026-06-01", supplier="SUP-A", bod="v1", ff="FF-A"):
    return {
        "LOCID": "LOC001", "GSCEQUIPCAT": "PUMP", "PRDID": mid,
        "LOCFR": supplier, "GSCFSCTQTY": qty, "GSCCONROJDATE": roj,
        "ZCOIBODVER": bod, "ZCOIFORMFACT": ff,
        "LASTMODIFIEDBY": "user1", "LASTMODIFIEDDATE": "2026-03-01",
    }


def _snap(date, rows):
    return {"snapshot_date": date, "rows": rows}


# ---------------------------------------------------------------------------
# Consistently increasing
# ---------------------------------------------------------------------------

def test_consistently_increasing():
    snaps = [
        _snap("2026-03-01", [_row("MAT-1", 10)]),
        _snap("2026-03-08", [_row("MAT-1", 20)]),
        _snap("2026-03-15", [_row("MAT-1", 30)]),
        _snap("2026-03-22", [_row("MAT-1", 40)]),
    ]
    trends = analyze_trends(snaps)
    assert len(trends) == 1
    assert trends[0].consistently_increasing is True
    assert trends[0].qty_trend == "increasing"


def test_not_consistently_increasing_when_dip():
    snaps = [
        _snap("2026-03-01", [_row("MAT-1", 10)]),
        _snap("2026-03-08", [_row("MAT-1", 20)]),
        _snap("2026-03-15", [_row("MAT-1", 15)]),  # dip
    ]
    trends = analyze_trends(snaps)
    assert trends[0].consistently_increasing is False
    assert trends[0].qty_trend == "volatile"


# ---------------------------------------------------------------------------
# Recurring changes
# ---------------------------------------------------------------------------

def test_recurring_changes():
    snaps = [
        _snap("2026-03-01", [_row("MAT-2", 10)]),
        _snap("2026-03-08", [_row("MAT-2", 20)]),   # change 1
        _snap("2026-03-15", [_row("MAT-2", 30)]),   # change 2
        _snap("2026-03-22", [_row("MAT-2", 40)]),   # change 3
    ]
    trends = analyze_trends(snaps, recurring_threshold=3)
    assert trends[0].is_recurring is True
    assert trends[0].changed_snapshot_count == 3


def test_not_recurring_below_threshold():
    snaps = [
        _snap("2026-03-01", [_row("MAT-3", 10)]),
        _snap("2026-03-08", [_row("MAT-3", 20)]),   # change 1
        _snap("2026-03-15", [_row("MAT-3", 20)]),   # no change
    ]
    trends = analyze_trends(snaps, recurring_threshold=3)
    assert trends[0].is_recurring is False


# ---------------------------------------------------------------------------
# One-off spike
# ---------------------------------------------------------------------------

def test_one_off_spike():
    snaps = [
        _snap("2026-03-01", [_row("MAT-4", 10)]),
        _snap("2026-03-08", [_row("MAT-4", 10)]),
        _snap("2026-03-15", [_row("MAT-4", 100)]),  # spike > 2x
        _snap("2026-03-22", [_row("MAT-4", 12)]),   # recovers
    ]
    trends = analyze_trends(snaps)
    assert trends[0].is_one_off_spike is True
    assert "2026-03-15" in trends[0].spike_dates


def test_not_one_off_when_multiple_spikes():
    snaps = [
        _snap("2026-03-01", [_row("MAT-5", 10)]),
        _snap("2026-03-08", [_row("MAT-5", 100)]),  # spike 1
        _snap("2026-03-15", [_row("MAT-5", 10)]),
        _snap("2026-03-22", [_row("MAT-5", 100)]),  # spike 2
    ]
    trends = analyze_trends(snaps)
    assert trends[0].is_one_off_spike is False


# ---------------------------------------------------------------------------
# Change streak
# ---------------------------------------------------------------------------

def test_change_streak():
    snaps = [
        _snap("2026-03-01", [_row("MAT-6", 10)]),
        _snap("2026-03-08", [_row("MAT-6", 10)]),   # no change
        _snap("2026-03-15", [_row("MAT-6", 20)]),   # streak start
        _snap("2026-03-22", [_row("MAT-6", 30)]),   # streak 2
        _snap("2026-03-29", [_row("MAT-6", 40)]),   # streak 3
    ]
    trends = analyze_trends(snaps)
    assert trends[0].change_streak == 3


def test_streak_resets_on_no_change():
    snaps = [
        _snap("2026-03-01", [_row("MAT-7", 10)]),
        _snap("2026-03-08", [_row("MAT-7", 20)]),   # change
        _snap("2026-03-15", [_row("MAT-7", 20)]),   # no change — streak resets
    ]
    trends = analyze_trends(snaps)
    assert trends[0].change_streak == 0


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def test_filter_by_location_in_trend():
    snaps = [
        _snap("2026-03-01", [
            _row("MAT-8", 10),
            {"LOCID": "LOC002", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-9",
             "LOCFR": "SUP-A", "GSCFSCTQTY": 10, "GSCCONROJDATE": "2026-06-01",
             "ZCOIBODVER": "v1", "ZCOIFORMFACT": "FF-A"},
        ]),
    ]
    trends = analyze_trends(snaps, location_id="LOC001")
    assert all(t.location_id == "LOC001" for t in trends)
    assert len(trends) == 1


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def test_trend_summary_keys():
    snaps = [
        _snap("2026-03-01", [_row("MAT-10", 10)]),
        _snap("2026-03-08", [_row("MAT-10", 25)]),
        _snap("2026-03-15", [_row("MAT-10", 60)]),
    ]
    trends = analyze_trends(snaps)
    summary = build_trend_summary(trends)
    for key in [
        "total_materials_tracked", "consistently_increasing_count",
        "recurring_change_count", "one_off_spike_count",
        "volatile_count", "stable_count",
        "consistently_increasing", "recurring_changes", "one_off_spikes",
    ]:
        assert key in summary, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Snapshots sorted regardless of input order
# ---------------------------------------------------------------------------

def test_snapshots_sorted_by_date():
    snaps = [
        _snap("2026-03-15", [_row("MAT-11", 30)]),
        _snap("2026-03-01", [_row("MAT-11", 10)]),  # out of order
        _snap("2026-03-08", [_row("MAT-11", 20)]),
    ]
    trends = analyze_trends(snaps)
    assert trends[0].snapshot_dates == ["2026-03-01", "2026-03-08", "2026-03-15"]
    assert trends[0].qty_values == [10.0, 20.0, 30.0]
    assert trends[0].consistently_increasing is True
