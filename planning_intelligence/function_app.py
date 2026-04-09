import json
import logging
from typing import Optional, List
import azure.functions as func

from normalizer import normalize_rows
from filters import filter_records
from comparator import compare_records
from analytics import (
    build_summary,
    build_location_material_list,
    filter_by_supplier_design_change,
    changes_by_location,
    changes_by_material_group,
    change_driver_analysis,
    high_risk_records,
)
from trend_analyzer import (
    analyze_trends,
    build_trend_summary,
    get_consistently_increasing,
    get_recurring_changes,
    get_one_off_spikes,
    get_change_streaks,
)
from dashboard_builder import build_dashboard_response
from response_builder import build_response
from snapshot_store import load_snapshot, snapshot_exists, get_last_updated_time
from reasoning_engine import ReasoningEngine
from clarification_engine import ClarificationEngine
from enhanced_intent_parser import EnhancedIntentParser
from nlp_endpoint import handle_nlp_query, NLPEndpointHandler

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# ============================================================================
# DATA NORMALIZATION UTILITY
# ============================================================================
# Normalizes detailRecords from various formats to a consistent dict format
# that works with both .get() and getattr() access patterns

def _normalize_detail_records(records: list) -> list:
    """
    Normalize detailRecords to consistent format.
    
    Handles:
    - Raw CSV dicts with field names like LOCID, LOCFR, GSCFSCTQTY
    - ComparedRecord objects with attributes like location_id, supplier
    - Already-normalized dicts with keys like locationId, supplier
    
    Returns list of dicts with normalized keys:
    - locationId (from LOCID or location_id)
    - materialGroup (from GSCEQUIPCAT or material_group)
    - materialId (from PRDID or material_id)
    - supplier (from LOCFR or supplier_current)
    - forecastQty (from GSCFSCTQTY or forecast_qty_current)
    - roj (from GSCCONROJDATE or roj_current)
    - changed (from various change flags)
    - qtyChanged, supplierChanged, designChanged, scheduleChanged
    - qtyDelta, riskLevel, changeType
    """
    if not records:
        return []
    
    normalized = []
    for r in records:
        if isinstance(r, dict):
            # Already a dict - normalize keys
            norm = {
                # Location/Material/Supplier keys
                "locationId": r.get("locationId") or r.get("LOCID") or r.get("location_id") or "",
                "materialGroup": r.get("materialGroup") or r.get("GSCEQUIPCAT") or r.get("material_group") or "",
                "materialId": r.get("materialId") or r.get("PRDID") or r.get("material_id") or "",
                "supplier": r.get("supplier") or r.get("LOCFR") or r.get("supplier_current") or "",
                
                # Forecast/ROJ/BOD/FF
                "forecastQty": r.get("forecastQty") or r.get("GSCFSCTQTY") or r.get("forecast_qty_current"),
                "roj": r.get("roj") or r.get("GSCCONROJDATE") or r.get("roj_current"),
                "bod": r.get("bod") or r.get("ZCOIBODVER") or r.get("bod_current"),
                "formFactor": r.get("formFactor") or r.get("ZCOIFORMFACT") or r.get("ff_current"),
                
                # Change flags
                "changed": r.get("changed") or any([
                    r.get("qtyChanged"), r.get("qty_changed"),
                    r.get("supplierChanged"), r.get("supplier_changed"),
                    r.get("designChanged"), r.get("design_changed"),
                    r.get("scheduleChanged"), r.get("roj_changed"),
                ]),
                "qtyChanged": r.get("qtyChanged") or r.get("qty_changed") or False,
                "supplierChanged": r.get("supplierChanged") or r.get("supplier_changed") or False,
                "designChanged": r.get("designChanged") or r.get("design_changed") or False,
                "scheduleChanged": r.get("scheduleChanged") or r.get("roj_changed") or False,
                
                # Deltas and metrics
                "qtyDelta": r.get("qtyDelta") or r.get("qty_delta") or r.get("FCST_Delta Qty") or 0,
                "riskLevel": r.get("riskLevel") or r.get("risk_level") or "Normal",
                "changeType": r.get("changeType") or r.get("change_type") or "Unchanged",
                
                # Context fields
                "dcSite": r.get("dcSite") or r.get("ZCOIDCID") or r.get("dc_site"),
                "metro": r.get("metro") or r.get("ZCOIMETROID"),
                "country": r.get("country") or r.get("ZCOICOUNTRY"),
                "supplierDate": r.get("supplierDate") or r.get("GSCSUPLDATE") or r.get("supplier_date"),
                "isSupplierDateMissing": r.get("isSupplierDateMissing") or r.get("Is_SupplierDateMissing") or False,
            }
            normalized.append(norm)
        else:
            # ComparedRecord or similar object - convert to dict
            try:
                norm = {
                    "locationId": getattr(r, "location_id", "") or "",
                    "materialGroup": getattr(r, "material_group", "") or "",
                    "materialId": getattr(r, "material_id", "") or "",
                    "supplier": getattr(r, "supplier_current", "") or getattr(r, "supplier", "") or "",
                    "forecastQty": getattr(r, "forecast_qty_current", None),
                    "roj": getattr(r, "roj_current", None),
                    "bod": getattr(r, "bod_current", None),
                    "formFactor": getattr(r, "ff_current", None),
                    "changed": getattr(r, "qty_changed", False) or getattr(r, "supplier_changed", False) or getattr(r, "design_changed", False) or getattr(r, "roj_changed", False),
                    "qtyChanged": getattr(r, "qty_changed", False),
                    "supplierChanged": getattr(r, "supplier_changed", False),
                    "designChanged": getattr(r, "design_changed", False),
                    "scheduleChanged": getattr(r, "roj_changed", False),
                    "qtyDelta": getattr(r, "qty_delta", 0) or 0,
                    "riskLevel": getattr(r, "risk_level", "Normal") or "Normal",
                    "changeType": getattr(r, "change_type", "Unchanged") or "Unchanged",
                    "dcSite": getattr(r, "dc_site", None),
                    "metro": getattr(r, "metro", None),
                    "country": getattr(r, "country", None),
                    "supplierDate": getattr(r, "supplier_date", None),
                    "isSupplierDateMissing": getattr(r, "is_supplier_date_missing", False),
                }
                normalized.append(norm)
            except Exception as e:
                logging.warning(f"Failed to normalize record: {e}. Skipping.")
                continue
    
    return normalized


@app.route(route="planning-intelligence", methods=["POST"])
def planning_intelligence(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Planning Intelligence function triggered.")

    try:
        body = req.get_json()
    except ValueError:
        return _error("Invalid JSON body.", 400)

    query_type = body.get("query_type", "summary")
    current_rows: List[dict] = body.get("current_rows", [])
    previous_rows: List[dict] = body.get("previous_rows", [])
    snapshots_input: List[dict] = body.get("snapshots", [])
    location_id: Optional[str] = body.get("location_id")
    material_group: Optional[str] = body.get("material_group")
    min_streak: int = int(body.get("min_streak", 2))
    recurring_threshold: int = int(body.get("recurring_threshold", 3))

    # --- Trend queries (multi-snapshot path) ---
    if query_type in (
        "trend_analysis", "consistently_increasing",
        "recurring_changes", "one_off_spikes", "change_streaks",
    ):
        if not snapshots_input:
            return _error("'snapshots' array is required for trend queries.", 400)

        trends = analyze_trends(snapshots_input, location_id, material_group, recurring_threshold)

        if query_type == "trend_analysis":
            result = build_trend_summary(trends)
        elif query_type == "consistently_increasing":
            result = {"consistently_increasing": get_consistently_increasing(trends)}
        elif query_type == "recurring_changes":
            result = {"recurring_changes": get_recurring_changes(trends)}
        elif query_type == "one_off_spikes":
            result = {"one_off_spikes": get_one_off_spikes(trends)}
        elif query_type == "change_streaks":
            result = {"change_streaks": get_change_streaks(trends, min_streak)}

        return func.HttpResponse(
            json.dumps(result, default=str),
            mimetype="application/json",
            status_code=200,
        )

    # --- Two-snapshot queries (existing path) ---
    if not current_rows:
        return _error("'current_rows' is required.", 400)

    # Normalize
    current_records = normalize_rows(current_rows, is_current=True)
    previous_records = normalize_rows(previous_rows, is_current=False)

    # Filter
    current_filtered = filter_records(current_records, location_id, material_group)
    previous_filtered = filter_records(previous_records, location_id, material_group)

    # Compare
    compared = compare_records(current_filtered, previous_filtered)

    # Route query
    if query_type == "list_locations_and_groups":
        result = build_location_material_list(compared)

    elif query_type == "changed_records":
        summary = build_summary(compared)
        result = {
            "changed_record_count": summary["changed_record_count"],
            "changed_records": summary["changed_records"],
        }

    elif query_type == "changed_count":
        result = {"changed_record_count": build_summary(compared)["changed_record_count"]}

    elif query_type == "changed_material_ids":
        result = {"changed_material_ids": build_summary(compared)["changed_material_ids"]}

    elif query_type == "supplier_design_changes":
        result = {"supplier_design_changes": filter_by_supplier_design_change(compared)}

    # --- New analytical queries ---
    elif query_type == "changes_by_location":
        # Q3: Which locations have the most changes?
        result = changes_by_location(compared)

    elif query_type == "changes_by_material_group":
        # Q4: Which material groups have changes?
        result = changes_by_material_group(compared)

    elif query_type == "change_driver_analysis":
        # Q5: Are changes qty-, supplier-, or design-driven?
        result = change_driver_analysis(compared)

    elif query_type == "high_risk_records":
        # Q6: Which records are high risk?
        result = high_risk_records(compared)

    else:  # default: full summary covering all six questions
        result = build_summary(compared)

    return func.HttpResponse(
        json.dumps(result, default=str),
        mimetype="application/json",
        status_code=200,
    )


def _error(message: str, status: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"error": message}),
        mimetype="application/json",
        status_code=status,
    )


@app.route(route="planning_intelligence_nlp", methods=["POST"])
def planning_intelligence_nlp(req: func.HttpRequest) -> func.HttpResponse:
    """
    Natural Language Processing endpoint for Copilot UI.
    
    Accepts natural language questions and processes them through the NLP pipeline.
    
    Request body:
    {
        "question": "List suppliers for CYS20_F01C01",
        "detail_records": [...],
        "conversation_history": [...]  # Optional
    }
    
    Response:
    {
        "question": "List suppliers for CYS20_F01C01",
        "answer": "📊 CYS20_F01C01: 15 records total...",
        "queryType": "traceability",
        "scopeType": "location",
        "scopeValue": "CYS20_F01C01",
        "answerMode": "investigate",
        "confidence": 0.95,
        "conversationHistory": [...]
    }
    """
    logging.info("Planning Intelligence NLP endpoint triggered.")
    return handle_nlp_query(req)


@app.route(route="reasoning-query", methods=["POST"])
def reasoning_query(req: func.HttpRequest) -> func.HttpResponse:
    """
    Reasoning-based query endpoint using the new intelligence layer.
    
    Replaces template-based responses with dynamic, reasoning-driven outputs.
    Implements strict query → intent → execution flow with accurate computation.
    
    Request body:
    {
        "question": "Which suppliers at CYS20_F01C01 have design changes?",
        "detailRecords": [...],  // Optional: if provided, uses this data
        "context": {...}         // Optional: if provided, uses this context
    }
    
    Response:
    {
        "question": "...",
        "answer": "...",  // Dynamic, reasoning-driven response
        "intent": "list|compare|root_cause|...",
        "entities": {
            "location": "...",
            "supplier": "...",
            "material_id": "...",
            "material_group": "..."
        }
    }
    """
    logging.info("Reasoning query endpoint triggered.")
    
    try:
        body = req.get_json()
    except ValueError:
        return _error("Invalid JSON body.", 400)
    
    question = body.get("question", "").strip()
    if not question:
        return _error("question is required", 400)
    
    # Get detail records from request or context
    detail_records = body.get("detailRecords", [])
    if not detail_records:
        context = body.get("context", {})
        detail_records = context.get("detailRecords", [])
    
    # If still no records, try loading from snapshot
    if not detail_records:
        snap = load_snapshot()
        if snap:
            detail_records = snap.get("detailRecords", [])
    
    if not detail_records:
        return _error("No detail records available. Provide detailRecords or run daily-refresh.", 404)
    
    # Normalize records
    detail_records = _normalize_detail_records(detail_records)
    
    # Process query through reasoning engine
    try:
        engine = ReasoningEngine()
        answer = engine.process_query(question, detail_records)
        
        # Extract entities for response
        entities = {
            "location": engine.extractor.extract_location(question),
            "material_id": engine.extractor.extract_material_id(question),
            "material_group": engine.extractor.extract_material_group(question),
            "supplier": engine.extractor.extract_supplier(question),
            "comparison_pair": engine.extractor.extract_comparison_pair(question),
        }
        
        intent = engine.classifier.classify(question)
        
        response = {
            "question": question,
            "answer": answer,
            "intent": intent,
            "entities": entities,
            "dataMode": "reasoning",
            "timestamp": get_last_updated_time(),
        }
        
        return func.HttpResponse(
            json.dumps(response, default=str),
            mimetype="application/json",
            status_code=200,
        )
    
    except Exception as e:
        logging.error(f"Reasoning query failed: {e}", exc_info=True)
        return _error(f"Query processing failed: {str(e)}", 500)


@app.route(route="planning-dashboard", methods=["POST"])
def planning_dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """
    Dashboard endpoint — returns a fully shaped UI-ready JSON payload.
    Accepts same input as planning-intelligence but returns dashboard model.
    """
    logging.info("Planning Dashboard function triggered.")

    try:
        body = req.get_json()
    except ValueError:
        return _error("Invalid JSON body.", 400)

    current_rows: List[dict] = body.get("current_rows", [])
    previous_rows: List[dict] = body.get("previous_rows", [])
    snapshots_input: List[dict] = body.get("snapshots", [])
    location_id: Optional[str] = body.get("location_id")
    material_group: Optional[str] = body.get("material_group")
    recurring_threshold: int = int(body.get("recurring_threshold", 3))

    if not current_rows:
        return _error("'current_rows' is required.", 400)

    # Normalize + filter + compare
    current_records = normalize_rows(current_rows, is_current=True)
    previous_records = normalize_rows(previous_rows, is_current=False)
    current_filtered = filter_records(current_records, location_id, material_group)
    previous_filtered = filter_records(previous_records, location_id, material_group)
    compared = compare_records(current_filtered, previous_filtered)

    # Optional trend analysis
    trends = []
    if snapshots_input:
        trends = analyze_trends(snapshots_input, location_id, material_group, recurring_threshold)

    result = build_dashboard_response(compared, trends, location_id, material_group)

    return func.HttpResponse(
        json.dumps(result, default=str),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="planning-dashboard-v2", methods=["POST"])
def planning_dashboard_v2(req: func.HttpRequest) -> func.HttpResponse:
    """
    Blob-first AI dashboard endpoint.
    Reads from cached snapshot first; falls back to live blob reload.
    """
    logging.info("Planning Dashboard v2 triggered.")

    try:
        body = req.get_json()
    except ValueError:
        body = {}

    location_id: Optional[str] = body.get("location_id") if body else None
    material_group: Optional[str] = body.get("material_group") if body else None

    # Try cached snapshot first (fast path)
    snap = load_snapshot()
    if snap:
        if location_id or material_group:
            snap = _filter_snapshot(snap, location_id, material_group)
        return func.HttpResponse(
            json.dumps(snap, default=str),
            mimetype="application/json",
            status_code=200,
        )

    # No snapshot — load from blob directly
    logging.info("No snapshot found, loading from blob.")
    try:
        from blob_loader import load_current_previous_from_blob
        current_rows, previous_rows = load_current_previous_from_blob()
    except Exception as e:
        return _error(f"Blob load failed: {str(e)}", 500)

    current_records = normalize_rows(current_rows, is_current=True)
    previous_records = normalize_rows(previous_rows, is_current=False)
    current_filtered = filter_records(current_records, location_id, material_group)
    previous_filtered = filter_records(previous_records, location_id, material_group)
    compared = compare_records(current_filtered, previous_filtered)

    result = build_response(
        compared, [], location_id, material_group,
        data_mode="blob",
    )

    return func.HttpResponse(
        json.dumps(result, default=str),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="daily-refresh", methods=["POST"])
def daily_refresh(req: func.HttpRequest) -> func.HttpResponse:
    """
    Triggers daily refresh from Azure Blob Storage and saves a snapshot.
    """
    logging.info("Daily refresh triggered — loading from Blob Storage.")
    try:
        from run_daily_refresh import run_daily_refresh
        result = run_daily_refresh()
        return func.HttpResponse(
            json.dumps({
                "status": "ok",
                "lastRefreshedAt": result.get("lastRefreshedAt"),
                "totalRecords": result.get("totalRecords"),
                "changedRecordCount": result.get("changedRecordCount"),
                "planningHealth": result.get("planningHealth"),
            }, default=str),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        return _error(f"Daily refresh failed: {str(e)}", 500)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_scope(question: str) -> tuple:
    """
    Extract scope from question. Enhanced for comparison queries and material IDs.
    
    Returns: (scope_type, scope_value) or (scope_type, [scope_value1, scope_value2]) for comparisons
    
    scope_type: "location" | "supplier" | "material_group" | "material_id" | "risk_type" | None
    scope_value: extracted entity name or ID (or list for comparisons)
    """
    import re
    q = question.lower()
    
    # Check for comparison patterns first (e.g., "LOC001 vs LOC002")
    # Enhanced to match location IDs like CMH02_F01C01, AVC11_F01C01, etc.
    comparison_patterns = [
        r'(LOC\d+|location\s+[\w\-]+|[A-Z]+\d+_[A-Z0-9]+)\s+(?:vs|versus|compared?\s+to)\s+(LOC\d+|location\s+[\w\-]+|[A-Z]+\d+_[A-Z0-9]+)',
        r'(PUMP|VALVE|[\w\s]+)\s+(?:vs|versus|compared?\s+to)\s+(PUMP|VALVE|[\w\s]+)',
        r'(MAT\d+|material\s+[\w\-]+|C\d{8}-\d{3})\s+(?:vs|versus|compared?\s+to)\s+(MAT\d+|material\s+[\w\-]+|C\d{8}-\d{3})',
    ]
    
    for pattern in comparison_patterns:
        match = re.search(pattern, q, re.IGNORECASE)
        if match:
            entity1 = match.group(1).upper()
            entity2 = match.group(2).upper()
            # Determine scope type from entities
            if 'LOC' in entity1 or 'LOCATION' in entity1 or '_' in entity1:
                return ("location", [entity1, entity2])
            elif 'MAT' in entity1 or 'MATERIAL' in entity1 or 'C' in entity1[:1]:
                return ("material_id", [entity1, entity2])
            else:
                return ("material_group", [entity1, entity2])
    
    # Material ID patterns - FIRST (before location) to catch C00000560-001 format
    mat_match = re.search(r'\b(C\d{8}-\d{3}|material\s+([\w\-]+)|MAT[\w\-]*)\b', q, re.IGNORECASE)
    if mat_match:
        material = mat_match.group(1).upper() if mat_match.lastindex == 1 else (mat_match.group(2).upper() if mat_match.lastindex and mat_match.group(2) else mat_match.group(0).upper())
        if material and material not in ['MATERIAL']:
            return ("material_id", material)
    
    # Location patterns - enhanced to match various formats like LOC001, AVC11_F01C01, CMH02_F01C01, etc.
    # Matches: LOC001, location LOC001, location AVC11_F01C01, at AVC11_F01C01, etc.
    loc_patterns = [
        r'\blocation\s+([\w\-]+)',  # "location AVC11_F01C01"
        r'\bat\s+([\w\-]+)',         # "at AVC11_F01C01"
        r'\b(LOC\d+|[A-Z]+\d+_[A-Z0-9]+)\b',  # "LOC001" or "AVC11_F01C01" or "CMH02_F01C01"
    ]
    
    for pattern in loc_patterns:
        loc_match = re.search(pattern, q, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).upper() if loc_match.lastindex else loc_match.group(0).upper()
            # Verify it looks like a location ID (not a common word)
            if location not in ['FOR', 'THE', 'AND', 'OR', 'AT', 'IN', 'TO', 'FROM']:
                return ("location", location)
    
    # Supplier patterns
    sup_match = re.search(r'\b(supplier\s+([\w\-]+)|SUP[\w\-]*)\b', q, re.IGNORECASE)
    if sup_match:
        supplier = sup_match.group(1).upper() if sup_match.lastindex and sup_match.group(2) else sup_match.group(0).upper()
        return ("supplier", supplier)
    
    # Material group patterns (equipment categories like UPS, MVSXRM, etc.)
    mg_match = re.search(r'\b(material\s+group\s+([\w\-]+)|category\s+([\w\-]+)|in\s+([\w\-]+)|PUMP|VALVE|UPS|MVSXRM|LVS|EPMS|ATS|BAS|GEN|BUS|MVS|AHU|HAC|ACC|CRAH|CDU|AHF|TCP|PDU|CT|EHOUSE|WCC)\b', q, re.IGNORECASE)
    if mg_match:
        mg = mg_match.group(1).upper() if mg_match.lastindex == 1 else (mg_match.group(2).upper() if mg_match.lastindex and mg_match.group(2) else (mg_match.group(3).upper() if mg_match.lastindex and mg_match.group(3) else (mg_match.group(4).upper() if mg_match.lastindex and mg_match.group(4) else mg_match.group(0).upper())))
        if mg and mg not in ['MATERIAL', 'GROUP', 'CATEGORY', 'IN']:
            return ("material_group", mg)
    
    # Risk type patterns
    if any(w in q for w in ["high risk", "low risk", "critical", "normal"]):
        return ("risk_type", None)
    
    return (None, None)


def _determine_answer_mode(query_type: str, scope_type: str) -> str:
    """
    Determine if Summary or Investigate mode. Enhanced for comparison and supplier queries.
    
    Returns: "summary" | "investigate"
    """
    # Always investigate for these query types
    if query_type in ["comparison", "traceability", "supplier_by_location", "record_detail", "design_filter"]:
        return "investigate"
    
    # Investigate if scoped
    if query_type in ["root_cause", "why_not"] and scope_type:
        return "investigate"
    
    # Investigate if scoped and not summary/provenance
    if scope_type and query_type not in ["summary", "provenance"]:
        return "investigate"
    
    return "summary"


def _compute_scoped_metrics(detail_records: list, scope_type: str, scope_value: str) -> dict:
    """
    Filter detailRecords to scope and recompute metrics.
    
    Returns: {
        "filteredRecordsCount": int,
        "scopedContributionBreakdown": {...},
        "scopedDrivers": {...},
        "topContributingRecords": [...],
        "scopedMetrics": {...}
    }
    """
    # NORMALIZE: Ensure consistent data format
    detail_records = _normalize_detail_records(detail_records)
    
    # Filter records to scope
    if scope_type == "location":
        filtered = [r for r in detail_records if (r.get("locationId") or "").upper() == (scope_value or "").upper()]
    elif scope_type == "supplier":
        filtered = [r for r in detail_records if (r.get("supplier") or "").upper() == (scope_value or "").upper()]
    elif scope_type == "material_group":
        filtered = [r for r in detail_records if (r.get("materialGroup") or "").upper() == (scope_value or "").upper()]
    elif scope_type == "material_id":
        filtered = [r for r in detail_records if (r.get("materialId") or "").upper() == (scope_value or "").upper()]
    elif scope_type == "risk_type":
        filtered = [r for r in detail_records if r.get("riskLevel") == scope_value]
    else:
        filtered = detail_records
    
    # Recompute metrics
    changed_count = sum(1 for r in filtered if r.get("changed"))
    total_count = len(filtered)
    change_rate = round(changed_count / max(total_count, 1) * 100, 1)
    
    # Contribution breakdown
    qty_changed = sum(1 for r in filtered if r.get("qtyChanged"))
    supplier_changed = sum(1 for r in filtered if r.get("supplierChanged"))
    design_changed = sum(1 for r in filtered if r.get("designChanged"))
    schedule_changed = sum(1 for r in filtered if r.get("scheduleChanged"))
    
    contribution = {
        "quantity": round(qty_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
        "supplier": round(supplier_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
        "design": round(design_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
        "schedule": round(schedule_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
    }
    
    # Top drivers
    drivers = {
        "primary": max(
            [("quantity", qty_changed), ("supplier", supplier_changed), 
             ("design", design_changed), ("schedule", schedule_changed)],
            key=lambda x: x[1]
        )[0] if changed_count > 0 else "none",
        "changedCount": changed_count,
        "totalCount": total_count,
    }
    
    # Top contributing records
    top_records = sorted(
        filtered,
        key=lambda r: abs(r.get("qtyDelta", 0)),
        reverse=True
    )[:5]
    
    return {
        "filteredRecordsCount": total_count,
        "scopedContributionBreakdown": contribution,
        "scopedDrivers": drivers,
        "topContributingRecords": top_records,
        "scopedMetrics": {
            "changedCount": changed_count,
            "changeRate": change_rate,
            "totalRecords": total_count,
        }
    }


def _generate_comparison_answer(question: str, ctx: dict) -> str:
    """Generate comparison answer with side-by-side metrics."""
    import re
    
    # Extract two entities
    entities = re.findall(r'\b(LOC\d+|SUP\d+|MAT\d+)\b', question, re.IGNORECASE)
    if len(entities) < 2:
        return "Could not extract two entities to compare."
    
    entity_a, entity_b = entities[0].upper(), entities[1].upper()
    detail_records = ctx.get("detailRecords", [])
    
    # Determine scope type
    if entity_a.startswith("LOC"):
        scope_type = "location"
    elif entity_a.startswith("SUP"):
        scope_type = "supplier"
    else:
        scope_type = "material_id"
    
    # Compute metrics for each
    metrics_a = _compute_scoped_metrics(detail_records, scope_type, entity_a)
    metrics_b = _compute_scoped_metrics(detail_records, scope_type, entity_b)
    
    # Format comparison
    return (
        f"📊 Comparison: {entity_a} vs {entity_b}\n\n"
        f"{entity_a}: {metrics_a['scopedMetrics']['changedCount']}/{metrics_a['filteredRecordsCount']} changed "
        f"({metrics_a['scopedMetrics']['changeRate']}%). "
        f"Primary driver: {metrics_a['scopedDrivers']['primary']}\n"
        f"{entity_b}: {metrics_b['scopedMetrics']['changedCount']}/{metrics_b['filteredRecordsCount']} changed "
        f"({metrics_b['scopedMetrics']['changeRate']}%). "
        f"Primary driver: {metrics_b['scopedDrivers']['primary']}\n\n"
        f"→ {entity_a if metrics_a['scopedMetrics']['changedCount'] > metrics_b['scopedMetrics']['changedCount'] else entity_b} "
        f"has more changes."
    )


def _generate_root_cause_answer(question: str, ctx: dict, scope_type: str, scope_value: str, scoped_metrics: dict) -> str:
    """Generate root cause answer for specific entity.
    
    Task 19: Enhanced answer formatting for root cause queries - what changed, why risky, action.
    Task 20: Ask for clarification when scope is missing.
    """
    # Handle queries without scope (e.g., "Why is planning health critical?")
    if not scope_value:
        return (
            "To analyze why planning health is critical, I need more context:\n\n"
            "Please specify:\n"
            "  • Location ID (e.g., CYS20_F01C01, DSM18_F01C01)\n"
            "  • Or Equipment Category (e.g., UPS, MVSXRM)\n"
            "  • Or ask: 'Why is planning health at 37/100?'\n\n"
            "💡 Examples:\n"
            "  • 'Why is CYS20_F01C01 risky?'\n"
            "  • 'Why is UPS category critical?'\n"
            "  • 'What is driving the risk?'"
        )
    
    metrics = scoped_metrics or _compute_scoped_metrics(
        ctx.get("detailRecords", []), scope_type, scope_value
    )
    
    what_changed = metrics['scopedDrivers']['primary']
    change_rate = metrics['scopedMetrics']['changeRate']
    changed_count = metrics['scopedMetrics']['changedCount']
    total_count = metrics['filteredRecordsCount']
    actions = ctx.get("recommendedActions", ["Monitor situation"])
    action = actions[0] if actions else "Monitor situation"
    
    # Enhanced formatting (Task 19)
    lines = [f"📊 Root Cause Analysis: {scope_value}\n"]
    lines.append(f"What changed:")
    lines.append(f"  • Primary driver: {what_changed}")
    lines.append(f"  • Records affected: {changed_count}/{total_count} ({change_rate:.1f}%)\n")
    lines.append(f"Why it's risky:")
    lines.append(f"  • High change rate ({change_rate:.1f}%) indicates instability")
    lines.append(f"  • {changed_count} records changed in this cycle\n")
    lines.append(f"Recommended action:")
    lines.append(f"  • {action}")
    
    return "\n".join(lines)


def _generate_why_not_answer(question: str, ctx: dict, scope_type: str, scope_value: str, scoped_metrics: dict) -> str:
    """Generate why-not answer for stable entity.
    
    Task 19: Enhanced answer formatting for why-not queries - stability explanation.
    """
    if not scope_value:
        return "Could not identify specific entity in question."
    
    metrics = scoped_metrics or _compute_scoped_metrics(
        ctx.get("detailRecords", []), scope_type, scope_value
    )
    
    changed_count = metrics['scopedMetrics']['changedCount']
    total_count = metrics['filteredRecordsCount']
    change_rate = metrics['scopedMetrics']['changeRate']
    
    # Enhanced formatting (Task 19)
    lines = [f"📊 Stability Analysis: {scope_value}\n"]
    
    if changed_count == 0:
        lines.append(f"Status: Stable")
        lines.append(f"  • No records changed this cycle")
        lines.append(f"  • All {total_count} records remain unchanged\n")
        lines.append(f"Why it's not risky:")
        lines.append(f"  • Zero change rate indicates complete stability")
        lines.append(f"  • No new risks introduced")
    else:
        lines.append(f"Status: {'Stable' if change_rate < 10 else 'Moderate' if change_rate < 25 else 'Active'}")
        lines.append(f"  • {changed_count}/{total_count} records changed ({change_rate:.1f}%)\n")
        lines.append(f"Why it's {'not risky' if change_rate < 10 else 'below risk threshold'}:")
        if change_rate < 10:
            lines.append(f"  • Low change rate ({change_rate:.1f}%) is within normal parameters")
        else:
            lines.append(f"  • Change rate ({change_rate:.1f}%) is below the risk threshold")
        lines.append(f"  • Situation is under control")
    
    return "\n".join(lines)


def _generate_traceability_answer(question: str, ctx: dict, scoped_metrics: dict) -> str:
    """Generate traceability answer with top contributing records.
    
    Task 19: Enhanced answer formatting for traceability queries - top contributing records.
    """
    records = scoped_metrics.get("topContributingRecords", []) if scoped_metrics else []
    if not records:
        return "No contributing records found."
    
    lines = [f"📊 Top {len(records)} Contributing Records (by forecast delta):\n"]
    lines.append(f"{'Location':<12} {'Material Group':<18} {'Material ID':<12} {'Δ Qty':<12} {'Type':<15} {'Risk':<10}")
    lines.append("-" * 80)
    
    for r in records:
        delta = r.get("qtyDelta", 0)
        delta_str = f"{delta:+,.0f}"
        loc = r.get('locationId', '?')[:11]
        mg = r.get('materialGroup', '?')[:17]
        mid = r.get('materialId', '?')[:11]
        ctype = r.get('changeType', '?')[:14]
        risk = r.get('riskLevel', '?')[:9]
        lines.append(f"{loc:<12} {mg:<18} {mid:<12} {delta_str:<12} {ctype:<15} {risk:<10}")
    
    return "\n".join(lines)

def _generate_comparison_answer(question: str, ctx: dict, scope_type: str, scope_values: list) -> str:
    """Generate comparison answer with side-by-side metrics for two entities.
    
    Task 19: Enhanced answer formatting for comparison queries - side-by-side metrics.
    """
    if not isinstance(scope_values, list) or len(scope_values) < 2:
        return "Could not extract two entities to compare. Please specify both entities clearly."
    
    entity1, entity2 = scope_values[0], scope_values[1]
    detail_records = ctx.get("detailRecords", [])
    
    # NORMALIZE: Ensure consistent data format
    detail_records = _normalize_detail_records(detail_records)
    
    # Filter records for each entity
    def filter_by_entity(records, entity, scope_type):
        if scope_type == "location":
            return [r for r in records if (r.get("locationId", "") or "").upper() == (entity or "").upper()]
        elif scope_type == "material_group":
            return [r for r in records if (r.get("materialGroup", "") or "").upper() == (entity or "").upper()]
        elif scope_type == "material_id":
            return [r for r in records if (r.get("materialId", "") or "").upper() == (entity or "").upper()]
        return []
    
    records1 = filter_by_entity(detail_records, entity1, scope_type)
    records2 = filter_by_entity(detail_records, entity2, scope_type)
    
    # Compute metrics for each
    def compute_metrics(records):
        changed = sum(1 for r in records if r.get("changed"))
        total = len(records)
        change_rate = (changed / total * 100) if total > 0 else 0
        forecast_delta = sum(r.get("qtyDelta", 0) for r in records)
        design_changes = sum(1 for r in records if "design" in str(r.get("changeType", "")).lower())
        supplier_changes = sum(1 for r in records if "supplier" in str(r.get("changeType", "")).lower())
        risk_count = sum(1 for r in records if r.get("riskLevel") in ["High", "Critical"])
        
        return {
            "total": total,
            "changed": changed,
            "change_rate": change_rate,
            "forecast_delta": forecast_delta,
            "design_changes": design_changes,
            "supplier_changes": supplier_changes,
            "risk_count": risk_count,
        }
    
    metrics1 = compute_metrics(records1)
    metrics2 = compute_metrics(records2)
    
    # Format side-by-side comparison (Task 19)
    lines = [f"📊 Comparison: {entity1} vs {entity2}\n"]
    lines.append(f"{'Metric':<25} {'':>1} {entity1:<15} {'':>1} {entity2:<15}")
    lines.append("-" * 60)
    lines.append(f"{'Total records':<25} {'':>1} {metrics1['total']:<15} {'':>1} {metrics2['total']:<15}")
    lines.append(f"{'Changed':<25} {'':>1} {metrics1['changed']} ({metrics1['change_rate']:.1f}%){'':<5} {metrics2['changed']} ({metrics2['change_rate']:.1f}%)")
    lines.append(f"{'Forecast delta':<25} {'':>1} {metrics1['forecast_delta']:+,.0f}{'':<10} {metrics2['forecast_delta']:+,.0f}")
    lines.append(f"{'Design changes':<25} {'':>1} {metrics1['design_changes']:<15} {'':>1} {metrics2['design_changes']:<15}")
    lines.append(f"{'Supplier changes':<25} {'':>1} {metrics1['supplier_changes']:<15} {'':>1} {metrics2['supplier_changes']:<15}")
    lines.append(f"{'Risk count':<25} {'':>1} {metrics1['risk_count']:<15} {'':>1} {metrics2['risk_count']:<15}")
    lines.append("")
    
    # Comparison conclusion
    if metrics1['changed'] > metrics2['changed']:
        lines.append(f"→ {entity1} has more changes ({metrics1['changed']} vs {metrics2['changed']})")
    elif metrics2['changed'] > metrics1['changed']:
        lines.append(f"→ {entity2} has more changes ({metrics2['changed']} vs {metrics1['changed']})")
    else:
        lines.append(f"→ Both have similar change counts ({metrics1['changed']} records)")
    
    return "\n".join(lines)

def _generate_supplier_by_location_answer(question: str, ctx: dict, scope_type: str, scope_value: str, detail_level: str = "summary") -> str:
    """Generate supplier listing and analysis for a location.
    
    Task 19: Enhanced answer formatting for supplier queries - supplier list with metrics.
    Task 20: Ask for clarification when location is missing.
    
    detail_level: "summary" (basic), "detailed" (with metrics), "full" (all details)
    """
    if scope_type != "location":
        return (
            "To analyze suppliers, I need more context:\n\n"
            "Please specify:\n"
            "  • Location ID (e.g., CYS20_F01C01, DSM18_F01C01)\n"
            "  • Or ask: 'List suppliers for [location]'\n\n"
            "💡 Examples:\n"
            "  • 'List suppliers for CYS20_F01C01'\n"
            "  • 'Which suppliers at CYS20_F01C01 have design changes?'\n"
            "  • 'Which locations have the most changes?'"
        )
    
    location = scope_value
    detail_records = ctx.get("detailRecords", [])
    
    # NORMALIZE: Ensure consistent data format
    detail_records = _normalize_detail_records(detail_records)
    
    # Import helper functions from response_builder
    from response_builder import get_suppliers_for_location, compute_supplier_metrics, analyze_supplier_behavior
    
    # Get suppliers for this location
    suppliers = get_suppliers_for_location(detail_records, location)
    
    if not suppliers:
        return f"No supplier information found for location {location}."
    
    # Compute metrics for each supplier (Task 19)
    lines = [f"📊 Suppliers at {location}:\n"]
    
    if detail_level == "summary":
        lines.append(f"{'Supplier':<20} {'Records':<10} {'Changed':<10} {'Risk':<8}")
        lines.append("-" * 50)
        for supplier in suppliers:
            metrics = compute_supplier_metrics(detail_records, location, supplier)
            sup_name = supplier[:19]
            records = metrics['affected_records']
            changed = metrics['changed_records']
            risk = metrics['risk_count']
            lines.append(f"{sup_name:<20} {records:<10} {changed:<10} {risk:<8}")
    
    elif detail_level == "detailed":
        lines.append(f"{'Supplier':<20} {'Records':<10} {'Changed':<10} {'Forecast':<12} {'Design':<10} {'Risk':<8}")
        lines.append("-" * 70)
        for supplier in suppliers:
            metrics = compute_supplier_metrics(detail_records, location, supplier)
            behavior = analyze_supplier_behavior(detail_records, location, supplier)
            sup_name = supplier[:19]
            records = metrics['affected_records']
            changed = metrics['changed_records']
            forecast = f"{metrics['forecast_impact']:+,.0f}"
            design = f"{metrics['design_changes']}"
            risk = metrics['risk_count']
            lines.append(f"{sup_name:<20} {records:<10} {changed:<10} {forecast:<12} {design:<10} {risk:<8}")
    
    elif detail_level == "full":
        for idx, supplier in enumerate(suppliers[:10], 1):
            metrics = compute_supplier_metrics(detail_records, location, supplier)
            behavior = analyze_supplier_behavior(detail_records, location, supplier)
            lines.append(f"\n{idx}. Supplier: {supplier}")
            lines.append(f"   Records: {metrics['affected_records']}")
            lines.append(f"   Changed: {metrics['changed_records']}")
            lines.append(f"   Forecast impact: {metrics['forecast_impact']:+,.0f}")
            lines.append(f"   Design changes: {metrics['design_changes']} ({behavior['design_pct']}%)")
            lines.append(f"   Availability issues: {metrics['availability_issues']}")
            lines.append(f"   ROJ issues: {metrics['roj_issues']} ({behavior['roj_pct']}%)")
            lines.append(f"   Risk count: {metrics['risk_count']}")
    
    lines.append(f"\n💡 Tip: Ask for more details like 'Show materials for [supplier]' or 'Which materials have design changes?'")
    
    return "\n".join(lines)

def _generate_record_comparison_answer(question: str, ctx: dict, scope_type: str, scope_value: str) -> str:
    """Generate record-level comparison (current vs previous).
    
    Task 19: Enhanced answer formatting for record comparison queries - current vs previous.
    Task 20: Ask for clarification when location context is missing.
    """
    detail_records = ctx.get("detailRecords", [])
    
    # NORMALIZE: Ensure consistent data format
    detail_records = _normalize_detail_records(detail_records)
    
    # Handle material ID queries
    if scope_type == "material_id":
        material_id = scope_value
        
        # Import helper function from response_builder
        from response_builder import get_record_comparison
        
        # Get record comparison
        comparison = get_record_comparison(detail_records, material_id)
        
        if "error" in comparison:
            # Material not found - ask for clarification
            return (
                f"I couldn't find detailed records for material {material_id}.\n\n"
                f"To help you better, please provide:\n"
                f"  • Location ID (e.g., CYS20_F01C01, DSM18_F01C01)\n"
                f"  • Or ask: 'What changed for {material_id} at [location]?'\n\n"
                f"💡 Tip: You can also ask 'Show current vs previous for {material_id}' for a comparison view."
            )
        
        # Format current vs previous comparison (Task 19)
        lines = [f"📊 Record Comparison: {material_id}\n"]
        lines.append(f"{'Field':<20} {'Current':<20} {'Previous':<20} {'Change':<15}")
        lines.append("-" * 75)
        
        forecast_delta = comparison['changes']['forecast_delta']
        lines.append(f"{'Forecast':<20} {comparison['current']['forecast']:<20} {comparison['previous']['forecast']:<20} {forecast_delta:+,.0f}")
        lines.append(f"{'ROJ':<20} {str(comparison['current']['roj']):<20} {str(comparison['previous']['roj']):<20} {'Changed' if comparison['current']['roj'] != comparison['previous']['roj'] else 'Unchanged':<15}")
        lines.append(f"{'Supplier date':<20} {str(comparison['current']['supplier_date']):<20} {str(comparison['previous']['supplier_date']):<20} {'Changed' if comparison['current']['supplier_date'] != comparison['previous']['supplier_date'] else 'Unchanged':<15}")
        lines.append(f"{'BOD':<20} {str(comparison['current']['bod']):<20} {str(comparison['previous']['bod']):<20} {'Changed' if comparison['current']['bod'] != comparison['previous']['bod'] else 'Unchanged':<15}")
        lines.append(f"{'Form Factor':<20} {str(comparison['current']['form_factor']):<20} {str(comparison['previous']['form_factor']):<20} {'Changed' if comparison['current']['form_factor'] != comparison['previous']['form_factor'] else 'Unchanged':<15}")
        lines.append("")
        
        lines.append("Flags:")
        lines.append(f"  • New demand: {comparison['changes']['is_new_demand']}")
        lines.append(f"  • Cancelled: {comparison['changes']['is_cancelled']}")
        lines.append(f"  • Risk level: {comparison['changes']['risk_level']}")
        
        return "\n".join(lines)
    
    # Handle location queries
    if scope_type == "location":
        location = scope_value
        return (
            f"To show what changed at {location}, I need more details:\n\n"
            f"Please specify:\n"
            f"  • Material ID (e.g., C00000560-001)\n"
            f"  • Or Equipment Category (e.g., UPS, MVSXRM)\n"
            f"  • Or ask: 'List suppliers for {location}'\n\n"
            f"💡 Examples:\n"
            f"  • 'What changed for C00000560-001 at {location}?'\n"
            f"  • 'Which materials have design changes at {location}?'\n"
            f"  • 'List suppliers for {location}'"
        )
    
    # Handle material group queries
    if scope_type == "material_group":
        category = scope_value
        return (
            f"To show what changed in {category}, I need more details:\n\n"
            f"Please specify:\n"
            f"  • Location ID (e.g., CYS20_F01C01, DSM18_F01C01)\n"
            f"  • Or ask: 'Which materials have design changes in {category}?'\n\n"
            f"💡 Examples:\n"
            f"  • 'What changed in {category} at CYS20_F01C01?'\n"
            f"  • 'Which materials have design changes in {category}?'\n"
            f"  • 'List suppliers for [location]'"
        )
    
    # Default: ask for clarification
    return (
        "To help you better, please provide more context:\n\n"
        "You can ask:\n"
        "  • 'What changed for [material ID]?'\n"
        "  • 'What changed at [location]?'\n"
        "  • 'What changed in [equipment category]?'\n\n"
        "💡 Examples:\n"
        "  • 'What changed for C00000560-001?'\n"
        "  • 'What changed at CYS20_F01C01?'\n"
        "  • 'What changed in UPS?'"
    )


def _generate_design_filter_answer(question: str, ctx: dict, detail_level: str = "summary") -> str:
    """Generate list of materials with design/form factor changes.
    
    Handles queries like: "Which materials have Form Factor changes?"
    
    detail_level: "summary" (basic), "detailed" (with location/supplier), "full" (all fields)
    """
    detail_records = ctx.get("detailRecords", [])
    
    # NORMALIZE: Ensure consistent data format
    detail_records = _normalize_detail_records(detail_records)
    
    # Filter records with design changes
    design_changed = [r for r in detail_records if r.get("designChanged")]
    
    if not design_changed:
        return "No materials with design changes found."
    
    # Group by material ID and compute metrics
    materials_dict = {}
    for record in design_changed:
        mat_id = record.get("materialId", "UNKNOWN")
        if mat_id not in materials_dict:
            materials_dict[mat_id] = {
                "count": 0,
                "locations": set(),
                "suppliers": set(),
                "forecast_delta": 0,
                "risk_count": 0,
                "material_group": record.get("materialGroup", ""),
                "records": [],
            }
        materials_dict[mat_id]["count"] += 1
        materials_dict[mat_id]["locations"].add(record.get("locationId", ""))
        materials_dict[mat_id]["suppliers"].add(record.get("supplier", ""))
        materials_dict[mat_id]["forecast_delta"] += record.get("qtyDelta", 0)
        if record.get("riskLevel") in ["High", "Critical"]:
            materials_dict[mat_id]["risk_count"] += 1
        materials_dict[mat_id]["records"].append(record)
    
    # Sort by count (most impacted first)
    sorted_materials = sorted(materials_dict.items(), key=lambda x: x[1]["count"], reverse=True)
    
    # Format output based on detail level
    lines = [f"📊 Materials with Design/Form Factor Changes:\n"]
    
    if detail_level == "summary":
        lines.append(f"{'Material ID':<15} {'Records':<10} {'Locations':<15} {'Forecast':<12} {'Risk':<8}")
        lines.append("-" * 60)
        for mat_id, metrics in sorted_materials[:20]:
            loc_count = len(metrics["locations"])
            forecast = f"{metrics['forecast_delta']:+,.0f}"
            risk = metrics["risk_count"]
            lines.append(f"{mat_id:<15} {metrics['count']:<10} {loc_count:<15} {forecast:<12} {risk:<8}")
    
    elif detail_level == "detailed":
        lines.append(f"{'Material ID':<15} {'Group':<15} {'Records':<10} {'Locations':<15} {'Suppliers':<15} {'Forecast':<12} {'Risk':<8}")
        lines.append("-" * 90)
        for mat_id, metrics in sorted_materials[:20]:
            loc_count = len(metrics["locations"])
            sup_count = len(metrics["suppliers"])
            forecast = f"{metrics['forecast_delta']:+,.0f}"
            risk = metrics["risk_count"]
            group = metrics["material_group"][:14]
            lines.append(f"{mat_id:<15} {group:<15} {metrics['count']:<10} {loc_count:<15} {sup_count:<15} {forecast:<12} {risk:<8}")
    
    elif detail_level == "full":
        for idx, (mat_id, metrics) in enumerate(sorted_materials[:10], 1):
            lines.append(f"\n{idx}. Material ID: {mat_id}")
            lines.append(f"   Group: {metrics['material_group']}")
            lines.append(f"   Records affected: {metrics['count']}")
            lines.append(f"   Locations: {', '.join(sorted(metrics['locations']))}")
            lines.append(f"   Suppliers: {', '.join(sorted(metrics['suppliers']))}")
            lines.append(f"   Forecast delta: {metrics['forecast_delta']:+,.0f}")
            lines.append(f"   High-risk records: {metrics['risk_count']}")
    
    lines.append(f"\nTotal: {len(sorted_materials)} materials with design changes")
    lines.append(f"\n💡 Tip: Ask for more details like 'Show locations for MAT-001' or 'Which suppliers have design changes?'")
    
    return "\n".join(lines)


def _build_comparison_metrics(ctx: dict, scope_type: str, scope_value: str) -> dict:
    """
    Build comparison metrics for comparison queries.
    Returns side-by-side metrics for two entities.
    """
    # This is a placeholder that will be populated by the comparison logic
    # The actual metrics are computed in _generate_comparison_answer
    return {
        "entity1": scope_value,
        "entity2": None,  # Will be extracted from question
        "metrics": {}
    }


def _build_supplier_metrics(ctx: dict, scope_value: str) -> dict:
    """
    Build supplier metrics for supplier-by-location queries.
    Returns supplier list with metrics for a location.
    """
    detail_records = ctx.get("detailRecords", [])
    
    # DEBUG: Log what we received
    logging.info(f"_build_supplier_metrics: scope_value={scope_value}, detailRecords count={len(detail_records)}")
    if detail_records and len(detail_records) > 0:
        logging.info(f"First record keys: {list(detail_records[0].keys()) if isinstance(detail_records[0], dict) else 'not a dict'}")
        logging.info(f"First record: {detail_records[0]}")
    
    # NORMALIZE: Ensure consistent data format
    detail_records = _normalize_detail_records(detail_records)
    
    suppliers = {}
    matched_count = 0
    
    # Group records by supplier for the given location
    for record in detail_records:
        loc = (record.get("locationId") or "").upper()
        if loc == (scope_value or "").upper():
            matched_count += 1
            supplier = record.get("supplier", "Unknown")
            if supplier not in suppliers:
                suppliers[supplier] = {
                    "supplier": supplier,
                    "affectedRecords": 0,
                    "forecastImpact": 0,
                    "designChanges": 0,
                    "availabilityIssues": 0,
                    "rojIssues": 0,
                    "riskLevel": "LOW"
                }
            
            suppliers[supplier]["affectedRecords"] += 1
            if record.get("qtyChanged"):
                suppliers[supplier]["forecastImpact"] += record.get("qtyDelta", 0)
            if record.get("designChanged"):
                suppliers[supplier]["designChanges"] += 1
            if record.get("rojChanged"):
                suppliers[supplier]["rojIssues"] += 1
            if record.get("riskLevel") in ["HIGH", "CRITICAL"]:
                suppliers[supplier]["riskLevel"] = record.get("riskLevel")
    
    logging.info(f"_build_supplier_metrics: matched {matched_count} records for location {scope_value}, found {len(suppliers)} suppliers")
    
    return {
        "location": scope_value,
        "suppliers": list(suppliers.values())
    }


def _build_record_comparison(ctx: dict, scope_type: str, scope_value: str) -> dict:
    """
    Build record comparison for record-detail queries.
    Returns current vs previous comparison for a record.
    """
    detail_records = ctx.get("detailRecords", [])
    
    # NORMALIZE: Ensure consistent data format
    detail_records = _normalize_detail_records(detail_records)
    
    # Find the record matching the scope
    for record in detail_records:
        if scope_type == "material_id" and (record.get("materialId") or "").upper() == (scope_value or "").upper():
            return {
                "materialId": record.get("materialId"),
                "locationId": record.get("locationId"),
                "current": {
                    "forecast": record.get("forecastQty"),
                    "roj": record.get("roj"),
                    "bod": record.get("bod"),
                    "formFactor": record.get("formFactor"),
                },
                "previous": {
                    "forecast": record.get("forecastQtyPrevious"),
                    "roj": record.get("rojPrevious"),
                    "bod": record.get("bodPrevious"),
                    "formFactor": record.get("ffPrevious"),
                },
                "changes": {
                    "forecastDelta": record.get("qtyDelta"),
                    "qtyChanged": record.get("qtyChanged"),
                    "rojChanged": record.get("rojChanged"),
                    "designChanged": record.get("designChanged"),
                    "supplierChanged": record.get("supplierChanged"),
                },
                "riskLevel": record.get("riskLevel")
            }
    
    return {}


@app.route(route="explain", methods=["POST"])
def explain(req: func.HttpRequest) -> func.HttpResponse:
    """
    Focused insight endpoint with real-time, question-specific answers.
    
    ENHANCED WITH NLP LAYER INTEGRATION (BUGFIX):
    - Routes natural language questions through NLP layer first
    - Performs intent classification, entity extraction, out-of-scope detection
    - Maintains conversation history to prevent duplicate responses
    - Falls back to REASONING ENGINE for complete queries
    
    NLP Layer Integration:
    - Detects out-of-scope questions and returns clarification
    - Extracts entities and classifies intent
    - Maintains conversation context across interactions
    - Prevents duplicate responses
    """
    logging.info("Explain endpoint triggered.")
    try:
        body = req.get_json()
    except ValueError:
        return _error("Invalid JSON body.", 400)

    question: str = body.get("question", "").strip()
    if not question:
        return _error("question is required", 400)

    location_id: Optional[str] = body.get("location_id")
    material_group: Optional[str] = body.get("material_group")
    context: Optional[dict] = body.get("context")
    selected_context: Optional[dict] = body.get("selectedContext")  # User's previous selections
    conversation_history: Optional[List[dict]] = body.get("conversationHistory", [])

    # Get detail records from context or snapshot
    detail_records = []
    if context:
        detail_records = context.get("detailRecords", [])
    
    if not detail_records:
        snap = load_snapshot()
        if snap:
            detail_records = snap.get("detailRecords", [])
    
    if not detail_records:
        return _error("No detail records available. Run daily-refresh to load data.", 404)
    
    # Normalize records
    detail_records = _normalize_detail_records(detail_records)
    
    try:
        # ===== NEW: PHASE 1 - ROUTE THROUGH NLP LAYER FIRST =====
        # Step 1: Process question through NLP layer for intent classification and entity extraction
        logging.info(f"Processing question through NLP layer: {question}")
        nlp_handler = NLPEndpointHandler()
        nlp_response = nlp_handler.process_question(
            question=question,
            detail_records=detail_records,
            conversation_history=conversation_history
        )
        
        # Extract NLP results
        nlp_query_type = nlp_response.get("queryType", "summary")
        nlp_scope_type = nlp_response.get("scopeType")
        nlp_scope_value = nlp_response.get("scopeValue")
        nlp_confidence = nlp_response.get("confidence", 0.5)
        nlp_answer = nlp_response.get("answer")
        nlp_conversation_history = nlp_response.get("conversationHistory", [])
        azure_openai_used = nlp_response.get("azureOpenAIUsed", False)
        
        logging.info(f"NLP Classification: queryType={nlp_query_type}, confidence={nlp_confidence}, azureOpenAIUsed={azure_openai_used}")
        
        # ===== NEW: PHASE 2 - HANDLE OUT-OF-SCOPE QUESTIONS =====
        # Step 2: If NLP detected out-of-scope question, return NLP response directly
        if nlp_query_type == "out_of_scope":
            logging.info("Out-of-scope question detected by NLP layer")
            response = {
                "question": question,
                "answer": nlp_answer,
                "intent": nlp_query_type,
                "entities": {},
                "nlpProcessed": True,
                "azureOpenAIUsed": azure_openai_used,
                "confidence": nlp_confidence,
                "conversationHistory": nlp_conversation_history,
                "timestamp": get_last_updated_time(),
            }
            return func.HttpResponse(
                json.dumps(response, default=str),
                mimetype="application/json",
                status_code=200,
            )
        
        # ===== NEW: PHASE 3 - HANDLE CLARIFICATION NEEDED =====
        # Step 3: If NLP detected clarification is needed, return clarification response
        if nlp_query_type == "clarification_needed":
            logging.info("Clarification needed for question")
            response = {
                "question": question,
                "answer": nlp_answer,
                "intent": nlp_query_type,
                "entities": {},
                "nlpProcessed": True,
                "azureOpenAIUsed": azure_openai_used,
                "confidence": nlp_confidence,
                "conversationHistory": nlp_conversation_history,
                "timestamp": get_last_updated_time(),
            }
            return func.HttpResponse(
                json.dumps(response, default=str),
                mimetype="application/json",
                status_code=200,
            )
        
        # ===== NEW: PHASE 4 - CHECK FOR DUPLICATE QUESTIONS =====
        # Step 4: Check if this is a duplicate question in conversation history
        is_duplicate = False
        cached_answer = None
        if nlp_conversation_history and len(nlp_conversation_history) > 1:
            # Check if same question was asked recently
            for prev_turn in nlp_conversation_history[:-1]:  # Exclude current turn
                if prev_turn.get("question", "").lower() == question.lower():
                    is_duplicate = True
                    cached_answer = prev_turn.get("answer")
                    logging.info(f"Duplicate question detected, using cached response")
                    break
        
        if is_duplicate and cached_answer:
            # Return cached response for duplicate question
            response = {
                "question": question,
                "answer": cached_answer,
                "intent": nlp_query_type,
                "entities": {},
                "nlpProcessed": True,
                "azureOpenAIUsed": azure_openai_used,
                "confidence": nlp_confidence,
                "isDuplicate": True,
                "conversationHistory": nlp_conversation_history,
                "timestamp": get_last_updated_time(),
            }
            return func.HttpResponse(
                json.dumps(response, default=str),
                mimetype="application/json",
                status_code=200,
            )
        
        # ===== PHASE 5 - USE NLP RESULTS TO GUIDE REASONING ENGINE =====
        # Step 5: Parse query using enhanced intent parser (for backward compatibility)
        intent_parser = EnhancedIntentParser()
        query_type, extracted_entities = intent_parser.parse_query(question)
        
        # Override with NLP results if confidence is high
        if nlp_confidence > 0.8:
            query_type = nlp_query_type
            extracted_entities = nlp_scope_value or extracted_entities
            logging.info(f"Using NLP classification (confidence={nlp_confidence})")
        
        # Step 6: Check for missing context using clarification engine
        clarification_engine = ClarificationEngine()
        has_missing, next_step, clarification_data = clarification_engine.detect_missing_context(
            query_type=query_type,
            extracted_entities=extracted_entities,
            detail_records=detail_records
        )
        
        # Step 7: If context is missing, return clarification response
        if has_missing:
            logging.info(f"Missing context detected: {next_step}")
            
            # Build clarification response with data-driven options
            response = {
                "question": question,
                "requiresClarification": True,
                "clarificationNeeded": {
                    "nextStep": next_step,
                    "clarificationData": clarification_data,
                },
                "intent": query_type,
                "extractedEntities": extracted_entities,
                "nlpProcessed": True,
                "azureOpenAIUsed": azure_openai_used,
                "confidence": nlp_confidence,
                "conversationHistory": nlp_conversation_history,
                "timestamp": get_last_updated_time(),
            }
            
            return func.HttpResponse(
                json.dumps(response, default=str),
                mimetype="application/json",
                status_code=200,
            )
        
        # Step 8: Context is complete, process query through reasoning engine
        engine = ReasoningEngine()
        answer = engine.process_query(question, detail_records)
        
        # Extract entities for response
        entities = {
            "location": engine.extractor.extract_location(question),
            "material_id": engine.extractor.extract_material_id(question),
            "material_group": engine.extractor.extract_material_group(question),
            "supplier": engine.extractor.extract_supplier(question),
            "comparison_pair": engine.extractor.extract_comparison_pair(question),
        }
        
        intent = engine.classifier.classify(question)
        
        # ===== NEW: BUILD RESPONSE WITH NLP METADATA =====
        # Build response with NLP metadata included
        response = {
            "question": question,
            "answer": answer,
            "intent": intent,
            "entities": entities,
            "dataMode": "reasoning",
            "requiresClarification": False,
            # NEW: NLP metadata
            "nlpProcessed": True,
            "nlpIntent": nlp_query_type,
            "scopeType": nlp_scope_type,  # Include scope type in response
            "scopeValue": nlp_scope_value,  # Include scope value in response
            "nlpScopeType": nlp_scope_type,
            "nlpScopeValue": nlp_scope_value,
            "nlpConfidence": nlp_confidence,
            "confidence": nlp_confidence,  # Also include as confidence for compatibility
            "azureOpenAIUsed": azure_openai_used,  # Track if Azure OpenAI was used
            "conversationHistory": nlp_conversation_history,
            "timestamp": get_last_updated_time(),
        }
        
        # Add context if available
        if context:
            response["contextUsed"] = [k for k, v in context.items() if v is not None]
            response["aiInsight"] = context.get("aiInsight")
            response["rootCause"] = context.get("rootCause")
            response["recommendedActions"] = context.get("recommendedActions", [])
            response["planningHealth"] = context.get("planningHealth")
        
        return func.HttpResponse(
            json.dumps(response, default=str),
            mimetype="application/json",
            status_code=200,
        )
    
    except Exception as e:
        logging.error(f"Query processing failed: {e}", exc_info=True)
        return _error(f"Query processing failed: {str(e)}", 500)


def _generate_answer_from_context(question: str, ctx: dict, answer_mode: str = "summary", scope_type: str = None, scope_value: str = None, scoped_metrics: dict = None) -> str:
    """Generate answer based on mode and scope. Enhanced for comparison and supplier queries.
    
    Task 18: Improved response filtering - shows only answer to current question, removes unrelated metrics.
    """
    query_type = _classify_question(question)
    
    # Investigate mode routing
    if answer_mode == "investigate":
        if query_type == "comparison":
            if isinstance(scope_value, list) and len(scope_value) >= 2:
                return _generate_comparison_answer(question, ctx, scope_type, scope_value)
            return "Could not extract entities to compare."
        elif query_type == "supplier_by_location":
            return _generate_supplier_by_location_answer(question, ctx, scope_type, scope_value, detail_level="detailed")
        elif query_type == "record_detail":
            return _generate_record_comparison_answer(question, ctx, scope_type, scope_value)
        elif query_type == "design_filter":
            return _generate_design_filter_answer(question, ctx, detail_level="detailed")
        elif query_type == "root_cause":
            return _generate_root_cause_answer(question, ctx, scope_type, scope_value, scoped_metrics)
        elif query_type == "why_not":
            return _generate_why_not_answer(question, ctx, scope_type, scope_value, scoped_metrics)
        elif query_type == "traceability":
            return _generate_traceability_answer(question, ctx, scoped_metrics)
    
    # Default: summary mode with improved filtering (Task 18)
    q = question.lower()
    health = ctx.get("planningHealth")
    status = ctx.get("status", "")
    changed = ctx.get("changedRecordCount", 0)
    total = ctx.get("totalRecords", 0)
    pct = round(changed / total * 100, 1) if total else 0
    ai_insight = ctx.get("aiInsight", "")
    root_cause = ctx.get("rootCause", "")
    actions = ctx.get("recommendedActions", [])
    drivers = ctx.get("drivers") or {}
    risk_summary = ctx.get("riskSummary") or {}
    risk = risk_summary.get("highestRiskLevel", "Normal")
    trend = ctx.get("trendDirection", "")
    trend_delta = ctx.get("trendDelta", 0)
    contrib = ctx.get("contributionBreakdown") or {}
    kpis = ctx.get("kpis") or {}
    details = ctx.get("detailRecords") or []
    dc_summary = ctx.get("datacenterSummary") or []
    mg_summary = ctx.get("materialGroupSummary") or []

    # Task 18: Filter responses to show only answer to current question
    # Remove unrelated metrics and suggestions, keep answer and supporting metrics for current scope
    
    if any(w in q for w in ["health", "critical", "score", "low"]):
        contrib_text = ""
        if contrib:
            contrib_text = f" Breakdown: Qty {contrib.get('quantity', 0)}%, Supplier {contrib.get('supplier', 0)}%, Design {contrib.get('design', 0)}%, Schedule {contrib.get('schedule', 0)}%."
        return (
            f"Planning health is {health}/100 ({status}). "
            f"{pct}% of records changed ({changed}/{total}). "
            f"Risk level: {risk}.{contrib_text}"
        )
    if any(w in q for w in ["changed", "change", "most", "what changed"]):
        loc = drivers.get("location", "N/A")
        change_type = drivers.get("changeType", "N/A")
        contrib_text = ""
        if contrib:
            contrib_text = f" Contribution: Qty {contrib.get('quantityCount', 0)}, Supplier {contrib.get('supplierCount', 0)}, Design {contrib.get('designCount', 0)}, Schedule {contrib.get('scheduleCount', 0)}."
        return (
            f"{changed} records changed ({pct}% of total). "
            f"Primary driver: {change_type}. Top location: {loc}.{contrib_text}"
        )
    if any(w in q for w in ["forecast", "demand", "increase", "decrease", "trend"]):
        return (
            f"Forecast trend is {trend} with a delta of {trend_delta:+,.0f} units. "
            f"Demand volatility: {kpis.get('demandVolatility', 'N/A')}%."
        )
    if any(w in q for w in ["action", "planner", "do next", "recommend"]):
        if actions:
            return "Recommended actions:\n" + "\n".join(f"• {a}" for a in actions)
        return "No specific actions recommended at this time."
    if any(w in q for w in ["location", "site", "datacenter"]):
        # Check if asking about a specific location
        if scope_type == "location" and scope_value:
            return (
                f"To show what changed at {scope_value}, I need more details:\n\n"
                f"Please specify:\n"
                f"  • Material ID (e.g., C00000560-001)\n"
                f"  • Or Equipment Category (e.g., UPS, MVSXRM)\n"
                f"  • Or ask: 'List suppliers for {scope_value}'\n\n"
                f"💡 Examples:\n"
                f"  • 'What changed for C00000560-001 at {scope_value}?'\n"
                f"  • 'Which materials have design changes at {scope_value}?'\n"
                f"  • 'List suppliers for {scope_value}'"
            )
        # Global location query
        loc = drivers.get("location", "N/A")
        top_locs = ", ".join(f"{d.get('locationId', '?')}: {d.get('changed', 0)} changed" for d in dc_summary[:3]) if dc_summary else "N/A"
        return f"Top impacted location: {loc}. Top locations: {top_locs}."
    if any(w in q for w in ["material", "group", "category", "equipment"]):
        # Check if asking about a specific material group
        if scope_type == "material_group" and scope_value:
            return (
                f"To show what changed in {scope_value}, I need more details:\n\n"
                f"Please specify:\n"
                f"  • Location ID (e.g., CYS20_F01C01, DSM18_F01C01)\n"
                f"  • Or ask: 'Which materials have design changes in {scope_value}?'\n\n"
                f"💡 Examples:\n"
                f"  • 'What changed in {scope_value} at CYS20_F01C01?'\n"
                f"  • 'Which materials have design changes in {scope_value}?'\n"
                f"  • 'List suppliers for [location]'"
            )
        # Global material group query
        top_mgs = ", ".join(f"{g.get('materialGroup', '?')}: {g.get('changed', 0)} changed" for g in mg_summary[:3]) if mg_summary else "N/A"
        return f"Top material groups: {top_mgs}."
    if any(w in q for w in ["supplier"]):
        # Check if asking about a specific location
        if scope_type == "location" and scope_value:
            return _generate_supplier_by_location_answer(question, ctx, scope_type, scope_value, detail_level="detailed")
        # Global supplier query - ask for clarification
        return (
            "To analyze suppliers, I need more context:\n\n"
            "Please specify:\n"
            "  • Location ID (e.g., CYS20_F01C01, DSM18_F01C01)\n"
            "  • Or ask: 'List suppliers for [location]'\n\n"
            "💡 Examples:\n"
            "  • 'List suppliers for CYS20_F01C01'\n"
            "  • 'Which suppliers at CYS20_F01C01 have design changes?'\n"
            "  • 'Which locations have the most changes?'"
        )
    if any(w in q for w in ["risk", "high risk"]):
        high_risk_count = risk_summary.get("highRiskCount", 0)
        risk_conc = kpis.get("riskConcentration", "N/A")
        return f"Risk level: {risk}. High-risk records: {high_risk_count}. Risk concentration: {risk_conc}%."
    if any(w in q for w in ["design", "bod", "form factor"]):
        design_rate = kpis.get("designChangeRate", "N/A")
        return f"Design change rate: {design_rate}%."
    if any(w in q for w in ["schedule", "roj", "delay"]):
        # Check if asking about a specific location
        if scope_type == "location" and scope_value:
            return (
                f"To check ROJ delays at {scope_value}, I need more details:\n\n"
                f"Please specify:\n"
                f"  • Material ID (e.g., C00000560-001)\n"
                f"  • Or Equipment Category (e.g., UPS, MVSXRM)\n"
                f"  • Or ask: 'List suppliers for {scope_value}'\n\n"
                f"💡 Examples:\n"
                f"  • 'Which suppliers at {scope_value} have ROJ delays?'\n"
                f"  • 'List suppliers for {scope_value}'\n"
                f"  • 'Which locations have ROJ delays?'"
            )
        # Global ROJ query
        stability = kpis.get("scheduleStability", "N/A")
        return f"Schedule stability: {stability}%."
    if any(w in q for w in ["new demand", "new record"]):
        new_ratio = kpis.get("newDemandRatio", "N/A")
        return f"New demand ratio: {new_ratio}%. {ctx.get('newRecordCount', 0)} new records this cycle."
    if any(w in q for w in ["cancel"]):
        cancel_rate = kpis.get("cancellationRate", "N/A")
        return f"Cancellation rate: {cancel_rate}%."
    if any(w in q for w in ["kpi", "metric", "score"]):
        parts = [f"Design change rate: {kpis.get('designChangeRate', 'N/A')}%",
                 f"Supplier reliability: {kpis.get('supplierReliability', 'N/A')}%",
                 f"Demand volatility: {kpis.get('demandVolatility', 'N/A')}%",
                 f"Schedule stability: {kpis.get('scheduleStability', 'N/A')}%",
                 f"Risk concentration: {kpis.get('riskConcentration', 'N/A')}%"]
        return "KPI Summary:\n" + "\n".join(f"• {p}" for p in parts)

    # --- COMPARISON MODE ---
    if any(w in q for w in ["compare", " vs ", "versus", "difference between"]):
        return _handle_comparison(q, ctx, dc_summary, mg_summary, details)

    # --- WHY-NOT REASONING ---
    if any(w in q for w in ["why not", "why isn't", "not risky", "not flagged", "not changed", "stable"]):
        return _handle_why_not(q, ctx, dc_summary, mg_summary, details)

    # --- TRACEABILITY / TOP RECORDS ---
    if any(w in q for w in ["top record", "contributing", "impacted material", "show record", "detail"]):
        return _handle_traceability(q, ctx, details)

    # Default: return focused insight
    return ai_insight or root_cause or "No analysis available for this question."


def _handle_comparison(q: str, ctx: dict, dc_summary: list, mg_summary: list, details: list) -> str:
    """Handle comparison prompts by extracting two entities and comparing metrics."""
    import re
    # Try to extract two entities from "compare X vs Y" or "X versus Y"
    match = re.search(r'(?:compare\s+)?(\S+)\s+(?:vs\.?|versus|and)\s+(\S+)', q)
    if not match:
        return "Please specify two entities to compare, e.g., 'Compare LOC001 vs LOC002'."

    a, b = match.group(1).upper(), match.group(2).upper()

    # Try location comparison
    loc_a = next((d for d in dc_summary if d.get("locationId", "").upper() == a), None)
    loc_b = next((d for d in dc_summary if d.get("locationId", "").upper() == b), None)
    if loc_a and loc_b:
        pct_a = round(loc_a["changed"] / max(loc_a["total"], 1) * 100, 1)
        pct_b = round(loc_b["changed"] / max(loc_b["total"], 1) * 100, 1)
        return (
            f"📊 Comparison: {a} vs {b}\n\n"
            f"{a}: {loc_a['changed']}/{loc_a['total']} changed ({pct_a}%)\n"
            f"{b}: {loc_b['changed']}/{loc_b['total']} changed ({pct_b}%)\n\n"
            f"{'→ ' + a + ' has more changes.' if loc_a['changed'] > loc_b['changed'] else '→ ' + b + ' has more changes.' if loc_b['changed'] > loc_a['changed'] else '→ Both have equal changes.'}"
        )

    # Try material group comparison
    mg_a = next((g for g in mg_summary if g.get("materialGroup", "").upper() == a), None)
    mg_b = next((g for g in mg_summary if g.get("materialGroup", "").upper() == b), None)
    if mg_a and mg_b:
        return (
            f"📊 Comparison: {a} vs {b}\n\n"
            f"{a}: {mg_a.get('changed', 0)}/{mg_a.get('total', 0)} changed (Qty:{mg_a.get('qtyChanged', 0)} Design:{mg_a.get('designChanged', 0)} Supplier:{mg_a.get('supplierChanged', 0)})\n"
            f"{b}: {mg_b.get('changed', 0)}/{mg_b.get('total', 0)} changed (Qty:{mg_b.get('qtyChanged', 0)} Design:{mg_b.get('designChanged', 0)} Supplier:{mg_b.get('supplierChanged', 0)})\n\n"
            f"{'→ ' + a + ' is more impacted.' if mg_a.get('changed', 0) > mg_b.get('changed', 0) else '→ ' + b + ' is more impacted.'}"
        )

    return f"Could not find both {a} and {b} in the current dataset. Available locations: {', '.join(d.get('locationId', '') for d in dc_summary[:5])}."


def _handle_why_not(q: str, ctx: dict, dc_summary: list, mg_summary: list, details: list) -> str:
    """Handle why-not reasoning — explain absence of risk or change."""
    risk_summary = ctx.get("riskSummary") or {}
    drivers = ctx.get("drivers") or {}

    # Extract entity name from question
    words = q.split()
    entity = None
    for w in words:
        if w.upper() in [d.get("locationId", "").upper() for d in dc_summary]:
            entity = w.upper()
            break
        if w.upper() in [g.get("materialGroup", "").upper() for g in mg_summary]:
            entity = w.upper()
            break

    if entity:
        loc = next((d for d in dc_summary if d.get("locationId", "").upper() == entity), None)
        mg = next((g for g in mg_summary if g.get("materialGroup", "").upper() == entity), None)
        if loc:
            if loc["changed"] == 0:
                return f"📊 {entity} is stable because no records changed this cycle ({loc['total']} total records, 0 changed). No risk signals detected."
            pct = round(loc["changed"] / max(loc["total"], 1) * 100, 1)
            return f"📊 {entity} has {loc['changed']}/{loc['total']} changes ({pct}%). It {'is flagged' if pct > 25 else 'is below the risk threshold because change rate is low'}."
        if mg:
            if mg["changed"] == 0:
                return f"📊 {entity} is stable — no changes detected across {mg['total']} records."
            return f"📊 {entity} has {mg['changed']}/{mg['total']} changes. Design: {mg.get('designChanged', 0)}, Supplier: {mg.get('supplierChanged', 0)}. {'Low risk because no design/supplier changes.' if mg.get('designChanged', 0) == 0 and mg.get('supplierChanged', 0) == 0 else ''}"

    # Generic why-not
    if risk_summary.get("highRiskCount", 0) == 0:
        return "📊 No high-risk records detected this cycle. All changes are within normal parameters."
    return f"📊 Current risk level is {risk_summary.get('highestRiskLevel', 'Normal')}. {risk_summary.get('highRiskCount', 0)} records are flagged. Entities not mentioned are below risk thresholds."


def _handle_traceability(q: str, ctx: dict, details: list) -> str:
    """Return top contributing records for traceability."""
    if not details:
        return "📊 Detail records are not available in the current context. Run daily-refresh to populate."

    # Sort by absolute qty_delta descending
    sorted_details = sorted(details, key=lambda r: abs(r.get("qtyDelta") or 0), reverse=True)
    top = sorted_details[:5]
    lines = []
    for r in top:
        delta = r.get("qtyDelta")
        delta_str = f"{delta:+,.0f}" if delta is not None else "N/A"
        lines.append(f"  {r.get('locationId', '?')} / {r.get('materialGroup', '?')} / {r.get('materialId', '?')} — Δ{delta_str} [{r.get('changeType', '?')}] [{r.get('riskLevel', '?')}]")
    return f"📊 Top {len(top)} contributing records (by forecast delta):\n" + "\n".join(lines)


def _classify_question(question: str) -> str:
    """Classify question type for routing and explainability. Enhanced for comparison and supplier queries."""
    q = question.lower()
    
    # Comparison queries
    if any(w in q for w in ["compare", " vs ", "versus", "difference between", "compared to"]):
        return "comparison"
    
    # Supplier queries
    if any(w in q for w in ["supplier", "suppliers", "which supplier", "list supplier"]):
        return "supplier_by_location"
    
    # Record detail queries
    if any(w in q for w in ["what changed", "compare this", "current vs previous", "record detail"]):
        return "record_detail"
    
    # Why-not queries
    if any(w in q for w in ["why not", "why isn't", "not risky", "not flagged", "not changed", "stable"]):
        return "why_not"
    
    # Traceability queries
    if any(w in q for w in ["top record", "contributing", "impacted material", "show record", "detail"]):
        return "traceability"
    
    # Design/Form Factor queries - materials with design changes
    if any(w in q for w in ["which materials have", "which material", "materials with"]) and any(w in q for w in ["design", "form factor", "bod"]):
        return "design_filter"
    
    # Root cause queries
    if any(w in q for w in ["why", "cause", "reason", "root"]):
        return "root_cause"
    
    # Risk queries
    if any(w in q for w in ["risk", "high risk", "danger"]):
        return "risk"
    
    # Action queries
    if any(w in q for w in ["action", "do next", "recommend", "planner"]):
        return "action"
    
    # Provenance queries
    if any(w in q for w in ["source", "blob", "mock", "refresh", "stale", "provenance"]):
        return "provenance"
    
    return "summary"


def _build_explainability(ctx: dict, question: str) -> dict:
    """Build explainability metadata for the response."""
    from datetime import datetime, timezone
    last_refreshed = ctx.get("lastRefreshedAt")
    freshness_minutes = None
    is_stale = False
    if last_refreshed:
        try:
            refreshed_dt = datetime.fromisoformat(last_refreshed.replace("Z", "+00:00"))
            freshness_minutes = round((datetime.now(timezone.utc) - refreshed_dt).total_seconds() / 60, 1)
            is_stale = freshness_minutes > 1440  # stale if > 24 hours
        except (ValueError, TypeError):
            pass

    total = ctx.get("totalRecords", 0)
    changed = ctx.get("changedRecordCount", 0)
    data_coverage = round(changed / max(total, 1) * 100, 1)

    # Confidence based on data availability
    fields_present = sum(1 for k in ["aiInsight", "rootCause", "drivers", "riskSummary", "contributionBreakdown", "kpis"] if ctx.get(k))
    confidence = min(round(fields_present / 6 * 100), 100)

    return {
        "confidenceScore": confidence,
        "dataCoverage": data_coverage,
        "dataSource": ctx.get("dataMode", "unknown"),
        "lastRefreshedAt": last_refreshed,
        "dataFreshnessMinutes": freshness_minutes,
        "isStale": is_stale,
        "queryType": _classify_question(question),
        "fieldsUsed": [k for k in ["aiInsight", "rootCause", "drivers", "riskSummary", "contributionBreakdown", "kpis", "detailRecords"] if ctx.get(k)],
    }


def _build_suggested_actions(question: str, ctx: dict) -> list:
    """Build actionable suggestions based on question and context."""
    q = question.lower()
    actions = []
    if any(w in q for w in ["risk", "high risk"]):
        actions.append({"action": "filter_dashboard", "label": "Show high-risk records", "filter": "risk"})
    if any(w in q for w in ["supplier"]):
        actions.append({"action": "open_drill_down", "label": "Review supplier details", "type": "supplier"})
    if any(w in q for w in ["design", "bod"]):
        actions.append({"action": "open_drill_down", "label": "Show design changes", "type": "material"})
    if any(w in q for w in ["location", "datacenter"]):
        actions.append({"action": "open_drill_down", "label": "Drill into location", "type": "location"})
    if any(w in q for w in ["schedule", "roj", "delay"]):
        actions.append({"action": "filter_dashboard", "label": "Show delayed ROJ records", "filter": "roj"})
    if not actions:
        actions.append({"action": "open_copilot", "label": "Ask a follow-up question"})
    return actions


def _build_follow_ups(question: str, ctx: dict) -> list:
    """Generate contextual follow-up questions.
    
    Task 20: Improved follow-up suggestion generation - 2-3 contextual suggestions per answer.
    Implements patterns for each intent type to guide toward deeper analysis.
    """
    q = question.lower()
    query_type = _classify_question(question)
    drivers = ctx.get("drivers") or {}
    follow_ups = []
    
    # Task 20: Contextual suggestions based on query type
    if query_type == "comparison":
        # For comparison: suggest drill-down into specific supplier or material
        follow_ups = [
            "Which supplier is driving the difference?",
            "Show design changes for each entity",
            "What's the forecast impact for each?"
        ]
    elif query_type == "supplier_by_location":
        # For supplier: suggest root cause analysis
        follow_ups = [
            "Why is this supplier having issues?",
            "What's the root cause of the changes?",
            "Which materials are most affected?"
        ]
    elif query_type == "record_detail":
        # For record detail: suggest comparison with other records
        follow_ups = [
            "How does this compare to other records?",
            "What's the risk level for this record?",
            "Show similar records with changes"
        ]
    elif query_type == "root_cause":
        # For root cause: suggest actions and related analysis
        follow_ups = [
            "What actions should be taken?",
            "Which locations are most impacted?",
            "Show top contributing records"
        ]
    elif query_type == "why_not":
        # For why-not: suggest what IS changing
        follow_ups = [
            "What IS driving changes?",
            "Show current risk level",
            "What changed most this cycle?"
        ]
    elif query_type == "traceability":
        # For traceability: suggest deeper analysis
        follow_ups = [
            "Why are these records changing?",
            "What's the risk level for top records?",
            "Compare these records to others"
        ]
    elif any(w in q for w in ["health", "critical"]):
        follow_ups = ["What is driving the risk?", "Which locations are most impacted?", "What actions should be taken?"]
    elif any(w in q for w in ["change", "driver"]):
        follow_ups = ["Is this demand-driven or design-driven?", "Show top risk areas", "What should the planner do?"]
    elif any(w in q for w in ["supplier"]):
        follow_ups = ["Which materials are affected?", "Is there a schedule delay?", "What is the supplier reliability?"]
    elif any(w in q for w in ["location"]):
        follow_ups = ["Which material groups changed here?", "What is the forecast delta?", "Any design changes?"]
    elif any(w in q for w in ["forecast", "demand"]):
        follow_ups = ["Is this a spike or a trend?", "Which locations drive the increase?", "What actions are recommended?"]
    elif any(w in q for w in ["not", "why not", "isn't"]):
        follow_ups = ["What IS driving changes?", "Show current risk level", "What changed most?"]
    else:
        follow_ups = ["What changed most?", "Show KPI summary", "What should the planner do next?"]
    
    return follow_ups[:3]


def _filter_snapshot(snap: dict, location_id: Optional[str], material_group: Optional[str]) -> dict:
    """Filter detailRecords in a cached snapshot by location/material group."""
    if not snap.get("detailRecords"):
        return snap
    loc = location_id.strip().lower() if location_id else None
    mg = material_group.strip().lower() if material_group else None
    snap["detailRecords"] = [
        r for r in snap["detailRecords"]
        if (not loc or r.get("locationId", "").lower() == loc)
        and (not mg or r.get("materialGroup", "").lower() == mg)
    ]
    return snap


@app.route(route="debug-snapshot", methods=["POST"])
def debug_snapshot(req: func.HttpRequest) -> func.HttpResponse:
    """
    Debug endpoint — returns raw intermediate analytics values for validation.
    Accepts optional mode, location_id, material_group to scope the analysis.
    """
    logging.info("Debug snapshot endpoint triggered.")
    try:
        body = req.get_json()
    except ValueError:
        body = {}

    mode: str = (body.get("mode") or "cached").lower()
    location_id: Optional[str] = body.get("location_id")
    material_group: Optional[str] = body.get("material_group")

    try:
        if mode == "cached":
            snap = load_snapshot()
            if not snap:
                return _error("No cached snapshot available. Run daily refresh first.", 404)
            # Return debug info derived from snapshot
            changed = snap.get("changedRecordCount", 0)
            total = snap.get("totalRecords", 0)
            risk_summary = snap.get("riskSummary", {})
            return func.HttpResponse(
                json.dumps({
                    "normalizedCount": total,
                    "filteredCount": total,
                    "comparedCount": total,
                    "changedCount": changed,
                    "healthScoreInputs": {
                        "total": total,
                        "changed": changed,
                        "riskCounts": risk_summary.get("riskBreakdown", {}),
                        "designCount": risk_summary.get("designChangedCount", 0),
                        "supplierCount": risk_summary.get("supplierChangedCount", 0),
                        "highestRisk": risk_summary.get("highestRiskLevel", "Normal"),
                        "deductions": {
                            "changeRatio": round((changed / max(total, 1)) * 40),
                            "riskLevel": 25 if "Design + Supplier" in risk_summary.get("highestRiskLevel", "") else 15 if any(x in risk_summary.get("highestRiskLevel", "") for x in ["Design", "Supplier"]) else 10 if "Spike" in risk_summary.get("highestRiskLevel", "") else 0,
                            "designPenalty": min(risk_summary.get("designChangedCount", 0) * 2, 10),
                            "supplierPenalty": min(risk_summary.get("supplierChangedCount", 0) * 2, 10),
                        },
                    },
                    "dashboardResponse": snap,
                }, default=str),
                mimetype="application/json",
                status_code=200,
            )

        elif mode == "blob":
            from blob_loader import load_current_previous_from_blob
            current_rows, previous_rows = load_current_previous_from_blob()

        else:
            return _error("Only blob and cached modes are supported.", 400)

        # Run pipeline capturing intermediate counts
        current_records = normalize_rows(current_rows, is_current=True)
        previous_records = normalize_rows(previous_rows, is_current=False)
        current_filtered = filter_records(current_records, location_id, material_group)
        previous_filtered = filter_records(previous_records, location_id, material_group)
        compared = compare_records(current_filtered, previous_filtered)

        from analytics import is_changed
        changed_records = [r for r in compared if is_changed(r)]
        changed_count = len(changed_records)
        total_count = len(compared)

        from collections import Counter
        risk_counts = Counter(r.risk_level for r in changed_records if r.risk_level != "Normal")
        design_count = sum(1 for r in changed_records if r.design_changed)
        supplier_count = sum(1 for r in changed_records if r.supplier_changed)
        highest_risk = next((r for r in ["Design + Supplier Change Risk", "Design Change Risk", "Supplier Change Risk", "High Demand Spike"] if r in risk_counts), "Normal")

        change_ratio_ded = round((changed_count / max(total_count, 1)) * 40)
        risk_ded = 25 if "Design + Supplier" in highest_risk else 15 if any(x in highest_risk for x in ["Design", "Supplier"]) else 10 if "Spike" in highest_risk else 0
        design_ded = min(design_count * 2, 10)
        supplier_ded = min(supplier_count * 2, 10)

        result = build_response(compared, [], location_id, material_group, data_mode=mode)

        return func.HttpResponse(
            json.dumps({
                "normalizedCount": len(current_records),
                "filteredCount": len(current_filtered),
                "comparedCount": total_count,
                "changedCount": changed_count,
                "healthScoreInputs": {
                    "total": total_count,
                    "changed": changed_count,
                    "riskCounts": dict(risk_counts),
                    "designCount": design_count,
                    "supplierCount": supplier_count,
                    "highestRisk": highest_risk,
                    "deductions": {
                        "changeRatio": change_ratio_ded,
                        "riskLevel": risk_ded,
                        "designPenalty": design_ded,
                        "supplierPenalty": supplier_ded,
                    },
                },
                "dashboardResponse": result,
            }, default=str),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logging.exception("Debug snapshot failed")
        return _error(f"Debug snapshot failed: {str(e)}", 500)
