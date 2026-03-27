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

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


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
    Hybrid AI dashboard endpoint with mode switching.

    Modes:
      "cached" (default) — returns stored daily snapshot instantly
      "live"             — reads current_rows/previous_rows from request body
      "sharepoint"       — reads directly from SharePoint (no rows needed)
    """
    logging.info("Planning Dashboard v2 triggered.")

    try:
        body = req.get_json()
    except ValueError:
        return _error("Invalid JSON body.", 400)

    mode: str = body.get("mode", "cached").lower()
    location_id: Optional[str] = body.get("location_id")
    material_group: Optional[str] = body.get("material_group")
    recurring_threshold: int = int(body.get("recurring_threshold", 3))

    # ----------------------------------------------------------------
    # CACHED MODE — return snapshot immediately
    # ----------------------------------------------------------------
    if mode == "cached":
        snap = load_snapshot()
        if snap:
            # Apply filters to detail records if requested
            if location_id or material_group:
                snap = _filter_snapshot(snap, location_id, material_group)
            return func.HttpResponse(
                json.dumps(snap, default=str),
                mimetype="application/json",
                status_code=200,
            )
        # No snapshot yet — fall through to live
        logging.info("No snapshot found, falling back to live mode.")
        mode = "live"

    # ----------------------------------------------------------------
    # SHAREPOINT MODE — load directly from SharePoint
    # ----------------------------------------------------------------
    if mode == "sharepoint":
        try:
            from sharepoint_loader import load_current_previous_from_sharepoint, SharePointError
            current_rows, previous_rows = load_current_previous_from_sharepoint()
        except Exception as e:
            return _error(f"SharePoint load failed: {str(e)}", 500)
        snapshots_input = []

    # ----------------------------------------------------------------
    # LIVE MODE — rows provided in request body
    # ----------------------------------------------------------------
    else:
        current_rows: List[dict] = body.get("current_rows", [])
        previous_rows: List[dict] = body.get("previous_rows", [])
        snapshots_input: List[dict] = body.get("snapshots", [])
        if not current_rows:
            return _error("'current_rows' is required for live mode.", 400)

    # Analytics pipeline (shared by live + sharepoint)
    current_records = normalize_rows(current_rows, is_current=True)
    previous_records = normalize_rows(previous_rows, is_current=False)
    current_filtered = filter_records(current_records, location_id, material_group)
    previous_filtered = filter_records(previous_records, location_id, material_group)
    compared = compare_records(current_filtered, previous_filtered)

    trends = []
    if snapshots_input:
        trends = analyze_trends(snapshots_input, location_id, material_group, recurring_threshold)

    result = build_response(
        compared, trends, location_id, material_group,
        data_mode=mode,
    )

    return func.HttpResponse(
        json.dumps(result, default=str),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="daily-refresh", methods=["POST"])
def daily_refresh(req: func.HttpRequest) -> func.HttpResponse:
    """
    Manually triggers the daily SharePoint refresh and saves a snapshot.
    Useful for testing or on-demand cache refresh.
    """
    logging.info("Manual daily refresh triggered.")
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

@app.route(route="explain", methods=["POST"])
def explain(req: func.HttpRequest) -> func.HttpResponse:
    """
    Focused insight endpoint for Copilot Studio or UI drill-down.
    Accepts a question + analytics context, returns targeted explanation.
    Supports natural language query-driven filters.

    Request:
    {
      "question": "Why did forecast increase at LOC001?",
      "location_id": "LOC001",
      "material_group": "PUMP",
      "mode": "cached"  // or "live" with current_rows/previous_rows
    }
    """
    logging.info("Explain endpoint triggered.")
    try:
        body = req.get_json()
    except ValueError:
        return _error("Invalid JSON body.", 400)

    question: str = body.get("question", "Explain the current planning situation.")
    mode: str = body.get("mode", "cached").lower()
    location_id: Optional[str] = body.get("location_id")
    material_group: Optional[str] = body.get("material_group")

    # Get analytics context
    if mode == "cached":
        snap = load_snapshot()
        if not snap:
            return _error("No cached snapshot available. Run daily refresh first.", 404)
        # Return focused insight from snapshot
        return func.HttpResponse(
            json.dumps({
                "question": question,
                "aiInsight": snap.get("aiInsight"),
                "rootCause": snap.get("rootCause"),
                "recommendedActions": snap.get("recommendedActions"),
                "alerts": snap.get("alerts"),
                "drivers": snap.get("drivers"),
                "planningHealth": snap.get("planningHealth"),
                "dataMode": "cached",
                "lastRefreshedAt": snap.get("lastRefreshedAt"),
            }, default=str),
            mimetype="application/json",
            status_code=200,
        )

    # Live mode — run analytics then explain
    current_rows: List[dict] = body.get("current_rows", [])
    previous_rows: List[dict] = body.get("previous_rows", [])
    if not current_rows:
        return _error("'current_rows' required for live explain.", 400)

    current_records = normalize_rows(current_rows, is_current=True)
    previous_records = normalize_rows(previous_rows, is_current=False)
    current_filtered = filter_records(current_records, location_id, material_group)
    previous_filtered = filter_records(previous_records, location_id, material_group)
    compared = compare_records(current_filtered, previous_filtered)
    result = build_response(compared, [], location_id, material_group, data_mode="live")

    return func.HttpResponse(
        json.dumps({
            "question": question,
            "aiInsight": result.get("aiInsight"),
            "rootCause": result.get("rootCause"),
            "recommendedActions": result.get("recommendedActions"),
            "alerts": result.get("alerts"),
            "drivers": result.get("drivers"),
            "planningHealth": result.get("planningHealth"),
            "dataMode": "live",
        }, default=str),
        mimetype="application/json",
        status_code=200,
    )


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
