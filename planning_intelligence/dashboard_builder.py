"""
Dashboard Response Builder
Transforms raw analytics output into a structured dashboard JSON payload.
Keeps frontend decoupled from raw ComparedRecord / TrendRecord internals.
"""
from typing import Optional
from collections import Counter
from models import ComparedRecord, TrendRecord
from analytics import is_changed
from insight_generator import generate_insights


def build_dashboard_response(
    compared: list,           # list[ComparedRecord]
    trends: list,             # list[TrendRecord] — pass [] if not available
    location_id: Optional[str] = None,
    material_group: Optional[str] = None,
) -> dict:

    changed = [r for r in compared if is_changed(r)]
    unchanged = [r for r in compared if not is_changed(r)]
    total = len(compared)
    changed_count = len(changed)

    # --- Forecast aggregates ---
    forecast_new = sum(r.forecast_qty_current or 0 for r in compared)
    forecast_old = sum(r.forecast_qty_previous or 0 for r in compared if r.forecast_qty_previous is not None)
    trend_delta = forecast_new - forecast_old
    trend_direction = _classify_trend(trends, trend_delta)

    # --- New records (no previous match) ---
    new_records = sum(1 for r in compared if r.forecast_qty_previous is None)

    # --- Change driver counts ---
    qty_changed_count = sum(1 for r in changed if r.qty_changed)
    supplier_changed_count = sum(1 for r in changed if r.supplier_changed)
    design_changed_count = sum(1 for r in changed if r.design_changed)
    roj_changed_count = sum(1 for r in changed if r.roj_changed)

    # --- Risk summary ---
    risk_counts = Counter(r.risk_level for r in changed if r.risk_level != "Normal")
    highest_risk = _highest_risk(risk_counts)

    # --- Top impacted dimensions ---
    top_location = _top_by(changed, "location_id")
    top_supplier = _top_by_supplier(changed)
    top_material = _top_by(changed, "material_id")
    top_group = _top_by(changed, "material_group")

    # --- Datacenter / location summary ---
    dc_summary = _dc_summary(compared)

    # --- Material group summary ---
    mg_summary = _material_group_summary(compared)

    # --- Supplier summary ---
    supplier_summary = _supplier_summary(changed)

    # --- Design summary ---
    design_summary = _design_summary(changed)

    # --- ROJ summary ---
    roj_summary = _roj_summary(changed)

    # --- Planning health score (0-100) ---
    health_score = _compute_health_score(
        total, changed_count, highest_risk,
        design_changed_count, supplier_changed_count,
    )

    # --- AI Insight ---
    insights = generate_insights(
        total_records=total,
        matched_records=total - new_records,
        new_records=new_records,
        forecast_new=forecast_new,
        forecast_old=forecast_old,
        trend_delta=trend_delta,
        trend_direction=trend_direction,
        quantity_changed_count=qty_changed_count,
        supplier_changed_count=supplier_changed_count,
        design_changed_count=design_changed_count,
        roj_changed_count=roj_changed_count,
        highest_risk_level=highest_risk,
        top_impacted_location=top_location,
        top_impacted_supplier=top_supplier,
        top_impacted_material=top_material,
        top_impacted_material_group=top_group,
    )

    return {
        # Health
        "planningHealth": {
            "score": health_score,
            "status": _health_label(health_score),
        },

        # Forecast
        "forecastNew": round(forecast_new, 2),
        "forecastOld": round(forecast_old, 2),
        "trendDelta": round(trend_delta, 2),
        "trendDirection": trend_direction,

        # Counts
        "totalRecords": total,
        "changedRecordCount": changed_count,
        "unchangedRecordCount": len(unchanged),
        "newRecordCount": new_records,

        # Change drivers
        "changeDrivers": {
            "quantityChanged": qty_changed_count,
            "supplierChanged": supplier_changed_count,
            "designChanged": design_changed_count,
            "rojChanged": roj_changed_count,
        },

        # Summaries
        "datacenterSummary": dc_summary,
        "materialGroupSummary": mg_summary,
        "supplierSummary": supplier_summary,
        "designSummary": design_summary,
        "rojSummary": roj_summary,

        # Risk
        "riskSummary": {
            "highestRiskLevel": highest_risk,
            "riskBreakdown": dict(risk_counts),
            "highRiskCount": sum(risk_counts.values()),
            "highRiskRecords": [_slim_record(r) for r in changed if r.risk_level != "Normal"],
        },

        # AI
        "aiInsight": insights["aiInsight"],
        "rootCause": insights["rootCause"],
        "recommendedActions": insights["recommendedActions"],

        # Detail
        "detailRecords": [_slim_record(r) for r in changed],

        # Filter context
        "filters": {
            "locationId": location_id,
            "materialGroup": material_group,
        },
    }


# ---------------------------------------------------------------------------
# Summary builders
# ---------------------------------------------------------------------------

def _dc_summary(records: list) -> list:
    locs = {}
    for r in records:
        key = r.location_id
        if key not in locs:
            locs[key] = {"locationId": key, "dcSite": r.dc_site, "total": 0, "changed": 0}
        locs[key]["total"] += 1
        if is_changed(r):
            locs[key]["changed"] += 1
    return sorted(locs.values(), key=lambda x: -x["changed"])


def _material_group_summary(records: list) -> list:
    groups = {}
    for r in records:
        key = r.material_group
        if key not in groups:
            groups[key] = {"materialGroup": key, "total": 0, "changed": 0,
                           "qtyChanged": 0, "designChanged": 0, "supplierChanged": 0}
        groups[key]["total"] += 1
        if is_changed(r):
            groups[key]["changed"] += 1
            if r.qty_changed:
                groups[key]["qtyChanged"] += 1
            if r.design_changed:
                groups[key]["designChanged"] += 1
            if r.supplier_changed:
                groups[key]["supplierChanged"] += 1
    return sorted(groups.values(), key=lambda x: -x["changed"])


def _supplier_summary(changed: list) -> list:
    suppliers = {}
    for r in changed:
        if not r.supplier_changed:
            continue
        key = r.supplier_current or "Unknown"
        if key not in suppliers:
            suppliers[key] = {
                "supplier": key,
                "previousSupplier": r.supplier_previous,
                "affectedMaterials": [],
                "riskLevel": r.risk_level,
            }
        suppliers[key]["affectedMaterials"].append(r.material_id)
    return list(suppliers.values())


def _design_summary(changed: list) -> list:
    result = []
    for r in changed:
        if not r.design_changed:
            continue
        result.append({
            "materialId": r.material_id,
            "locationId": r.location_id,
            "materialGroup": r.material_group,
            "bodPrevious": r.bod_previous,
            "bodCurrent": r.bod_current,
            "ffPrevious": r.ff_previous,
            "ffCurrent": r.ff_current,
            "riskLevel": r.risk_level,
        })
    return result


def _roj_summary(changed: list) -> list:
    result = []
    for r in changed:
        if not r.roj_changed:
            continue
        result.append({
            "materialId": r.material_id,
            "locationId": r.location_id,
            "rojPrevious": r.roj_previous,
            "rojCurrent": r.roj_current,
            "rojReasonCode": r.roj_reason_code,
        })
    return result


# ---------------------------------------------------------------------------
# Health score
# ---------------------------------------------------------------------------

def _compute_health_score(
    total: int,
    changed: int,
    highest_risk: str,
    design_changed: int,
    supplier_changed: int,
) -> int:
    if total == 0:
        return 100
    score = 100
    change_pct = changed / total
    score -= int(change_pct * 40)                          # up to -40 for change volume
    if highest_risk == "Design + Supplier Change Risk":
        score -= 25
    elif highest_risk in ("Design Change Risk", "Supplier Change Risk"):
        score -= 15
    elif highest_risk == "High Demand Spike":
        score -= 10
    if design_changed > 0:
        score -= min(design_changed * 2, 10)
    if supplier_changed > 0:
        score -= min(supplier_changed * 2, 10)
    return max(0, min(100, score))


def _health_label(score: int) -> str:
    if score >= 80:
        return "Healthy"
    if score >= 60:
        return "Moderate"
    if score >= 40:
        return "At Risk"
    return "Critical"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_trend(trends: list, delta: float) -> str:
    if trends:
        directions = [t.qty_trend for t in trends]
        if all(d == "increasing" for d in directions):
            return "increasing"
        if all(d == "decreasing" for d in directions):
            return "decreasing"
        if all(d == "stable" for d in directions):
            return "stable"
        return "volatile"
    if delta > 0:
        return "increasing"
    if delta < 0:
        return "decreasing"
    return "stable"


def _highest_risk(risk_counts: Counter) -> str:
    priority = [
        "Design + Supplier Change Risk",
        "Design Change Risk",
        "Supplier Change Risk",
        "High Demand Spike",
    ]
    for level in priority:
        if level in risk_counts:
            return level
    return "Normal"


def _top_by(records: list, field: str) -> Optional[str]:
    if not records:
        return None
    counts = Counter(getattr(r, field) for r in records if getattr(r, field))
    return counts.most_common(1)[0][0] if counts else None


def _top_by_supplier(records: list) -> Optional[str]:
    supplier_changed = [r for r in records if r.supplier_changed]
    return _top_by(supplier_changed, "supplier_current") if supplier_changed else _top_by(records, "supplier_current")


def _slim_record(r) -> dict:
    return {
        "locationId": r.location_id,
        "materialGroup": r.material_group,
        "materialId": r.material_id,
        "supplier": r.supplier_current,
        "forecastQtyCurrent": r.forecast_qty_current,
        "forecastQtyPrevious": r.forecast_qty_previous,
        "qtyDelta": r.qty_delta,
        "rojCurrent": r.roj_current,
        "rojPrevious": r.roj_previous,
        "bodCurrent": r.bod_current,
        "bodPrevious": r.bod_previous,
        "ffCurrent": r.ff_current,
        "ffPrevious": r.ff_previous,
        "changeType": r.change_type,
        "riskLevel": r.risk_level,
        "qtyChanged": r.qty_changed,
        "supplierChanged": r.supplier_changed,
        "designChanged": r.design_changed,
        "rojChanged": r.roj_changed,
        "dcSite": r.dc_site,
        "country": r.country,
        "lastModifiedBy": r.last_modified_by,
        "lastModifiedDate": r.last_modified_date,
    }
