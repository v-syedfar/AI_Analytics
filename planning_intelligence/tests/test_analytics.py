import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import ComparedRecord
from analytics import (
    build_summary,
    build_location_material_list,
    filter_by_supplier_design_change,
    changes_by_location,
    changes_by_material_group,
    change_driver_analysis,
    high_risk_records,
)


def _rec(mid, loc="LOC001", mg="PUMP", change_type="Unchanged", risk_level="Normal",
         qty_changed=False, roj_changed=False, supplier_changed=False, design_changed=False) -> ComparedRecord:
    return ComparedRecord(
        location_id=loc, material_group=mg, material_id=mid,
        supplier_current="A", supplier_previous="A",
        forecast_qty_current=50.0, forecast_qty_previous=50.0,
        roj_current="2026-06-01", roj_previous="2026-06-01",
        bod_current="v1", bod_previous="v1",
        ff_current="FF-A", ff_previous="FF-A",
        change_type=change_type, risk_level=risk_level,
        qty_changed=qty_changed, roj_changed=roj_changed,
        supplier_changed=supplier_changed, design_changed=design_changed,
    )


RECORDS = [
    _rec("MAT-1"),
    _rec("MAT-2", change_type="Qty", risk_level="High Demand Spike", qty_changed=True),
    _rec("MAT-3", loc="LOC002", change_type="Supplier", risk_level="Supplier Change Risk", supplier_changed=True),
    _rec("MAT-4", loc="LOC002", mg="VALVE", change_type="Design", risk_level="Design Change Risk", design_changed=True),
    _rec("MAT-5", loc="LOC001", change_type="Qty + ROJ", qty_changed=True, roj_changed=True),
]


# --- Q1: How many records changed? ---
def test_changed_count():
    s = build_summary(RECORDS)
    assert s["changed_record_count"] == 4
    assert s["unchanged_record_count"] == 1
    assert s["total_available_records"] == 5


# --- Q2: Which material IDs changed? ---
def test_changed_material_ids():
    s = build_summary(RECORDS)
    assert set(s["changed_material_ids"]) == {"MAT-2", "MAT-3", "MAT-4", "MAT-5"}


# --- Q3: Which locations have the most changes? ---
def test_changes_by_location():
    result = changes_by_location(RECORDS)
    by_loc = {r["location_id"]: r["change_count"] for r in result["changes_by_location"]}
    assert by_loc["LOC001"] == 2   # MAT-2, MAT-5
    assert by_loc["LOC002"] == 2   # MAT-3, MAT-4
    # sorted descending
    counts = [r["change_count"] for r in result["changes_by_location"]]
    assert counts == sorted(counts, reverse=True)


# --- Q4: Which material groups have changes? ---
def test_changes_by_material_group():
    result = changes_by_material_group(RECORDS)
    by_mg = {r["material_group"]: r["change_count"] for r in result["changes_by_material_group"]}
    assert by_mg["PUMP"] == 3
    assert by_mg["VALVE"] == 1


# --- Q5: Change driver analysis ---
def test_change_driver_analysis():
    result = change_driver_analysis(RECORDS)
    d = result["change_driver_summary"]
    assert d["quantity_driven"] == 2   # MAT-2, MAT-5
    assert d["supplier_driven"] == 1   # MAT-3
    assert d["design_driven"] == 1     # MAT-4
    assert d["roj_driven"] == 1        # MAT-5


# --- Q6: High risk records ---
def test_high_risk_records():
    result = high_risk_records(RECORDS)
    assert result["high_risk_count"] == 3
    risk_ids = {r["material_id"] for r in result["high_risk_records"]}
    assert risk_ids == {"MAT-2", "MAT-3", "MAT-4"}
    assert "High Demand Spike" in result["risk_level_summary"]
    assert "Supplier Change Risk" in result["risk_level_summary"]
    assert "Design Change Risk" in result["risk_level_summary"]


# --- Summary includes all six dimensions ---
def test_full_summary_has_all_keys():
    s = build_summary(RECORDS)
    for key in [
        "total_available_records", "changed_record_count", "unchanged_record_count",
        "changed_material_ids", "changes_by_location", "changes_by_material_group",
        "change_driver_summary", "high_risk_records", "change_type_summary", "changed_records",
    ]:
        assert key in s, f"Missing key: {key}"


# --- Supplier + design change filter ---
def test_supplier_design_changes():
    records = [
        _rec("MAT-X", change_type="Supplier + Design", risk_level="Design + Supplier Change Risk",
             supplier_changed=True, design_changed=True),
        _rec("MAT-Y", change_type="Supplier", risk_level="Supplier Change Risk", supplier_changed=True),
    ]
    result = filter_by_supplier_design_change(records)
    assert len(result) == 1
    assert result[0]["material_id"] == "MAT-X"
