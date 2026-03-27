import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import ComparedRecord
from mcp.tools import (
    analytics_context_tool,
    risk_summary_tool,
    root_cause_driver_tool,
    recommendation_tool,
    alert_trigger_tool,
)


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
        qty_delta=qty_current - qty_prev,
    )


RECORDS = [
    _rec("MAT-1"),
    _rec("MAT-2", "Qty", "High Demand Spike", qty_changed=True, qty_current=120, qty_prev=50),
    _rec("MAT-3", "Supplier", "Supplier Change Risk", supplier_changed=True, supplier="SUP-B"),
    _rec("MAT-4", "Design", "Design Change Risk", design_changed=True),
]


def test_analytics_context_tool():
    ctx = analytics_context_tool(RECORDS, 72, "increasing")
    assert ctx.total_records == 4
    assert ctx.planning_health == 72
    assert ctx.trend_direction == "increasing"
    assert ctx.quantity_changed_count == 1
    assert ctx.supplier_changed_count == 1
    assert ctx.design_changed_count == 1
    assert ctx.top_impacted_location == "LOC001"


def test_risk_summary_tool():
    risk = risk_summary_tool(RECORDS)
    assert risk.high_risk_count == 3
    assert risk.highest_risk_level in (
        "Design Change Risk", "Supplier Change Risk",
        "High Demand Spike", "Design + Supplier Change Risk"
    )
    assert len(risk.risk_drivers) > 0


def test_root_cause_driver_tool():
    root = root_cause_driver_tool(RECORDS)
    assert root.primary_driver in ("quantity", "supplier", "design", "schedule")
    assert root.driver_location == "LOC001"
    assert root.change_type_label != ""


def test_recommendation_tool():
    ctx = analytics_context_tool(RECORDS, 72, "increasing")
    risk = risk_summary_tool(RECORDS)
    root = root_cause_driver_tool(RECORDS)
    recs = recommendation_tool(ctx, risk, root)
    assert len(recs.actions) > 0


def test_alert_trigger_tool():
    ctx = analytics_context_tool(RECORDS, 40, "increasing")
    risk = risk_summary_tool(RECORDS)
    alert = alert_trigger_tool(ctx, risk)
    assert "shouldTrigger" in alert
    assert "severity" in alert
    assert "message" in alert


def test_stable_records_no_alert():
    stable = [_rec("MAT-S1"), _rec("MAT-S2")]
    ctx = analytics_context_tool(stable, 95, "stable")
    risk = risk_summary_tool(stable)
    alert = alert_trigger_tool(ctx, risk)
    assert alert["shouldTrigger"] is False
