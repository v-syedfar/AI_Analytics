"""
Integration Tests
Tests the full pipeline end-to-end without Azure Functions runtime.
Simulates HTTP requests through the analytics pipeline directly.
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from normalizer import normalize_rows
from filters import filter_records
from comparator import compare_records
from analytics import build_summary
from response_builder import build_response
from snapshot_store import save_snapshot, load_snapshot, clear_snapshot
from alert_rules import evaluate_alerts, alert_to_dict
from mcp.tools import analytics_context_tool, risk_summary_tool, root_cause_driver_tool

# ---------------------------------------------------------------------------
# Sample payloads (mirrors samples/request.json)
# ---------------------------------------------------------------------------

CURRENT_ROWS = [
    {
        "LOCID": "LOC001", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-100",
        "LOCFR": "SUP-A", "GSCFSCTQTY": 120, "GSCCONROJDATE": "2026-07-01",
        "ZCOIBODVER": "v3", "ZCOIFORMFACT": "FF-B",
        "ZCOIDCID": "DC-WEST", "ZCOICOUNTRY": "US",
    },
    {
        "LOCID": "LOC001", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-101",
        "LOCFR": "SUP-B", "GSCFSCTQTY": 50, "GSCCONROJDATE": "2026-06-15",
        "ZCOIBODVER": "v1", "ZCOIFORMFACT": "FF-A",
        "ZCOIDCID": "DC-WEST", "ZCOICOUNTRY": "US",
    },
]

PREVIOUS_ROWS = [
    {
        "LOCID": "LOC001", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-100",
        "LOCFR": "SUP-A", "GSCPREVFCSTQTY": 50, "GSCPREVROJNBD": "2026-06-01",
        "ZCOIBODVER": "v2", "ZCOIFORMFACT": "FF-A",
    },
    {
        "LOCID": "LOC001", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-101",
        "LOCFR": "SUP-B", "GSCPREVFCSTQTY": 50, "GSCPREVROJNBD": "2026-06-15",
        "ZCOIBODVER": "v1", "ZCOIFORMFACT": "FF-A",
    },
]


def _run_pipeline(current_rows, previous_rows, location_id=None, material_group=None):
    """Runs the full analytics pipeline and returns compared records."""
    current = normalize_rows(current_rows, is_current=True)
    previous = normalize_rows(previous_rows, is_current=False)
    current_f = filter_records(current, location_id, material_group)
    previous_f = filter_records(previous, location_id, material_group)
    return compare_records(current_f, previous_f)


# ---------------------------------------------------------------------------
# Pipeline integration tests
# ---------------------------------------------------------------------------

def test_full_pipeline_returns_correct_change_count():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    assert len(compared) == 2
    changed = [r for r in compared if r.change_type != "Unchanged"]
    assert len(changed) == 1
    assert changed[0].material_id == "MAT-100"


def test_full_pipeline_detects_design_change():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    mat100 = next(r for r in compared if r.material_id == "MAT-100")
    assert mat100.design_changed is True
    assert mat100.bod_previous == "v2"
    assert mat100.bod_current == "v3"
    assert mat100.ff_previous == "FF-A"
    assert mat100.ff_current == "FF-B"


def test_full_pipeline_detects_qty_change():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    mat100 = next(r for r in compared if r.material_id == "MAT-100")
    assert mat100.qty_changed is True
    assert mat100.qty_delta == 70.0


def test_full_pipeline_detects_roj_change():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    mat100 = next(r for r in compared if r.material_id == "MAT-100")
    assert mat100.roj_changed is True


def test_full_pipeline_risk_classification():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    mat100 = next(r for r in compared if r.material_id == "MAT-100")
    assert mat100.risk_level == "Design Change Risk"


def test_full_pipeline_unchanged_record():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    mat101 = next(r for r in compared if r.material_id == "MAT-101")
    assert mat101.change_type == "Unchanged"
    assert mat101.risk_level == "Normal"


def test_filter_reduces_records():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS, location_id="LOC001", material_group="PUMP")
    assert len(compared) == 2

    compared_filtered = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS, location_id="LOC002")
    assert len(compared_filtered) == 0


# ---------------------------------------------------------------------------
# Summary integration tests
# ---------------------------------------------------------------------------

def test_build_summary_from_pipeline():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    summary = build_summary(compared)
    assert summary["total_available_records"] == 2
    assert summary["changed_record_count"] == 1
    assert "MAT-100" in summary["changed_material_ids"]


# ---------------------------------------------------------------------------
# Response builder integration tests
# ---------------------------------------------------------------------------

def test_build_response_full_pipeline():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    result = build_response(compared, [], data_mode="live")

    assert result["dataMode"] == "live"
    assert result["totalRecords"] == 2
    assert result["changedRecordCount"] == 1
    assert result["planningHealth"] > 0
    assert result["planningHealth"] <= 100
    assert result["aiInsight"] != ""
    assert result["rootCause"] != ""
    assert len(result["recommendedActions"]) > 0
    assert "alerts" in result
    assert result["designSummary"]["status"] == "Changed"
    assert result["rojSummary"]["status"] == "Changed"


def test_build_response_json_serializable():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    result = build_response(compared, [], data_mode="live")
    # Must be JSON serializable — no datetime objects etc.
    serialized = json.dumps(result, default=str)
    parsed = json.loads(serialized)
    assert parsed["totalRecords"] == 2


# ---------------------------------------------------------------------------
# MCP tool integration tests
# ---------------------------------------------------------------------------

def test_mcp_tools_full_chain():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    ctx = analytics_context_tool(compared, 75, "increasing")
    risk = risk_summary_tool(compared)
    root = root_cause_driver_tool(compared)

    assert ctx.total_records == 2
    assert ctx.design_changed_count == 1
    assert ctx.quantity_changed_count == 1
    assert risk.highest_risk_level == "Design Change Risk"
    assert root.primary_driver in ("quantity", "design", "schedule")
    assert root.driver_location == "LOC001"


# ---------------------------------------------------------------------------
# Snapshot store integration tests
# ---------------------------------------------------------------------------

def test_snapshot_roundtrip():
    import tempfile
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    result = build_response(compared, [], data_mode="cached")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_snapshot(result, path=path)
        loaded = load_snapshot(path=path)
        assert loaded is not None
        assert loaded["dataMode"] == "cached"
        assert loaded["totalRecords"] == 2
        assert "lastRefreshedAt" in loaded
    finally:
        clear_snapshot(path=path)
        if os.path.exists(path):
            os.remove(path)


# ---------------------------------------------------------------------------
# Alert integration tests
# ---------------------------------------------------------------------------

def test_alert_triggered_for_design_change():
    compared = _run_pipeline(CURRENT_ROWS, PREVIOUS_ROWS)
    ctx = analytics_context_tool(compared, 75, "increasing")
    risk = risk_summary_tool(compared)

    from mcp.tools import alert_trigger_tool
    alert = alert_trigger_tool(ctx, risk)
    assert alert["shouldTrigger"] is True
    assert alert["severity"] in ("high", "critical", "warning")


def test_no_alert_for_unchanged_records():
    # Both records unchanged
    same_rows = [
        {"LOCID": "LOC001", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-200",
         "LOCFR": "SUP-A", "GSCFSCTQTY": 50, "GSCCONROJDATE": "2026-06-01",
         "ZCOIBODVER": "v1", "ZCOIFORMFACT": "FF-A"},
    ]
    prev_rows = [
        {"LOCID": "LOC001", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-200",
         "LOCFR": "SUP-A", "GSCPREVFCSTQTY": 50, "GSCPREVROJNBD": "2026-06-01",
         "ZCOIBODVER": "v1", "ZCOIFORMFACT": "FF-A"},
    ]
    compared = _run_pipeline(same_rows, prev_rows)
    ctx = analytics_context_tool(compared, 100, "stable")
    risk = risk_summary_tool(compared)

    from mcp.tools import alert_trigger_tool
    alert = alert_trigger_tool(ctx, risk)
    assert alert["shouldTrigger"] is False
