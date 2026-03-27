"""
Deterministic AI Insight Generator
Produces aiInsight, rootCause, and recommendedActions
grounded entirely in backend analytics metrics.
No LLM or random text — pure rule-based narrative.
"""
from typing import Optional


def generate_insights(
    total_records: int,
    matched_records: int,
    new_records: int,
    forecast_new: Optional[float],
    forecast_old: Optional[float],
    trend_delta: Optional[float],
    trend_direction: str,                  # increasing | decreasing | stable | volatile
    quantity_changed_count: int,
    supplier_changed_count: int,
    design_changed_count: int,
    roj_changed_count: int,
    highest_risk_level: str,               # Normal | High Demand Spike | Supplier Change Risk | Design Change Risk | Design + Supplier Change Risk
    top_impacted_location: Optional[str],
    top_impacted_supplier: Optional[str],
    top_impacted_material: Optional[str],
    top_impacted_material_group: Optional[str],
) -> dict:

    changed_count = quantity_changed_count + supplier_changed_count + design_changed_count + roj_changed_count
    unchanged_count = total_records - changed_count
    pct_changed = round((changed_count / total_records * 100), 1) if total_records > 0 else 0
    pct_stable = round((unchanged_count / total_records * 100), 1) if total_records > 0 else 0

    ai_insight = _build_insight(
        total_records, pct_changed, pct_stable, trend_direction, trend_delta,
        forecast_new, forecast_old, quantity_changed_count, supplier_changed_count,
        design_changed_count, roj_changed_count, highest_risk_level,
        top_impacted_location, top_impacted_material_group, new_records,
    )

    root_cause = _build_root_cause(
        trend_direction, trend_delta, quantity_changed_count, supplier_changed_count,
        design_changed_count, roj_changed_count, top_impacted_location,
        top_impacted_material, top_impacted_material_group, top_impacted_supplier,
        highest_risk_level,
    )

    recommended_actions = _build_actions(
        supplier_changed_count, design_changed_count, roj_changed_count,
        highest_risk_level, trend_direction, trend_delta, new_records,
        top_impacted_supplier, top_impacted_location,
    )

    return {
        "aiInsight": ai_insight,
        "rootCause": root_cause,
        "recommendedActions": recommended_actions,
    }


# ---------------------------------------------------------------------------
# Insight narrative
# ---------------------------------------------------------------------------

def _build_insight(
    total, pct_changed, pct_stable, trend_direction, trend_delta,
    forecast_new, forecast_old, qty_changed, supplier_changed,
    design_changed, roj_changed, risk_level,
    top_location, top_group, new_records,
) -> str:
    parts = []

    # Overall health
    if pct_stable >= 80:
        parts.append(f"Planning is largely stable with {pct_stable}% of records unchanged.")
    elif pct_changed >= 50:
        parts.append(f"Significant planning activity detected — {pct_changed}% of records changed this cycle.")
    else:
        parts.append(f"{pct_changed}% of records changed this cycle across {total} total records.")

    # Forecast trend
    if trend_direction == "increasing" and trend_delta is not None:
        parts.append(f"Forecast demand is trending upward with a net delta of +{trend_delta:,.0f} units.")
    elif trend_direction == "decreasing" and trend_delta is not None:
        parts.append(f"Forecast demand is trending downward with a net delta of {trend_delta:,.0f} units.")
    elif trend_direction == "volatile":
        parts.append("Forecast quantities are volatile — no consistent directional trend detected.")

    # Key drivers
    drivers = []
    if qty_changed > 0:
        drivers.append(f"{qty_changed} quantity adjustment{'s' if qty_changed > 1 else ''}")
    if supplier_changed > 0:
        drivers.append(f"{supplier_changed} supplier change{'s' if supplier_changed > 1 else ''}")
    if design_changed > 0:
        drivers.append(f"{design_changed} design change{'s' if design_changed > 1 else ''}")
    if roj_changed > 0:
        drivers.append(f"{roj_changed} schedule shift{'s' if roj_changed > 1 else ''}")
    if drivers:
        parts.append("Key drivers include: " + ", ".join(drivers) + ".")

    # Location focus
    if top_location:
        parts.append(f"Location {top_location} accounts for the highest concentration of changes.")

    # Material group
    if top_group:
        parts.append(f"Material group {top_group} is the most impacted equipment category.")

    # New records
    if new_records > 0:
        parts.append(f"{new_records} new material record{'s' if new_records > 1 else ''} appeared with no prior baseline.")

    # Risk
    if risk_level not in ("Normal", ""):
        parts.append(f"Risk level is elevated: {risk_level}.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Root cause
# ---------------------------------------------------------------------------

def _build_root_cause(
    trend_direction, trend_delta, qty_changed, supplier_changed,
    design_changed, roj_changed, top_location, top_material,
    top_group, top_supplier, risk_level,
) -> str:
    parts = []

    # Primary driver
    drivers = {
        "Quantity": qty_changed,
        "Supplier": supplier_changed,
        "Design": design_changed,
        "Schedule (ROJ)": roj_changed,
    }
    primary = max(drivers, key=lambda k: drivers[k])
    primary_count = drivers[primary]

    if primary_count > 0:
        parts.append(f"The primary driver of change is {primary} with {primary_count} affected record{'s' if primary_count > 1 else ''}.")

    # Location
    if top_location:
        parts.append(f"Location {top_location} is the main source of planning movement.")

    # Material
    if top_material:
        parts.append(f"Material {top_material} shows the highest individual impact.")
    elif top_group:
        parts.append(f"Equipment category {top_group} is driving the most change volume.")

    # Supplier
    if supplier_changed > 0 and top_supplier:
        parts.append(f"Supplier {top_supplier} is involved in the supplier-related changes.")

    # Design
    if design_changed > 0:
        parts.append("Design changes (BOD version or Form Factor) indicate potential specification updates that may affect procurement.")

    # ROJ
    if roj_changed > 0:
        parts.append("ROJ date shifts suggest schedule adjustments that may impact delivery timelines.")

    # Trend direction
    if trend_direction == "increasing" and trend_delta is not None and trend_delta > 0:
        parts.append(f"The upward forecast trend (+{trend_delta:,.0f}) may reflect demand growth or buffer additions.")
    elif trend_direction == "decreasing" and trend_delta is not None and trend_delta < 0:
        parts.append(f"The downward forecast trend ({trend_delta:,.0f}) may reflect demand reduction or plan corrections.")

    # Risk
    if risk_level not in ("Normal", ""):
        parts.append(f"Risk classification '{risk_level}' warrants immediate planner review.")

    return " ".join(parts) if parts else "No significant root cause identified. Planning appears stable."


# ---------------------------------------------------------------------------
# Recommended actions
# ---------------------------------------------------------------------------

def _build_actions(
    supplier_changed, design_changed, roj_changed,
    risk_level, trend_direction, trend_delta,
    new_records, top_supplier, top_location,
) -> list:
    actions = []

    if risk_level in ("Design Change Risk", "Design + Supplier Change Risk"):
        actions.append("Review BOD version and Form Factor changes with engineering team before procurement.")

    if risk_level in ("Supplier Change Risk", "Design + Supplier Change Risk"):
        supplier_note = f" for supplier {top_supplier}" if top_supplier else ""
        actions.append(f"Validate supplier transition plan{supplier_note} to avoid supply disruption.")

    if risk_level == "High Demand Spike":
        actions.append("Investigate demand spike — confirm whether increase is intentional or a data entry error.")

    if roj_changed > 0:
        actions.append("Review ROJ date shifts with supply chain team to assess delivery risk.")

    if trend_direction == "increasing" and trend_delta is not None and trend_delta > 0:
        actions.append("Confirm capacity availability to support increasing forecast demand.")

    if trend_direction == "decreasing" and trend_delta is not None and trend_delta < 0:
        actions.append("Review downward forecast trend — assess whether inventory buffers need adjustment.")

    if new_records > 0:
        actions.append(f"Establish baseline planning parameters for {new_records} new material record{'s' if new_records > 1 else ''}.")

    if top_location:
        actions.append(f"Prioritize planner review for location {top_location} — highest change concentration.")

    if not actions:
        actions.append("No immediate actions required. Continue monitoring planning cycle.")

    return actions
