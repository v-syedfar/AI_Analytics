"""
Response Builder
Transforms analytics output + MCP context + LLM insights
into a clean UI-ready dashboard JSON payload.
Replaces dashboard_builder.py with a cleaner, schema-aligned structure.
"""
from typing import Optional, List
from collections import Counter
from models import ComparedRecord, TrendRecord
from analytics import is_changed
from mcp.tools import (
    analytics_context_tool,
    risk_summary_tool,
    root_cause_driver_tool,
    recommendation_tool,
    alert_trigger_tool,
)
from ai_insight_engine import generate_insights


def build_response(
    compared: List[ComparedRecord],
    trends: List[TrendRecord],
    location_id: Optional[str] = None,
    material_group: Optional[str] = None,
    data_mode: str = "live",
    last_refreshed_at: Optional[str] = None,
) -> dict:
    """
    Full pipeline:
    1. Compute health score
    2. Call MCP tools
    3. Generate AI insights
    4. Shape UI-ready response
    """
    changed = [r for r in compared if is_changed(r)]
    total = len(compared)

    # Health score
    health_score = _compute_health_score(compared, changed)
    trend_direction = _classify_trend(trends, compared)

    # --- MCP Tool calls ---
    ctx = analytics_context_tool(compared, health_score, trend_direction)
    risk = risk_summary_tool(compared)
    root_cause = root_cause_driver_tool(compared)
    recommendations = recommendation_tool(ctx, risk, root_cause)
    alert = alert_trigger_tool(ctx, risk)

    # --- AI Insight (LLM or deterministic fallback) ---
    insights = generate_insights(ctx, risk, root_cause, recommendations)

    # --- Summaries ---
    dc_summary = _dc_summary(compared)
    mg_summary = _material_group_summary(compared)
    supplier_summary = _supplier_summary(changed)
    design_summary = _design_summary(changed)
    roj_summary = _roj_summary(changed)

    material_groups = sorted({r.material_group for r in compared if r.material_group})
    dc_count = len({r.location_id for r in compared if r.location_id})

    from datetime import datetime, timezone
    now = last_refreshed_at or datetime.now(timezone.utc).isoformat()

    return {
        # Mode metadata
        "dataMode": data_mode,
        "lastRefreshedAt": now,

        # Health
        "planningHealth": health_score,
        "status": _health_label(health_score),

        # Forecast
        "forecastNew": round(ctx.forecast_new, 2),
        "forecastOld": round(ctx.forecast_old, 2),
        "trendDirection": _trend_label(trend_direction),
        "trendDelta": round(ctx.trend_delta, 2),

        # Counts
        "datacenterCount": dc_count,
        "materialGroups": material_groups,
        "totalRecords": total,
        "changedRecordCount": len(changed),
        "unchangedRecordCount": total - len(changed),
        "newRecordCount": ctx.new_records,

        # Supplier
        "supplierSummary": {
            "changed": ctx.supplier_changed_count,
            "topSupplier": ctx.top_impacted_supplier,
            "details": supplier_summary,
        },

        # Design
        "designSummary": {
            "status": "Changed" if ctx.design_changed_count > 0 else "No Change",
            "bodChangedCount": sum(1 for r in changed if r.design_changed and r.bod_current != r.bod_previous),
            "formFactorChangedCount": sum(1 for r in changed if r.design_changed and r.ff_current != r.ff_previous),
            "details": design_summary,
        },

        # ROJ
        "rojSummary": {
            "status": "Changed" if ctx.roj_changed_count > 0 else "No Change",
            "changedCount": ctx.roj_changed_count,
            "details": roj_summary,
        },

        # Risk
        "riskSummary": {
            "level": _risk_label(risk.highest_risk_level),
            "highestRiskLevel": risk.highest_risk_level,
            "quantityChangedCount": ctx.quantity_changed_count,
            "supplierChangedCount": ctx.supplier_changed_count,
            "designChangedCount": ctx.design_changed_count,
            "rojChangedCount": ctx.roj_changed_count,
            "highRiskCount": risk.high_risk_count,
            "riskBreakdown": risk.risk_breakdown,
        },

        # AI
        "aiInsight": insights["aiInsight"],
        "rootCause": insights["rootCause"],
        "recommendedActions": insights["recommendedActions"],

        # Drivers
        "drivers": {
            "location": root_cause.driver_location,
            "supplier": root_cause.driver_supplier,
            "material": root_cause.driver_material,
            "materialGroup": root_cause.driver_material_group,
            "changeType": root_cause.primary_driver,
        },

        # Summaries for UI cards
        "datacenterSummary": dc_summary,
        "materialGroupSummary": mg_summary,

        # Detail records (slim)
        "detailRecords": [_slim_record(r) for r in changed],

        # Alerts
        "alerts": alert,

        # Filter context
        "filters": {
            "locationId": location_id,
            "materialGroup": material_group,
        },
    }


# ---------------------------------------------------------------------------
# Summary builders
# ---------------------------------------------------------------------------

def _dc_summary(records: List[ComparedRecord]) -> list:
    locs = {}
    for r in records:
        key = r.location_id
        if key not in locs:
            locs[key] = {"locationId": key, "dcSite": r.dc_site, "total": 0, "changed": 0}
        locs[key]["total"] += 1
        if is_changed(r):
            locs[key]["changed"] += 1
    return sorted(locs.values(), key=lambda x: -x["changed"])


def _material_group_summary(records: List[ComparedRecord]) -> list:
    groups = {}
    for r in records:
        key = r.material_group
        if key not in groups:
            groups[key] = {"materialGroup": key, "total": 0, "changed": 0,
                           "qtyChanged": 0, "designChanged": 0, "supplierChanged": 0}
        groups[key]["total"] += 1
        if is_changed(r):
            groups[key]["changed"] += 1
            if r.qty_changed: groups[key]["qtyChanged"] += 1
            if r.design_changed: groups[key]["designChanged"] += 1
            if r.supplier_changed: groups[key]["supplierChanged"] += 1
    return sorted(groups.values(), key=lambda x: -x["changed"])


def _supplier_summary(changed: List[ComparedRecord]) -> list:
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


def _design_summary(changed: List[ComparedRecord]) -> list:
    return [
        {
            "materialId": r.material_id,
            "locationId": r.location_id,
            "materialGroup": r.material_group,
            "bodPrevious": r.bod_previous,
            "bodCurrent": r.bod_current,
            "ffPrevious": r.ff_previous,
            "ffCurrent": r.ff_current,
            "riskLevel": r.risk_level,
        }
        for r in changed if r.design_changed
    ]


def _roj_summary(changed: List[ComparedRecord]) -> list:
    return [
        {
            "materialId": r.material_id,
            "locationId": r.location_id,
            "rojPrevious": r.roj_previous,
            "rojCurrent": r.roj_current,
            "rojReasonCode": r.roj_reason_code,
        }
        for r in changed if r.roj_changed
    ]


def _slim_record(r: ComparedRecord) -> dict:
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_health_score(records: List[ComparedRecord], changed: List[ComparedRecord]) -> int:
    total = len(records)
    if total == 0:
        return 100
    score = 100
    score -= int((len(changed) / total) * 40)
    risk_counts = Counter(r.risk_level for r in changed if r.risk_level != "Normal")
    highest = _highest_risk(risk_counts)
    if highest == "Design + Supplier Change Risk": score -= 25
    elif highest in ("Design Change Risk", "Supplier Change Risk"): score -= 15
    elif highest == "High Demand Spike": score -= 10
    design_count = sum(1 for r in changed if r.design_changed)
    supplier_count = sum(1 for r in changed if r.supplier_changed)
    score -= min(design_count * 2, 10)
    score -= min(supplier_count * 2, 10)
    return max(0, min(100, score))


def _classify_trend(trends: List[TrendRecord], compared: List[ComparedRecord]) -> str:
    if trends:
        directions = [t.qty_trend for t in trends]
        if all(d == "increasing" for d in directions): return "increasing"
        if all(d == "decreasing" for d in directions): return "decreasing"
        if all(d == "stable" for d in directions): return "stable"
        return "volatile"
    delta = sum((r.forecast_qty_current or 0) - (r.forecast_qty_previous or 0)
                for r in compared if r.forecast_qty_previous is not None)
    if delta > 0: return "increasing"
    if delta < 0: return "decreasing"
    return "stable"


def _highest_risk(risk_counts: Counter) -> str:
    for level in ["Design + Supplier Change Risk", "Design Change Risk",
                  "Supplier Change Risk", "High Demand Spike"]:
        if level in risk_counts:
            return level
    return "Normal"


def _health_label(score: int) -> str:
    if score >= 80: return "Healthy"
    if score >= 60: return "Stable"
    if score >= 40: return "At Risk"
    return "Critical"


def _risk_label(level: str) -> str:
    if "Design + Supplier" in level: return "CRITICAL"
    if "Design" in level or "Supplier" in level: return "HIGH"
    if "Spike" in level: return "MEDIUM"
    return "LOW"


def _trend_label(direction: str) -> str:
    return {"increasing": "Increase", "decreasing": "Decrease",
            "stable": "Stable", "volatile": "Volatile"}.get(direction, direction)
