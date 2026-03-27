import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from alert_rules import evaluate_alerts, alert_to_dict


def _base(**kwargs):
    defaults = dict(
        planning_health=80, status="Healthy",
        forecast_new=500, forecast_old=450, trend_delta=50,
        trend_direction="increasing",
        quantity_changed_count=2, supplier_changed_count=0,
        design_changed_count=0, roj_changed_count=0,
        highest_risk_level="Normal",
        top_impacted_location="LOC001",
        top_impacted_supplier=None,
        top_impacted_material_group="PUMP",
        total_records=100, new_record_count=0,
    )
    return {**defaults, **kwargs}


def test_no_alert_when_healthy():
    alert = evaluate_alerts(**_base())
    assert alert.should_trigger is False
    assert alert.severity == "info"


def test_health_critical():
    alert = evaluate_alerts(**_base(planning_health=30))
    assert alert.should_trigger is True
    assert alert.severity == "critical"
    assert alert.trigger_type == "health_critical"


def test_health_drop():
    alert = evaluate_alerts(**_base(planning_health=55))
    assert alert.should_trigger is True
    assert alert.severity == "high"
    assert alert.trigger_type == "health_drop"


def test_demand_spike():
    alert = evaluate_alerts(**_base(
        forecast_new=600, forecast_old=400, trend_delta=200,
        trend_direction="increasing",
    ))
    assert alert.should_trigger is True
    assert alert.trigger_type == "demand_spike"


def test_design_change_alert():
    alert = evaluate_alerts(**_base(design_changed_count=2, highest_risk_level="Design Change Risk"))
    assert alert.should_trigger is True
    assert alert.trigger_type == "design_change"
    assert alert.severity == "high"


def test_supplier_change_alert():
    alert = evaluate_alerts(**_base(supplier_changed_count=3, top_impacted_supplier="SUP-A"))
    assert alert.should_trigger is True
    assert alert.trigger_type == "supplier_change"
    assert alert.severity == "warning"


def test_combined_risk_critical():
    alert = evaluate_alerts(**_base(
        design_changed_count=1, supplier_changed_count=1,
        highest_risk_level="Design + Supplier Change Risk",
    ))
    assert alert.should_trigger is True
    assert alert.severity == "critical"
    assert alert.trigger_type == "combined_risk"


def test_new_records_info():
    alert = evaluate_alerts(**_base(new_record_count=5))
    assert alert.should_trigger is True
    assert alert.severity == "info"
    assert alert.trigger_type == "new_records"


def test_alert_to_dict():
    alert = evaluate_alerts(**_base(planning_health=30))
    d = alert_to_dict(alert)
    assert "shouldTrigger" in d
    assert "severity" in d
    assert "message" in d
    assert "triggerType" in d


def test_highest_severity_wins():
    # Both design change (high) and health critical should return critical
    alert = evaluate_alerts(**_base(
        planning_health=30,
        design_changed_count=2,
        highest_risk_level="Design + Supplier Change Risk",
    ))
    assert alert.severity == "critical"
