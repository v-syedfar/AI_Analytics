import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import ComparedRecord
from dashboard_builder import build_dashboard_response


def _rec(mid, change_type="Unchanged", risk_level="Normal",
         qty_changed=False, supplier_changed=False, design_changed=False, roj_changed=False,
         qty_current=50.0, qty_prev=50.0, supplier="SUP-A", loc="LOC001", mg="PUMP") -> ComparedRecord:
    return ComparedRecord(
        location_id=loc, material_group=mg, material_id=mid,
        supplier_current=supplier, supplier_previous=supplier,
        forecast_qty_current=qty_current, forecast_qty_previous=qty_prev,
        roj_current="2026-06-01", roj_previous="2026-06-01",
        bod_current="v1", bod_previous="v1",
        ff_current="FF-A", ff_previous="FF-A",
        change_type=change_type, risk_level=risk_level,
        qty_changed=qty_changed, supplier_changed=supplier_changed,
        design_changed=design_changed, roj_changed=roj_changed,
        qty_delta=qty_current - qty_prev if qty_prev else None,
    )


RECORDS = [
    _rec("MAT-1"),
    _rec("MAT-2", "Qty", "High Demand Spike", qty_changed=True, qty_current=120, qty_prev=50),
    _rec("MAT-3", "Supplier", "Supplier Change Risk", supplier_changed=True, supplier="SUP-B"),
    _rec("MAT-4", "Design", "Design Change Risk", design_changed=True),
]


def test_dashboard_has_required_keys():
    result = build_dashboard_response(RECORDS, [])
    for key in [
        "planningHealth", "forecastNew", "forecastOld", "trendDelta", "trendDirection",
        "totalRecords", "changedRecordCount", "unchangedRecordCount", "newRecordCount",
        "changeDrivers", "datacenterSummary", "materialGroupSummary",
        "supplierSummary", "designSummary", "rojSummary", "riskSummary",
        "aiInsight", "rootCause", "recommendedActions", "detailRecords", "filters",
    ]:
        assert key in result, f"Missing key: {key}"


def test_health_score_range():
    result = build_dashboard_response(RECORDS, [])
    score = result["planningHealth"]["score"]
    assert 0 <= score <= 100


def test_changed_count():
    result = build_dashboard_response(RECORDS, [])
    assert result["changedRecordCount"] == 3
    assert result["unchangedRecordCount"] == 1
    assert result["totalRecords"] == 4


def test_risk_summary():
    result = build_dashboard_response(RECORDS, [])
    assert result["riskSummary"]["highRiskCount"] == 3
    assert result["riskSummary"]["highestRiskLevel"] in (
        "Design Change Risk", "Supplier Change Risk", "High Demand Spike",
        "Design + Supplier Change Risk"
    )


def test_ai_insight_not_empty():
    result = build_dashboard_response(RECORDS, [])
    assert len(result["aiInsight"]) > 20
    assert len(result["rootCause"]) > 20
    assert len(result["recommendedActions"]) > 0


def test_supplier_summary_only_changed():
    result = build_dashboard_response(RECORDS, [])
    # Only MAT-3 has supplier_changed=True
    assert len(result["supplierSummary"]) == 1
    assert result["supplierSummary"][0]["supplier"] == "SUP-B"


def test_design_summary_only_changed():
    result = build_dashboard_response(RECORDS, [])
    assert len(result["designSummary"]) == 1
    assert result["designSummary"][0]["materialId"] == "MAT-4"


def test_filter_context_preserved():
    result = build_dashboard_response(RECORDS, [], location_id="LOC001", material_group="PUMP")
    assert result["filters"]["locationId"] == "LOC001"
    assert result["filters"]["materialGroup"] == "PUMP"
