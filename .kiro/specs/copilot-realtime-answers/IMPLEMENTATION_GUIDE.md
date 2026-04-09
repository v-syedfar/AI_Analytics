# Implementation Guide - Copilot Real-Time Answers

## Overview

This guide shows the exact code changes needed to implement the Copilot Real-Time Answers improvement.

## File to Modify

**Primary File**: `planning_intelligence/function_app.py`

**Changes**:
1. Add new helper functions (before `explain()` function)
2. Update `explain()` function
3. Update `_generate_answer_from_context()` function
4. Add new answer template functions

## Step 1: Add New Helper Functions

Add these functions before the `explain()` function (around line 270):

### 1.1 Scope Extraction Function

```python
def _extract_scope(question: str) -> tuple:
    """
    Extract scope from question.
    
    Returns: (scope_type, scope_value)
    
    scope_type: "location" | "supplier" | "material_group" | "material_id" | "risk_type" | None
    scope_value: extracted entity name or ID
    """
    import re
    q = question.lower()
    
    # Location patterns
    loc_match = re.search(r'\b(LOC\d+|location\s+(\w+))\b', q, re.IGNORECASE)
    if loc_match:
        return ("location", loc_match.group(1).upper())
    
    # Supplier patterns
    sup_match = re.search(r'\b(supplier\s+(\w+)|SUP\d+)\b', q, re.IGNORECASE)
    if sup_match:
        return ("supplier", sup_match.group(1).upper())
    
    # Material group patterns
    mg_match = re.search(r'\b(material\s+group\s+(\w+)|category\s+(\w+))\b', q, re.IGNORECASE)
    if mg_match:
        return ("material_group", mg_match.group(1).upper())
    
    # Material ID patterns
    mat_match = re.search(r'\b(material\s+(\w+)|MAT\d+)\b', q, re.IGNORECASE)
    if mat_match:
        return ("material_id", mat_match.group(1).upper())
    
    # Risk type patterns
    if any(w in q for w in ["high risk", "low risk", "critical", "normal"]):
        return ("risk_type", None)
    
    return (None, None)
```

### 1.2 Answer Mode Determination Function

```python
def _determine_answer_mode(query_type: str, scope_type: str) -> str:
    """
    Determine if Summary or Investigate mode.
    
    Returns: "summary" | "investigate"
    """
    if query_type in ["comparison", "traceability"]:
        return "investigate"
    
    if query_type in ["root_cause", "why_not"] and scope_type:
        return "investigate"
    
    if scope_type and query_type not in ["summary", "provenance"]:
        return "investigate"
    
    return "summary"
```

### 1.3 Scoped Metrics Computation Function

```python
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
    # Filter records to scope
    if scope_type == "location":
        filtered = [r for r in detail_records if r.get("locationId") == scope_value]
    elif scope_type == "supplier":
        filtered = [r for r in detail_records if r.get("supplier") == scope_value]
    elif scope_type == "material_group":
        filtered = [r for r in detail_records if r.get("materialGroup") == scope_value]
    elif scope_type == "material_id":
        filtered = [r for r in detail_records if r.get("materialId") == scope_value]
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
```

## Step 2: Add Answer Template Functions

Add these functions before the `explain()` function:

### 2.1 Comparison Answer Template

```python
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
```

### 2.2 Root Cause Answer Template

```python
def _generate_root_cause_answer(question: str, ctx: dict, scope_type: str, scope_value: str, scoped_metrics: dict) -> str:
    """Generate root cause answer for specific entity."""
    if not scope_value:
        return "Could not identify specific entity in question."
    
    metrics = scoped_metrics or _compute_scoped_metrics(
        ctx.get("detailRecords", []), scope_type, scope_value
    )
    
    what_changed = metrics['scopedDrivers']['primary']
    change_rate = metrics['scopedMetrics']['changeRate']
    actions = ctx.get("recommendedActions", ["Monitor situation"])
    action = actions[0] if actions else "Monitor situation"
    
    return (
        f"In {scope_value}, {what_changed} changed. "
        f"This is risky because {change_rate}% of records changed "
        f"({metrics['scopedMetrics']['changedCount']}/{metrics['filteredRecordsCount']}). "
        f"Recommended action: {action}"
    )
```

### 2.3 Why-Not Answer Template

```python
def _generate_why_not_answer(question: str, ctx: dict, scope_type: str, scope_value: str, scoped_metrics: dict) -> str:
    """Generate why-not answer for stable entity."""
    if not scope_value:
        return "Could not identify specific entity in question."
    
    metrics = scoped_metrics or _compute_scoped_metrics(
        ctx.get("detailRecords", []), scope_type, scope_value
    )
    
    if metrics['scopedMetrics']['changedCount'] == 0:
        return f"{scope_value} is stable because no records changed this cycle."
    
    change_rate = metrics['scopedMetrics']['changeRate']
    if change_rate < 10:
        return f"{scope_value} is stable because only {change_rate}% of records changed."
    
    return f"{scope_value} has {change_rate}% change rate, which is below risk threshold."
```

### 2.4 Traceability Answer Template

```python
def _generate_traceability_answer(question: str, ctx: dict, scoped_metrics: dict) -> str:
    """Generate traceability answer with top contributing records."""
    records = scoped_metrics.get("topContributingRecords", []) if scoped_metrics else []
    if not records:
        return "No contributing records found."
    
    lines = [f"📊 Top {len(records)} contributing records (by forecast delta):"]
    for r in records:
        delta = r.get("qtyDelta", 0)
        delta_str = f"{delta:+,.0f}"
        lines.append(
            f"  {r.get('locationId', '?')} / {r.get('materialGroup', '?')} / "
            f"{r.get('materialId', '?')} — Δ{delta_str} [{r.get('changeType', '?')}] "
            f"[{r.get('riskLevel', '?')}]"
        )
    
    return "\n".join(lines)
```

## Step 3: Update `_generate_answer_from_context()` Function

Replace the existing function with this enhanced version:

```python
def _generate_answer_from_context(
    question: str,
    ctx: dict,
    answer_mode: str = "summary",
    scope_type: str = None,
    scope_value: str = None,
    scoped_metrics: dict = None
) -> str:
    """Generate answer based on mode and scope."""
    query_type = _classify_question(question)
    
    # Investigate mode routing
    if answer_mode == "investigate":
        if query_type == "comparison":
            return _generate_comparison_answer(question, ctx)
        elif query_type == "root_cause":
            return _generate_root_cause_answer(question, ctx, scope_type, scope_value, scoped_metrics)
        elif query_type == "why_not":
            return _generate_why_not_answer(question, ctx, scope_type, scope_value, scoped_metrics)
        elif query_type == "traceability":
            return _generate_traceability_answer(question, ctx, scoped_metrics)
    
    # Default: summary mode (existing logic)
    # ... keep existing summary answer generation code ...
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

    # ... rest of existing summary answer generation code ...
    # (keep all existing if/elif blocks for summary mode)
```

## Step 4: Update `explain()` Function

Replace the existing `explain()` function with this enhanced version:

```python
@app.route(route="explain", methods=["POST"])
def explain(req: func.HttpRequest) -> func.HttpResponse:
    """
    Focused insight endpoint with real-time, question-specific answers.
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

    # --- Context-grounded path ---
    if context:
        # NEW: Extract scope and determine answer mode
        scope_type, scope_value = _extract_scope(question)
        query_type = _classify_question(question)
        answer_mode = _determine_answer_mode(query_type, scope_type)
        
        # Compute scoped metrics if needed
        scoped_metrics = None
        if answer_mode == "investigate":
            scoped_metrics = _compute_scoped_metrics(
                context.get("detailRecords", []),
                scope_type,
                scope_value
            )
        
        # Generate answer with new logic
        answer = _generate_answer_from_context(
            question, context, answer_mode, scope_type, scope_value, scoped_metrics
        )
        
        context_used = [k for k, v in context.items() if v is not None]
        explainability = _build_explainability(context, question)
        
        response = {
            "question": question,
            "answer": answer,
            "queryType": query_type,
            "answerMode": answer_mode,
            "aiInsight": context.get("aiInsight"),
            "rootCause": context.get("rootCause"),
            "recommendedActions": context.get("recommendedActions", []),
            "planningHealth": context.get("planningHealth"),
            "dataMode": context.get("dataMode", "cached"),
            "lastRefreshedAt": context.get("lastRefreshedAt"),
            "supportingMetrics": {
                "changedRecordCount": context.get("changedRecordCount"),
                "totalRecords": context.get("totalRecords"),
                "trendDelta": context.get("trendDelta"),
                "planningHealth": context.get("planningHealth"),
            },
            "contextUsed": context_used,
            "explainability": explainability,
            "suggestedActions": _build_suggested_actions(question, context),
            "followUpQuestions": _build_follow_ups(question, context),
        }
        
        # Add investigate mode fields
        if answer_mode == "investigate" and scoped_metrics:
            response["investigateMode"] = {
                "filteredRecordsCount": scoped_metrics.get("filteredRecordsCount"),
                "scopedContributionBreakdown": scoped_metrics.get("scopedContributionBreakdown"),
                "scopedDrivers": scoped_metrics.get("scopedDrivers"),
                "topContributingRecords": scoped_metrics.get("topContributingRecords"),
                "scopeType": scope_type,
                "scopeValue": scope_value,
            }
        
        return func.HttpResponse(
            json.dumps(response, default=str),
            mimetype="application/json",
            status_code=200,
        )

    # --- Cached snapshot path ---
    snap = load_snapshot()
    if not snap:
        return _error("No cached snapshot available. Run daily-refresh to load data from Blob Storage.", 404)
    
    # NEW: Extract scope and determine answer mode
    scope_type, scope_value = _extract_scope(question)
    query_type = _classify_question(question)
    answer_mode = _determine_answer_mode(query_type, scope_type)
    
    # Compute scoped metrics if needed
    scoped_metrics = None
    if answer_mode == "investigate":
        scoped_metrics = _compute_scoped_metrics(
            snap.get("detailRecords", []),
            scope_type,
            scope_value
        )
    
    # Generate answer with new logic
    answer = _generate_answer_from_context(
        question, snap, answer_mode, scope_type, scope_value, scoped_metrics
    )
    
    explainability = _build_explainability(snap, question)
    
    response = {
        "question": question,
        "answer": answer,
        "queryType": query_type,
        "answerMode": answer_mode,
        "aiInsight": snap.get("aiInsight"),
        "rootCause": snap.get("rootCause"),
        "recommendedActions": snap.get("recommendedActions", []),
        "alerts": snap.get("alerts"),
        "drivers": snap.get("drivers"),
        "planningHealth": snap.get("planningHealth"),
        "dataMode": "blob",
        "lastRefreshedAt": snap.get("lastRefreshedAt"),
        "supportingMetrics": {
            "changedRecordCount": snap.get("changedRecordCount"),
            "totalRecords": snap.get("totalRecords"),
            "trendDelta": snap.get("trendDelta"),
            "planningHealth": snap.get("planningHealth"),
        },
        "contextUsed": ["aiInsight", "rootCause", "planningHealth", "drivers"],
        "explainability": explainability,
        "suggestedActions": _build_suggested_actions(question, snap),
        "followUpQuestions": _build_follow_ups(question, snap),
    }
    
    # Add investigate mode fields
    if answer_mode == "investigate" and scoped_metrics:
        response["investigateMode"] = {
            "filteredRecordsCount": scoped_metrics.get("filteredRecordsCount"),
            "scopedContributionBreakdown": scoped_metrics.get("scopedContributionBreakdown"),
            "scopedDrivers": scoped_metrics.get("scopedDrivers"),
            "topContributingRecords": scoped_metrics.get("topContributingRecords"),
            "scopeType": scope_type,
            "scopeValue": scope_value,
        }
    
    return func.HttpResponse(
        json.dumps(response, default=str),
        mimetype="application/json",
        status_code=200,
    )
```

## Summary of Changes

| Component | Change | Lines |
|-----------|--------|-------|
| New Functions | Add 4 helper functions | ~150 |
| New Templates | Add 4 answer template functions | ~100 |
| Update `_generate_answer_from_context()` | Add mode routing | ~20 |
| Update `explain()` | Add scope extraction and mode logic | ~50 |
| **Total** | | **~320 lines** |

## Testing Checklist

After implementing:

- [ ] Comparison questions return side-by-side metrics
- [ ] Root cause questions return entity-specific analysis
- [ ] Why-not questions return stability explanation
- [ ] Traceability questions return top records
- [ ] Summary questions still work (backward compatible)
- [ ] Response includes `investigateMode` fields
- [ ] Performance < 100ms for scoped computation
- [ ] All metrics traceable to detailRecords
- [ ] No breaking changes to API

## Deployment Notes

1. **Backward Compatible**: Existing clients continue to work
2. **New Fields**: `answerMode` and `investigateMode` are new (not replacing)
3. **Default Behavior**: Summary mode is default for unscoped questions
4. **No Data Changes**: Uses existing detailRecords, no new data sources
5. **Deterministic**: Same question + same data = same answer

---

**Implementation Status**: Ready to Code  
**Estimated Time**: 4-6 hours  
**Complexity**: Medium  
**Risk**: Low (additive changes, backward compatible)
