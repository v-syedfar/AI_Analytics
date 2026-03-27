"""
Alert Rules Engine
Evaluates deterministic thresholds against analytics output
and returns structured alert payloads.
No LLM involved — pure rule-based signal detection.

Alert severity levels: info | warning | high | critical
"""
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class AlertPayload:
    should_trigger: bool
    severity: str                    # info | warning | high | critical
    trigger_type: str                # e.g. "health_drop", "demand_spike"
    message: str
    drivers: dict = field(default_factory=dict)
    recommended_action: str = ""


# ---------------------------------------------------------------------------
# Configurable thresholds (override via env vars if needed)
# ---------------------------------------------------------------------------
import os

HEALTH_DROP_THRESHOLD = int(os.environ.get("ALERT_HEALTH_THRESHOLD", "60"))
FORECAST_DELTA_PCT_THRESHOLD = float(os.environ.get("ALERT_FORECAST_DELTA_PCT", "20"))
ROJ_SHIFT_DAYS_THRESHOLD = int(os.environ.get("ALERT_ROJ_SHIFT_DAYS", "14"))
RECURRING_CHANGE_THRESHOLD = int(os.environ.get("ALERT_RECURRING_THRESHOLD", "3"))


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------

def evaluate_alerts(
    planning_health: int,
    status: str,
    forecast_new: float,
    forecast_old: float,
    trend_delta: float,
    trend_direction: str,
    quantity_changed_count: int,
    supplier_changed_count: int,
    design_changed_count: int,
    roj_changed_count: int,
    highest_risk_level: str,
    top_impacted_location: Optional[str],
    top_impacted_supplier: Optional[str],
    top_impacted_material_group: Optional[str],
    total_records: int,
    new_record_count: int = 0,
    snapshot_history: Optional[List[dict]] = None,
) -> AlertPayload:
    """
    Evaluates all alert rules and returns the highest severity alert.
    Returns a no-trigger payload if nothing crosses thresholds.
    """
    alerts: List[AlertPayload] = []

    # Rule 1: Planning health critical
    if planning_health < 40:
        alerts.append(AlertPayload(
            should_trigger=True,
            severity="critical",
            trigger_type="health_critical",
            message=f"Planning health is critically low at {planning_health}/100.",
            drivers={"location": top_impacted_location, "materialGroup": top_impacted_material_group},
            recommended_action="Immediate planner review required across all changed records.",
        ))
    elif planning_health < HEALTH_DROP_THRESHOLD:
        alerts.append(AlertPayload(
            should_trigger=True,
            severity="high",
            trigger_type="health_drop",
            message=f"Planning health dropped to {planning_health}/100, below threshold of {HEALTH_DROP_THRESHOLD}.",
            drivers={"location": top_impacted_location},
            recommended_action="Review high-risk records and address design or supplier changes.",
        ))

    # Rule 2: Demand spike
    if forecast_old and forecast_old > 0:
        delta_pct = abs(trend_delta / forecast_old * 100)
        if delta_pct >= FORECAST_DELTA_PCT_THRESHOLD and trend_direction == "increasing":
            alerts.append(AlertPayload(
                should_trigger=True,
                severity="high",
                trigger_type="demand_spike",
                message=f"Forecast increased by {delta_pct:.1f}% (+{trend_delta:,.0f} units). Demand spike detected.",
                drivers={"location": top_impacted_location, "materialGroup": top_impacted_material_group},
                recommended_action="Confirm capacity availability and validate demand plan with stakeholders.",
            ))

    # Rule 3: Design change risk
    if design_changed_count > 0:
        alerts.append(AlertPayload(
            should_trigger=True,
            severity="high",
            trigger_type="design_change",
            message=f"{design_changed_count} design change(s) detected (BOD/Form Factor). Procurement impact likely.",
            drivers={"materialGroup": top_impacted_material_group, "supplier": top_impacted_supplier},
            recommended_action="Review BOD version and Form Factor changes with engineering before procurement.",
        ))

    # Rule 4: Supplier change
    if supplier_changed_count > 0:
        alerts.append(AlertPayload(
            should_trigger=True,
            severity="warning",
            trigger_type="supplier_change",
            message=f"{supplier_changed_count} supplier change(s) detected.",
            drivers={"supplier": top_impacted_supplier, "location": top_impacted_location},
            recommended_action=f"Validate supplier transition plan for {top_impacted_supplier or 'affected suppliers'}.",
        ))

    # Rule 5: Combined risk (design + supplier)
    if highest_risk_level == "Design + Supplier Change Risk":
        alerts.append(AlertPayload(
            should_trigger=True,
            severity="critical",
            trigger_type="combined_risk",
            message="Combined design and supplier change risk detected. High procurement exposure.",
            drivers={"supplier": top_impacted_supplier, "materialGroup": top_impacted_material_group},
            recommended_action="Escalate to supply chain leadership for immediate review.",
        ))

    # Rule 6: New records in scope
    if new_record_count > 0:
        alerts.append(AlertPayload(
            should_trigger=True,
            severity="info",
            trigger_type="new_records",
            message=f"{new_record_count} new material record(s) introduced with no prior baseline.",
            drivers={"location": top_impacted_location},
            recommended_action="Establish planning parameters for new materials.",
        ))

    # Rule 7: Recurring trend from snapshot history
    if snapshot_history and len(snapshot_history) >= RECURRING_CHANGE_THRESHOLD:
        directions = [s.get("trendDirection", "") for s in snapshot_history[-RECURRING_CHANGE_THRESHOLD:]]
        if all(d in ("Increase", "increasing") for d in directions):
            alerts.append(AlertPayload(
                should_trigger=True,
                severity="warning",
                trigger_type="recurring_increase",
                message=f"Forecast has increased for {RECURRING_CHANGE_THRESHOLD} consecutive cycles.",
                drivers={"materialGroup": top_impacted_material_group},
                recommended_action="Review sustained demand growth — confirm buffer strategy.",
            ))

    # Return highest severity alert or no-trigger
    if not alerts:
        return AlertPayload(
            should_trigger=False,
            severity="info",
            trigger_type="none",
            message="No alert thresholds crossed. Planning cycle within normal parameters.",
        )

    priority = {"critical": 4, "high": 3, "warning": 2, "info": 1}
    return max(alerts, key=lambda a: priority.get(a.severity, 0))


def alert_to_dict(alert: AlertPayload) -> dict:
    return {
        "shouldTrigger": alert.should_trigger,
        "severity": alert.severity,
        "triggerType": alert.trigger_type,
        "message": alert.message,
        "drivers": alert.drivers,
        "recommendedAction": alert.recommended_action,
    }
