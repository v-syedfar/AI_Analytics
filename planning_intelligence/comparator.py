from typing import Optional
from models import PlanningRecord, ComparedRecord


def _values_differ(a, b) -> bool:
    """Treat None == None as no change; otherwise compare as strings."""
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    return str(a).strip().lower() != str(b).strip().lower()


def _derive_change_type(rec: ComparedRecord) -> str:
    parts = []
    if rec.qty_changed:
        parts.append("Qty")
    if rec.roj_changed:
        parts.append("ROJ")
    if rec.supplier_changed:
        parts.append("Supplier")
    if rec.design_changed:
        parts.append("Design")
    return " + ".join(parts) if parts else "Unchanged"


def _derive_risk_level(rec: ComparedRecord) -> str:
    if rec.design_changed and rec.supplier_changed:
        return "Design + Supplier Change Risk"
    if rec.design_changed:
        return "Design Change Risk"
    if rec.supplier_changed:
        return "Supplier Change Risk"
    if (
        rec.qty_changed
        and rec.forecast_qty_previous is not None
        and rec.forecast_qty_current is not None
        and rec.forecast_qty_previous > 0
        and rec.forecast_qty_current > 2 * rec.forecast_qty_previous
    ):
        return "High Demand Spike"
    return "Normal"


def compare_records(
    current: list[PlanningRecord],
    previous: list[PlanningRecord],
) -> list[ComparedRecord]:
    """
    Match records by (location_id, material_group, material_id) and compare.
    Records only in current (new) are included with previous fields as None.
    """
    prev_map: dict[tuple, PlanningRecord] = {r.key: r for r in previous}
    results: list[ComparedRecord] = []

    for cur in current:
        prev = prev_map.get(cur.key)

        qty_changed = _values_differ(cur.forecast_qty, prev.forecast_qty if prev else None)
        roj_changed = _values_differ(cur.roj, prev.roj if prev else None)
        supplier_changed = _values_differ(cur.supplier, prev.supplier if prev else None)

        # Strict design change: BOD or FF changed, but NOT for new demand or cancelled
        bod_changed = _values_differ(cur.bod, prev.bod if prev else None)
        ff_changed = _values_differ(cur.ff, prev.ff if prev else None)
        is_new = cur.is_new_demand or (prev is None)
        is_cancelled = cur.is_cancelled
        design_changed = (bod_changed or ff_changed) and not is_new and not is_cancelled

        qty_delta: Optional[float] = None
        if cur.forecast_qty is not None and prev is not None and prev.forecast_qty is not None:
            qty_delta = cur.forecast_qty - prev.forecast_qty

        rec = ComparedRecord(
            location_id=cur.location_id,
            material_group=cur.material_group,
            material_id=cur.material_id,
            supplier_current=cur.supplier,
            supplier_previous=prev.supplier if prev else None,
            forecast_qty_current=cur.forecast_qty,
            forecast_qty_previous=prev.forecast_qty if prev else None,
            roj_current=cur.roj,
            roj_previous=prev.roj if prev else None,
            bod_current=cur.bod,
            bod_previous=prev.bod if prev else None,
            ff_current=cur.ff,
            ff_previous=prev.ff if prev else None,
            roc_region=cur.roc_region,
            dc_site=cur.dc_site,
            metro=cur.metro,
            country=cur.country,
            supplier_date=cur.supplier_date,
            planning_exception=cur.planning_exception,
            roj_reason_code=cur.roj_reason_code,
            automation_reason=cur.automation_reason,
            qty_changed=qty_changed,
            roj_changed=roj_changed,
            supplier_changed=supplier_changed,
            design_changed=design_changed,
            qty_delta=qty_delta,
            # Enhanced flags
            is_new_demand=is_new,
            is_cancelled=is_cancelled,
            risk_flag=cur.risk_flag,
            fcst_delta_qty=cur.fcst_delta_qty or qty_delta,
            nbd_delta_days=cur.nbd_delta_days,
            is_supplier_date_missing=cur.is_supplier_date_missing,
            bod_changed=bod_changed,
            ff_changed=ff_changed,
        )
        rec.change_type = _derive_change_type(rec)
        rec.risk_level = _derive_risk_level(rec)
        results.append(rec)

    return results
