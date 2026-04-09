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

        # Contribution breakdown (percentage-based)
        "contributionBreakdown": _contribution_breakdown(changed),

        # Enhanced KPIs
        "kpis": _compute_kpis(compared, changed),

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

        # Detail records (slim) - Include ALL records, not just changed
        # This is needed for supplier queries and other analysis
        "detailRecords": [_slim_record(r) for r in compared],

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


def _contribution_breakdown(changed: List[ComparedRecord]) -> dict:
    """Percentage-based contribution breakdown by change driver."""
    total = len(changed) if changed else 1
    qty = sum(1 for r in changed if r.qty_changed)
    sup = sum(1 for r in changed if r.supplier_changed)
    des = sum(1 for r in changed if r.design_changed)
    roj = sum(1 for r in changed if r.roj_changed)
    return {
        "quantity": round(qty / total * 100, 1),
        "supplier": round(sup / total * 100, 1),
        "design": round(des / total * 100, 1),
        "schedule": round(roj / total * 100, 1),
        "quantityCount": qty,
        "supplierCount": sup,
        "designCount": des,
        "scheduleCount": roj,
    }


def _compute_kpis(records: List[ComparedRecord], changed: List[ComparedRecord]) -> dict:
    """Compute enhanced KPIs from record data."""
    total = len(records) if records else 1
    changed_count = len(changed)

    # Design change rate
    design_count = sum(1 for r in changed if r.design_changed)
    design_change_rate = round(design_count / total * 100, 1)

    # Supplier reliability (% of records with supplier date missing or supplier changed)
    supplier_issues = sum(1 for r in records if getattr(r, 'is_supplier_date_missing', False) or r.supplier_changed)
    supplier_reliability = round(100 - (supplier_issues / total * 100), 1)

    # Demand volatility (% of records with qty change)
    qty_changed = sum(1 for r in changed if r.qty_changed)
    demand_volatility = round(qty_changed / total * 100, 1)

    # Schedule stability (% of records WITHOUT roj change)
    roj_changed = sum(1 for r in changed if r.roj_changed)
    schedule_stability = round(100 - (roj_changed / total * 100), 1)

    # New demand ratio
    new_demand = sum(1 for r in records if getattr(r, 'is_new_demand', False))
    new_demand_ratio = round(new_demand / total * 100, 1)

    # Cancellation rate
    cancelled = sum(1 for r in records if getattr(r, 'is_cancelled', False))
    cancellation_rate = round(cancelled / total * 100, 1)

    # Risk concentration (% of changed records that are high risk)
    high_risk = sum(1 for r in changed if r.risk_level != "Normal")
    risk_concentration = round(high_risk / max(changed_count, 1) * 100, 1)

    return {
        "designChangeRate": design_change_rate,
        "supplierReliability": supplier_reliability,
        "demandVolatility": demand_volatility,
        "scheduleStability": schedule_stability,
        "newDemandRatio": new_demand_ratio,
        "cancellationRate": cancellation_rate,
        "riskConcentration": risk_concentration,
    }


# ============================================================================
# NEW: Comparison and Supplier Metrics Functions (Version 1.5)
# ============================================================================

def compute_comparison_metrics(records: List[ComparedRecord], entity1: str, entity2: str, scope_type: str) -> dict:
    """
    Compute side-by-side metrics for two entities.
    
    Args:
        records: List of all records
        entity1: First entity to compare
        entity2: Second entity to compare
        scope_type: "location" | "material_group" | "material_id"
    
    Returns:
        Dict with metrics for both entities
    """
    def filter_by_entity(recs, entity, scope_type):
        """Filter records by entity and scope type."""
        if scope_type == "location":
            return [r for r in recs if getattr(r, 'location_id', '').upper() == entity.upper()]
        elif scope_type == "material_group":
            return [r for r in recs if getattr(r, 'material_group', '').upper() == entity.upper()]
        elif scope_type == "material_id":
            return [r for r in recs if getattr(r, 'material_id', '').upper() == entity.upper()]
        return []
    
    def compute_entity_metrics(recs):
        """Compute metrics for a set of records."""
        changed = [r for r in recs if is_changed(r)]
        total = len(recs)
        change_rate = round(len(changed) / max(total, 1) * 100, 1)
        
        forecast_delta = sum(getattr(r, 'qty_delta', 0) for r in recs)
        design_changes = sum(1 for r in changed if getattr(r, 'design_changed', False))
        supplier_changes = sum(1 for r in changed if getattr(r, 'supplier_changed', False))
        roj_changes = sum(1 for r in changed if getattr(r, 'roj_changed', False))
        supplier_date_issues = sum(1 for r in changed if getattr(r, 'is_supplier_date_missing', False))
        risk_count = sum(1 for r in changed if getattr(r, 'risk_level', 'Normal') != 'Normal')
        
        return {
            "total_records": total,
            "changed_records": len(changed),
            "change_rate": change_rate,
            "forecast_delta": forecast_delta,
            "design_changes": design_changes,
            "supplier_changes": supplier_changes,
            "roj_changes": roj_changes,
            "supplier_date_issues": supplier_date_issues,
            "risk_count": risk_count,
        }
    
    records1 = filter_by_entity(records, entity1, scope_type)
    records2 = filter_by_entity(records, entity2, scope_type)
    
    return {
        "entity1": entity1,
        "entity2": entity2,
        "scope_type": scope_type,
        "metrics1": compute_entity_metrics(records1),
        "metrics2": compute_entity_metrics(records2),
    }


def get_suppliers_for_location(records: List[ComparedRecord], location: str) -> list:
    """
    Get list of unique suppliers for a location.
    
    Args:
        records: List of all records (should be normalized dicts with locationId and supplier keys)
        location: Location ID to filter by
    
    Returns:
        List of unique supplier IDs/names
    """
    import logging
    
    logging.info(f"get_suppliers_for_location called with location={location}, records count={len(records)}")
    
    if records and len(records) > 0:
        first = records[0]
        if isinstance(first, dict):
            logging.info(f"First record keys: {list(first.keys())}")
            logging.info(f"First record locationId: {first.get('locationId')}, supplier: {first.get('supplier')}")
    
    # Filter by location and extract unique suppliers
    # Assumes records are already normalized with locationId and supplier keys
    suppliers = set()
    matched_count = 0
    
    for record in records:
        if isinstance(record, dict):
            loc = (record.get("locationId") or "").upper()
            supplier = record.get("supplier")
        else:
            # Fallback for non-dict objects
            loc = (getattr(record, 'location_id', '') or "").upper()
            supplier = getattr(record, 'supplier', None)
        
        if loc == (location or "").upper():
            matched_count += 1
            if supplier:
                suppliers.add(supplier)
    
    logging.info(f"get_suppliers_for_location: location={location}, found {matched_count} records for this location")
    
    result = sorted(list(suppliers))
    
    logging.info(f"get_suppliers_for_location: found {len(result)} unique suppliers: {result}")
    
    return result


def compute_supplier_metrics(records: List[ComparedRecord], location: str, supplier: str) -> dict:
    """
    Compute metrics for a supplier at a specific location.
    
    Args:
        records: List of all records (can be dicts or ComparedRecord objects)
        location: Location ID
        supplier: Supplier ID/name
    
    Returns:
        Dict with supplier metrics
    """
    # Handle both dict and object formats
    location_records = []
    for r in records:
        if isinstance(r, dict):
            loc = (r.get("locationId") or r.get("LOCID") or r.get("location_id") or "").upper()
        else:
            loc = (getattr(r, 'location_id', '') or "").upper()
        
        if loc == (location or "").upper():
            location_records.append(r)
    
    supplier_records = []
    for r in location_records:
        if isinstance(r, dict):
            sup = (r.get("supplier") or r.get("LOCFR") or r.get("supplier_current") or "").upper()
        else:
            sup = (getattr(r, 'supplier_current', '') or getattr(r, 'supplier', '') or "").upper()
        
        if sup == (supplier or "").upper():
            supplier_records.append(r)
    
    changed = [r for r in supplier_records if _is_changed_record(r)]
    
    affected = len(supplier_records)
    changed_count = len(changed)
    
    # Compute forecast delta
    forecast_delta = 0
    for r in supplier_records:
        if isinstance(r, dict):
            delta = r.get("qtyDelta") or r.get("qty_delta") or r.get("FCST_Delta Qty") or 0
        else:
            delta = getattr(r, 'qty_delta', 0) or 0
        forecast_delta += delta
    
    # Design changes
    design_changes = 0
    for r in changed:
        if isinstance(r, dict):
            if r.get("designChanged") or r.get("design_changed"):
                design_changes += 1
        else:
            if getattr(r, 'design_changed', False):
                design_changes += 1
    
    # Availability issues
    availability_issues = 0
    for r in changed:
        if isinstance(r, dict):
            if r.get("isSupplierDateMissing") or r.get("Is_SupplierDateMissing"):
                availability_issues += 1
        else:
            if getattr(r, 'is_supplier_date_missing', False):
                availability_issues += 1
    
    # ROJ issues
    roj_issues = 0
    for r in changed:
        if isinstance(r, dict):
            if r.get("scheduleChanged") or r.get("roj_changed"):
                roj_issues += 1
        else:
            if getattr(r, 'roj_changed', False):
                roj_issues += 1
    
    # Risk count
    risk_count = 0
    for r in changed:
        if isinstance(r, dict):
            risk = r.get("riskLevel") or r.get("risk_level") or "Normal"
        else:
            risk = getattr(r, 'risk_level', 'Normal') or 'Normal'
        
        if risk != 'Normal':
            risk_count += 1
    
    return {
        "supplier": supplier,
        "location": location,
        "affected_records": affected,
        "changed_records": changed_count,
        "forecast_impact": forecast_delta,
        "design_changes": design_changes,
        "availability_issues": availability_issues,
        "roj_issues": roj_issues,
        "risk_count": risk_count,
    }


def _is_changed_record(r) -> bool:
    """Check if a record has any changes."""
    if isinstance(r, dict):
        return r.get("changed") or any([
            r.get("qtyChanged"), r.get("qty_changed"),
            r.get("supplierChanged"), r.get("supplier_changed"),
            r.get("designChanged"), r.get("design_changed"),
            r.get("scheduleChanged"), r.get("roj_changed"),
        ])
    else:
        return (getattr(r, 'qty_changed', False) or 
                getattr(r, 'supplier_changed', False) or 
                getattr(r, 'design_changed', False) or 
                getattr(r, 'roj_changed', False))


def analyze_supplier_behavior(records: List[ComparedRecord], location: str, supplier: str) -> dict:
    """
    Analyze supplier behavior for a location.
    
    Args:
        records: List of all records (can be dicts or ComparedRecord objects)
        location: Location ID
        supplier: Supplier ID/name
    
    Returns:
        Dict with supplier behavior analysis
    """
    # Handle both dict and object formats
    location_records = []
    for r in records:
        if isinstance(r, dict):
            loc = (r.get("locationId") or r.get("LOCID") or r.get("location_id") or "").upper()
        else:
            loc = (getattr(r, 'location_id', '') or "").upper()
        
        if loc == (location or "").upper():
            location_records.append(r)
    
    supplier_records = []
    for r in location_records:
        if isinstance(r, dict):
            sup = (r.get("supplier") or r.get("LOCFR") or r.get("supplier_current") or "").upper()
        else:
            sup = (getattr(r, 'supplier_current', '') or getattr(r, 'supplier', '') or "").upper()
        
        if sup == (supplier or "").upper():
            supplier_records.append(r)
    
    changed = [r for r in supplier_records if _is_changed_record(r)]
    
    # Design changes
    design_changes = 0
    for r in changed:
        if isinstance(r, dict):
            if r.get("designChanged") or r.get("design_changed"):
                design_changes += 1
        else:
            if getattr(r, 'design_changed', False):
                design_changes += 1
    
    design_pct = round(design_changes / max(len(changed), 1) * 100, 1)
    
    # BOD changes
    bod_changes = 0
    for r in changed:
        if isinstance(r, dict):
            bod_curr = r.get("bod") or r.get("ZCOIBODVER") or r.get("bod_current")
            bod_prev = r.get("bod") or r.get("ZCOIBODVER") or r.get("bod_previous")
        else:
            bod_curr = getattr(r, 'bod_current', None)
            bod_prev = getattr(r, 'bod_previous', None)
        
        if bod_curr != bod_prev:
            bod_changes += 1
    
    # Form Factor changes
    ff_changes = 0
    for r in changed:
        if isinstance(r, dict):
            ff_curr = r.get("formFactor") or r.get("ZCOIFORMFACT") or r.get("ff_current")
            ff_prev = r.get("formFactor") or r.get("ZCOIFORMFACT") or r.get("ff_previous")
        else:
            ff_curr = getattr(r, 'ff_current', None)
            ff_prev = getattr(r, 'ff_previous', None)
        
        if ff_curr != ff_prev:
            ff_changes += 1
    
    # Availability issues
    missing_supplier_date = 0
    changed_supplier_date = 0
    for r in changed:
        if isinstance(r, dict):
            if r.get("isSupplierDateMissing") or r.get("Is_SupplierDateMissing"):
                missing_supplier_date += 1
        else:
            if getattr(r, 'is_supplier_date_missing', False):
                missing_supplier_date += 1
    
    # ROJ behavior
    roj_changes = 0
    for r in changed:
        if isinstance(r, dict):
            if r.get("scheduleChanged") or r.get("roj_changed"):
                roj_changes += 1
        else:
            if getattr(r, 'roj_changed', False):
                roj_changes += 1
    
    roj_pct = round(roj_changes / max(len(changed), 1) * 100, 1)
    
    # Forecast behavior
    forecast_increases = 0
    forecast_decreases = 0
    total_forecast_delta = 0
    
    for r in supplier_records:
        if isinstance(r, dict):
            delta = r.get("qtyDelta") or r.get("qty_delta") or r.get("FCST_Delta Qty") or 0
        else:
            delta = getattr(r, 'qty_delta', 0) or 0
        
        total_forecast_delta += delta
        if delta > 0:
            forecast_increases += 1
        elif delta < 0:
            forecast_decreases += 1
    
    return {
        "supplier": supplier,
        "location": location,
        "design_changes": design_changes,
        "design_pct": design_pct,
        "bod_changes": bod_changes,
        "form_factor_changes": ff_changes,
        "missing_supplier_date": missing_supplier_date,
        "changed_supplier_date": changed_supplier_date,
        "roj_changes": roj_changes,
        "roj_pct": roj_pct,
        "forecast_increases": forecast_increases,
        "forecast_decreases": forecast_decreases,
        "total_forecast_delta": total_forecast_delta,
    }


def get_record_comparison(records: List[ComparedRecord], material_id: str, location_id: str = None) -> dict:
    """
    Get current vs previous comparison for a record using composite key.
    
    Args:
        records: List of all records
        material_id: Material ID
        location_id: Optional location ID (for composite key)
    
    Returns:
        Dict with current vs previous comparison
    """
    # Find record using composite key if location provided
    record = None
    for r in records:
        if getattr(r, 'material_id', '').upper() == material_id.upper():
            if location_id is None or getattr(r, 'location_id', '').upper() == location_id.upper():
                record = r
                break
    
    if not record:
        return {"error": f"Record not found for material {material_id}"}
    
    return {
        "material_id": material_id,
        "location_id": getattr(record, 'location_id', None),
        "material_group": getattr(record, 'material_group', None),
        "current": {
            "forecast": getattr(record, 'qty_current', None),
            "roj": getattr(record, 'roj_current', None),
            "supplier_date": getattr(record, 'supplier_date_current', None),
            "bod": getattr(record, 'bod_current', None),
            "form_factor": getattr(record, 'ff_current', None),
        },
        "previous": {
            "forecast": getattr(record, 'qty_previous', None),
            "roj": getattr(record, 'roj_previous', None),
            "supplier_date": getattr(record, 'supplier_date_previous', None),
            "bod": getattr(record, 'bod_previous', None),
            "form_factor": getattr(record, 'ff_previous', None),
        },
        "changes": {
            "forecast_delta": getattr(record, 'qty_delta', 0),
            "changed": is_changed(record),
            "risk_level": getattr(record, 'risk_level', 'Normal'),
            "is_new_demand": getattr(record, 'is_new_demand', False),
            "is_cancelled": getattr(record, 'is_cancelled', False),
            "is_supplier_date_missing": getattr(record, 'is_supplier_date_missing', False),
        },
    }
