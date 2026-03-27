"""
MCP Tool Layer
Structured, callable tool functions that expose analytics context
to the LLM reasoning layer. No raw rows are passed to the LLM.
Each tool returns a typed schema object.
"""
from typing import List, Optional
from collections import Counter
from models import ComparedRecord
from analytics import is_changed
from mcp.schemas import (
    AnalyticsContext, RiskSummary, RootCauseContext,
    RecommendationContext, NotificationPayload,
)


# ---------------------------------------------------------------------------
# Tool 1: analytics_context_tool
# ---------------------------------------------------------------------------

def analytics_context_tool(
    compared: List[ComparedRecord],
    planning_health: int,
    trend_direction: str,
) -> AnalyticsContext:
    """
    Compresses raw analytics output into a structured context object
    suitable for LLM prompt injection.
    """
    changed = [r for r in compared if is_changed(r)]
    total = len(compared)
    new_records = sum(1 for r in compared if r.forecast_qty_previous is None)

    forecast_new = sum(r.forecast_qty_current or 0 for r in compared)
    forecast_old = sum(r.forecast_qty_previous or 0 for r in compared if r.forecast_qty_previous)
    trend_delta = forecast_new - forecast_old

    qty_changed = sum(1 for r in changed if r.qty_changed)
    supplier_changed = sum(1 for r in changed if r.supplier_changed)
    design_changed = sum(1 for r in changed if r.design_changed)
    roj_changed = sum(1 for r in changed if r.roj_changed)

    risk_counts = Counter(r.risk_level for r in changed if r.risk_level != "Normal")
    highest_risk = _highest_risk(risk_counts)

    return AnalyticsContext(
        total_records=total,
        matched_records=total - new_records,
        new_records=new_records,
        forecast_new=round(forecast_new, 2),
        forecast_old=round(forecast_old, 2),
        trend_delta=round(trend_delta, 2),
        trend_direction=trend_direction,
        quantity_changed_count=qty_changed,
        supplier_changed_count=supplier_changed,
        design_changed_count=design_changed,
        roj_changed_count=roj_changed,
        top_impacted_location=_top_by(changed, "location_id"),
        top_impacted_supplier=_top_by_supplier(changed),
        top_impacted_material=_top_by(changed, "material_id"),
        top_impacted_material_group=_top_by(changed, "material_group"),
        risk_level=highest_risk,
        planning_health=planning_health,
    )


# ---------------------------------------------------------------------------
# Tool 2: risk_summary_tool
# ---------------------------------------------------------------------------

def risk_summary_tool(compared: List[ComparedRecord]) -> RiskSummary:
    """Returns structured risk breakdown for LLM and UI consumption."""
    changed = [r for r in compared if is_changed(r)]
    risk_counts = Counter(r.risk_level for r in changed if r.risk_level != "Normal")
    highest_risk = _highest_risk(risk_counts)

    drivers = []
    if any(r.design_changed for r in changed):
        drivers.append("design_changed")
    if any(r.supplier_changed for r in changed):
        drivers.append("supplier_changed")
    if any(r.qty_changed for r in changed):
        drivers.append("quantity_changed")
    if any(r.roj_changed for r in changed):
        drivers.append("schedule_changed")

    affected_ids = sorted({r.material_id for r in changed if r.risk_level != "Normal"})

    return RiskSummary(
        highest_risk_level=highest_risk,
        risk_breakdown=dict(risk_counts),
        high_risk_count=sum(risk_counts.values()),
        risk_drivers=drivers,
        affected_material_ids=affected_ids,
    )


# ---------------------------------------------------------------------------
# Tool 3: root_cause_driver_tool
# ---------------------------------------------------------------------------

def root_cause_driver_tool(compared: List[ComparedRecord]) -> RootCauseContext:
    """Identifies the primary driver of change and its source dimensions."""
    changed = [r for r in compared if is_changed(r)]

    drivers = {
        "quantity": sum(1 for r in changed if r.qty_changed),
        "supplier": sum(1 for r in changed if r.supplier_changed),
        "design": sum(1 for r in changed if r.design_changed),
        "schedule": sum(1 for r in changed if r.roj_changed),
    }
    primary = max(drivers, key=lambda k: drivers[k]) if any(drivers.values()) else "none"
    primary_count = drivers.get(primary, 0)

    is_stable = primary_count == 0

    change_parts = [k for k, v in drivers.items() if v > 0]
    change_type_label = " + ".join(p.capitalize() for p in change_parts) if change_parts else "Stable"

    return RootCauseContext(
        primary_driver=primary,
        primary_driver_count=primary_count,
        driver_location=_top_by(changed, "location_id"),
        driver_supplier=_top_by_supplier(changed),
        driver_material=_top_by(changed, "material_id"),
        driver_material_group=_top_by(changed, "material_group"),
        change_type_label=change_type_label,
        is_stable=is_stable,
    )


# ---------------------------------------------------------------------------
# Tool 4: recommendation_tool
# ---------------------------------------------------------------------------

def recommendation_tool(
    ctx: "AnalyticsContext",
    risk: "RiskSummary",
    root_cause: "RootCauseContext",
) -> RecommendationContext:
    """Deterministic candidate actions based on analytics signals."""
    actions = []

    if risk.highest_risk_level in ("Design Change Risk", "Design + Supplier Change Risk"):
        actions.append("Review BOD version and Form Factor changes with engineering before procurement.")

    if risk.highest_risk_level in ("Supplier Change Risk", "Design + Supplier Change Risk"):
        supplier_note = f" for {ctx.top_impacted_supplier}" if ctx.top_impacted_supplier else ""
        actions.append(f"Validate supplier transition plan{supplier_note} to avoid supply disruption.")

    if risk.highest_risk_level == "High Demand Spike":
        actions.append("Investigate demand spike — confirm whether increase is intentional or a data error.")

    if ctx.roj_changed_count > 0:
        actions.append("Review ROJ date shifts with supply chain team to assess delivery risk.")

    if ctx.trend_direction == "increasing" and ctx.trend_delta > 0:
        actions.append("Confirm capacity availability to support increasing forecast demand.")

    if ctx.trend_direction == "decreasing" and ctx.trend_delta < 0:
        actions.append("Review downward forecast trend — assess whether inventory buffers need adjustment.")

    if ctx.new_records > 0:
        actions.append(f"Establish baseline planning parameters for {ctx.new_records} new material record(s).")

    if ctx.top_impacted_location:
        actions.append(f"Prioritize planner review for location {ctx.top_impacted_location}.")

    if not actions:
        actions.append("No immediate actions required. Continue monitoring planning cycle.")

    return RecommendationContext(actions=actions)


# ---------------------------------------------------------------------------
# Tool 5: notification_tool (future-ready)
# ---------------------------------------------------------------------------

def notification_tool(
    ctx: "AnalyticsContext",
    risk: "RiskSummary",
    recommendations: "RecommendationContext",
) -> NotificationPayload:
    """
    Future-ready notification payload for Teams / Copilot / email alerts.
    Not called in current flow — reserved for auto-trigger integration.
    """
    severity = "low"
    if risk.highest_risk_level in ("Design Change Risk", "Design + Supplier Change Risk"):
        severity = "high"
    elif risk.highest_risk_level in ("Supplier Change Risk", "High Demand Spike"):
        severity = "medium"

    subject = f"Planning Alert: {risk.highest_risk_level} detected"
    body = (
        f"Planning cycle analysis complete. "
        f"{ctx.quantity_changed_count} quantity changes, "
        f"{ctx.supplier_changed_count} supplier changes, "
        f"{ctx.design_changed_count} design changes detected. "
        f"Health score: {ctx.planning_health}/100."
    )

    return NotificationPayload(
        severity=severity,
        subject=subject,
        body=body,
        target_location=ctx.top_impacted_location,
        target_supplier=ctx.top_impacted_supplier,
        recommended_actions=recommendations.actions,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _top_by(records: List[ComparedRecord], field: str) -> Optional[str]:
    if not records:
        return None
    counts = Counter(getattr(r, field) for r in records if getattr(r, field))
    return counts.most_common(1)[0][0] if counts else None


def _top_by_supplier(records: List[ComparedRecord]) -> Optional[str]:
    supplier_changed = [r for r in records if r.supplier_changed]
    return _top_by(supplier_changed, "supplier_current") or _top_by(records, "supplier_current")


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


# ---------------------------------------------------------------------------
# Tool 6: alert_trigger_tool
# ---------------------------------------------------------------------------

def alert_trigger_tool(
    ctx: "AnalyticsContext",
    risk: "RiskSummary",
    snapshot_history: Optional[List[dict]] = None,
) -> dict:
    """
    Evaluates deterministic alert thresholds and returns a structured
    alert payload. Uses alert_rules.py — no LLM involved.
    """
    from alert_rules import evaluate_alerts, alert_to_dict

    alert = evaluate_alerts(
        planning_health=ctx.planning_health,
        status="",
        forecast_new=ctx.forecast_new,
        forecast_old=ctx.forecast_old,
        trend_delta=ctx.trend_delta,
        trend_direction=ctx.trend_direction,
        quantity_changed_count=ctx.quantity_changed_count,
        supplier_changed_count=ctx.supplier_changed_count,
        design_changed_count=ctx.design_changed_count,
        roj_changed_count=ctx.roj_changed_count,
        highest_risk_level=risk.highest_risk_level,
        top_impacted_location=ctx.top_impacted_location,
        top_impacted_supplier=ctx.top_impacted_supplier,
        top_impacted_material_group=ctx.top_impacted_material_group,
        total_records=ctx.total_records,
        new_record_count=ctx.new_records,
        snapshot_history=snapshot_history,
    )
    return alert_to_dict(alert)
