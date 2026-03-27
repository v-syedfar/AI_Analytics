import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import PlanningRecord
from comparator import compare_records


def _rec(**kwargs) -> PlanningRecord:
    defaults = dict(
        location_id="LOC001", material_group="PUMP", material_id="MAT-100",
        supplier="Supplier A", forecast_qty=50.0, roj="2026-06-01",
        bod="v2", ff="FF-A",
    )
    return PlanningRecord(**{**defaults, **kwargs})


def test_no_change():
    cur = [_rec()]
    prev = [_rec()]
    result = compare_records(cur, prev)
    assert result[0].change_type == "Unchanged"
    assert result[0].risk_level == "Normal"


def test_qty_changed():
    cur = [_rec(forecast_qty=100.0)]
    prev = [_rec(forecast_qty=50.0)]
    result = compare_records(cur, prev)
    assert result[0].qty_changed is True
    assert result[0].qty_delta == 50.0
    assert "Qty" in result[0].change_type


def test_high_demand_spike():
    cur = [_rec(forecast_qty=110.0)]
    prev = [_rec(forecast_qty=50.0)]
    result = compare_records(cur, prev)
    assert result[0].risk_level == "High Demand Spike"


def test_supplier_changed():
    cur = [_rec(supplier="Supplier B")]
    prev = [_rec(supplier="Supplier A")]
    result = compare_records(cur, prev)
    assert result[0].supplier_changed is True
    assert result[0].risk_level == "Supplier Change Risk"


def test_design_changed_bod():
    cur = [_rec(bod="v3")]
    prev = [_rec(bod="v2")]
    result = compare_records(cur, prev)
    assert result[0].design_changed is True
    assert result[0].risk_level == "Design Change Risk"


def test_design_changed_ff():
    cur = [_rec(ff="FF-B")]
    prev = [_rec(ff="FF-A")]
    result = compare_records(cur, prev)
    assert result[0].design_changed is True


def test_new_record_no_previous():
    cur = [_rec(material_id="MAT-NEW")]
    prev = []
    result = compare_records(cur, prev)
    # All fields differ from None -> all flags True
    assert result[0].qty_changed is True


def test_multiple_changes():
    cur = [_rec(forecast_qty=200.0, supplier="New Supplier")]
    prev = [_rec(forecast_qty=50.0, supplier="Supplier A")]
    result = compare_records(cur, prev)
    assert result[0].qty_changed is True
    assert result[0].supplier_changed is True
    assert "Qty" in result[0].change_type
    assert "Supplier" in result[0].change_type


def test_design_and_supplier_both_changed():
    cur = [_rec(bod="v3", supplier="New Supplier")]
    prev = [_rec(bod="v2", supplier="Supplier A")]
    result = compare_records(cur, prev)
    assert result[0].design_changed is True
    assert result[0].supplier_changed is True
    assert result[0].risk_level == "Design + Supplier Change Risk"
