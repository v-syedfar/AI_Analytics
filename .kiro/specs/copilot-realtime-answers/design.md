# Copilot Real-Time Answers - Design

## Hybrid Architecture Overview

```
User Query
    ↓
Azure OpenAI (Intent + Entity Extraction)
    ├─ Classify intent (comparison, root_cause, why_not, etc.)
    ├─ Extract entities (LOCID, GSCEQUIPCAT, PRDID, LOCFR)
    └─ Identify missing context
    ↓
Context Validation
    ├─ Check if required context is available
    ├─ If missing → ClarificationEngine (interactive guidance)
    └─ If complete → Proceed to MCP
    ↓
MCP (Single Source of Truth)
    ├─ Query Context (intent, entities, selectedContext)
    ├─ Analytics Context (metrics, drivers, risk summary)
    ├─ Provenance (data source, freshness, blob files)
    ├─ SAP Schema (field dictionary, semantic mapping)
    └─ Domain Rules (composite key, design change logic)
    ↓
Deterministic Engine (ReasoningEngine)
    ├─ Record matching (current vs previous)
    ├─ Forecast delta, ROJ delta computation
    ├─ Supplier changes, design changes detection
    ├─ Aggregation by location, supplier, material group
    └─ Scoped metrics computation
    ↓
MCP (Final Structured Output)
    ├─ Decision
    ├─ Key Metrics
    ├─ Drivers (percentage breakdown)
    ├─ Risk Profile
    ├─ Actions (Top / Next / Monitor)
    └─ Traceability (top contributing records)
    ↓
Azure OpenAI (Response Generation)
    ├─ Convert structured output to natural language
    ├─ Validate against SAP schema (prevent hallucination)
    ├─ Generate conversational response
    └─ Include decision, metrics, drivers, risk, actions
    ↓
Response to UI
    ├─ Natural language answer
    ├─ Investigate mode fields (if scoped)
    ├─ Explainability (freshness, confidence)
    ├─ Suggested actions
    └─ Follow-up questions
```

## Core Principle: Deterministic Engine = Truth

- **MCP** = Context (structured data, schema, domain rules)
- **Azure OpenAI** = Intelligence layer (intent, entity extraction, response generation)
- **ReasoningEngine** = Computation (all metrics, aggregations, comparisons)
- **Never invert this relationship** - LLM must never compute metrics or access raw data

## Architecture Overview (Original - Investigate Mode)

```
User Question
    ↓
Classify Question Type
    ↓
Extract Scope (location, supplier, material group, etc.)
    ↓
Determine Answer Mode (Summary vs Investigate)
    ↓
Compute Scoped Metrics (if Investigate mode)
    ├─ Filter detailRecords to scope
    ├─ Recompute changed count, change rate, drivers
    ├─ Identify top contributing records
    └─ Build scoped breakdown
    ↓
Generate Answer (using appropriate template)
    ├─ Summary template
    ├─ Comparison template
    ├─ Root cause template
    ├─ Why-not template
    ├─ Traceability template
    └─ Action template
    ↓
Build Response (with investigate mode fields)
    ├─ answer (generated text)
    ├─ queryType (classification)
    ├─ filteredRecordsCount (if investigate)
    ├─ scopedContributionBreakdown (if investigate)
    ├─ scopedDrivers (if investigate)
    ├─ topContributingRecords (if investigate)
    ├─ comparisonMetrics (if comparison)
    ├─ explainability (freshness, confidence)
    └─ suggestedActions, followUpQuestions
    ↓
Return Response
```

## Core Components

### 0. Azure OpenAI Integration (NEW)

**Purpose**: Intelligent intent understanding and natural language response generation

```python
class AzureOpenAIIntegration:
    """
    Handles all Azure OpenAI interactions.
    
    CRITICAL: Only use for:
    - Intent classification
    - Entity extraction
    - Clarification prompts
    - Response generation
    
    NEVER use for:
    - Calculations
    - Aggregations
    - Accessing raw data
    """
    
    def extract_intent_and_entities(self, query: str) -> dict:
        """
        Use Azure OpenAI to extract intent and entities.
        
        Returns: {
            "intent": "comparison" | "root_cause" | "why_not" | "traceability" | "summary",
            "entities": {
                "LOCID": ["LOC001", "LOC002"],
                "GSCEQUIPCAT": ["UPS", "PUMP"],
                "PRDID": ["MAT-101"],
                "LOCFR": ["Supplier A"]
            },
            "missingContext": ["LOCID", "GSCEQUIPCAT"],
            "confidence": 0.95
        }
        """
        # Call Azure OpenAI with system prompt
        # System prompt includes SAP field dictionary and semantic mapping
        # Extract intent and entities from response
        pass
    
    def generate_clarification_prompt(self, missing_context: list, available_options: dict) -> str:
        """
        Generate natural language clarification prompt.
        
        Args:
            missing_context: ["LOCID", "GSCEQUIPCAT"]
            available_options: {
                "LOCID": ["LOC001", "LOC002", "LOC003"],
                "GSCEQUIPCAT": ["UPS", "PUMP", "VALVE"]
            }
        
        Returns: "Please select a location: LOC001, LOC002, or LOC003?"
        """
        pass
    
    def generate_response(self, structured_output: dict, mcp_context: dict) -> str:
        """
        Convert structured output to natural language response.
        
        Args:
            structured_output: {
                "decision": "Location LOC001 is risky",
                "keyMetrics": {"changedCount": 15, "changeRate": 45.5},
                "drivers": {"forecast": 60, "supplier": 30, "design": 10},
                "riskProfile": "High",
                "actions": ["Monitor forecast changes", "Contact supplier"]
            }
            mcp_context: Full MCP context with SAP schema
        
        Returns: Natural language response grounded in data
        """
        # Call Azure OpenAI with structured output
        # Include SAP schema in system prompt to prevent hallucination
        # Validate response against schema before returning
        pass
```

### 0.1: MCP Context Builder (NEW)

**Purpose**: Build complete MCP context with schema and domain rules

```python
class MCPContextBuilder:
    """
    Builds complete MCP context for all queries.
    
    MCP = Single Source of Truth
    """
    
    def build_mcp_context(self, analytics_data: dict, detail_records: list) -> dict:
        """
        Build complete MCP context.
        
        Returns: {
            "queryContext": {
                "intent": "comparison",
                "entities": {"LOCID": ["LOC001", "LOC002"]},
                "selectedContext": {...}
            },
            "analyticsContext": {
                "planningHealth": "Critical",
                "forecastNew": 1000,
                "forecastOld": 800,
                "trendDelta": 200,
                "changedRecordCount": 15,
                "totalRecords": 33,
                "drivers": {"forecast": 60, "supplier": 30, "design": 10},
                "riskSummary": {...},
                "supplierSummary": {...},
                "materialGroupSummary": {...},
                "datacenterSummary": {...},
                "detailRecords": [...]
            },
            "provenance": {
                "dataSource": "Blob",
                "lastRefreshedAt": "2026-04-09T03:00:00Z",
                "blobFileNamesUsed": ["data_2026_04_09.csv"],
                "recordsAnalyzed": 1000
            },
            "sapSchema": {
                "fieldDictionary": {...},
                "semanticMapping": {...},
                "domainRules": {...}
            }
        }
        """
        pass
    
    def get_sap_field_dictionary(self) -> dict:
        """
        Return complete SAP field dictionary.
        """
        return {
            "LOCID": "Location ID",
            "PRDID": "Material ID",
            "GSCEQUIPCAT": "Material Group",
            "GSCPREVFCSTQTY": "Previous Forecast",
            "GSCFSCTQTY": "Current Forecast",
            "FCST_Delta Qty": "Forecast Change",
            "GSCPREVROJNBD": "Previous ROJ",
            "GSCCONROJDATE": "Current ROJ",
            "NBD_DeltaDays": "ROJ Shift",
            "LOCFR": "Supplier",
            "GSCPREVSUPLDATE": "Previous Supplier Date",
            "GSCSUPLDATE": "Current Supplier Date",
            "Is_SupplierDateMissing": "Supplier Missing Flag",
            "ZCOIBODVER": "BOD Version",
            "ZCOIFORMFACT": "Form Factor",
            "Is_New Demand": "New Demand",
            "Is_cancelled": "Cancelled",
            "Risk_Flag": "Risk"
        }
    
    def get_semantic_mapping(self) -> dict:
        """
        Return semantic mapping for domain logic.
        """
        return {
            "forecast_change": "GSCFSCTQTY - GSCPREVFCSTQTY",
            "design_change": "ZCOIBODVER changed OR ZCOIFORMFACT changed",
            "supplier_issue": "GSCSUPLDATE changed OR Is_SupplierDateMissing",
            "schedule_issue": "NBD_DeltaDays > 0"
        }
    
    def get_domain_rules(self) -> dict:
        """
        Return domain rules for SAP logic.
        """
        return {
            "compositeKey": ["LOCID", "GSCEQUIPCAT", "PRDID"],
            "designChangeLogic": {
                "TRUE_IF": ["ZCOIBODVER changed", "ZCOIFORMFACT changed"],
                "EXCLUDE": ["Is_New Demand", "Is_cancelled"]
            },
            "supplierGrouping": "LOCFR"
        }
```

### 1. Question Classification (Enhanced)

**Current**: Classifies into 7 types (comparison, why_not, traceability, root_cause, risk, action, provenance, summary)

**Enhancement**: Add scope extraction

```python
def _classify_question_and_extract_scope(question: str) -> tuple:
    """
    Returns: (query_type, scope_type, scope_value)
    
    scope_type: "location" | "supplier" | "material_group" | "material_id" | "risk_type" | None
    scope_value: extracted entity name or ID
    """
    # Existing classification logic
    query_type = _classify_question(question)
    
    # NEW: Extract scope
    scope_type, scope_value = _extract_scope(question)
    
    return query_type, scope_type, scope_value
```

### 2. Scope Extraction

**New function**: Extract entity mentions from question

```python
def _extract_scope(question: str) -> tuple:
    """
    Extract scope from question.
    
    Returns: (scope_type, scope_value)
    
    Examples:
    - "Why is LOC001 risky?" → ("location", "LOC001")
    - "Compare LOC001 vs LOC002" → ("location", ["LOC001", "LOC002"])
    - "Which supplier has design changes?" → ("supplier", None)  # generic
    - "Show top records" → (None, None)  # no scope
    """
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

### 3. Answer Mode Determination

**New logic**: Determine if Summary or Investigate mode

```python
def _determine_answer_mode(query_type: str, scope_type: str) -> str:
    """
    Returns: "summary" | "investigate"
    
    Investigate mode for:
    - comparison (always)
    - root_cause (if scoped)
    - why_not (if scoped)
    - traceability (always)
    - entity-specific questions (if scoped)
    """
    if query_type in ["comparison", "traceability"]:
        return "investigate"
    
    if query_type in ["root_cause", "why_not"] and scope_type:
        return "investigate"
    
    if scope_type and query_type not in ["summary", "provenance"]:
        return "investigate"
    
    return "summary"
```

### 4. Scoped Metrics Computation

**New function**: Compute metrics for specific scope

```python
def _compute_scoped_metrics(
    detail_records: list,
    scope_type: str,
    scope_value: str,
    global_metrics: dict
) -> dict:
    """
    Filter detailRecords to scope and recompute metrics.
    
    Returns: {
        "filteredRecordsCount": int,
        "scopedContributionBreakdown": {...},
        "scopedDrivers": {...},
        "topContributingRecords": [...],
        "scopedMetrics": {
            "changedCount": int,
            "changeRate": float,
            "riskDistribution": {...},
            ...
        }
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
        # Filter by risk level
        filtered = [r for r in detail_records if r.get("riskLevel") == scope_value]
    else:
        filtered = detail_records
    
    # Recompute metrics for filtered records
    changed_count = sum(1 for r in filtered if r.get("changed"))
    total_count = len(filtered)
    change_rate = round(changed_count / max(total_count, 1) * 100, 1)
    
    # Compute contribution breakdown
    qty_changed = sum(1 for r in filtered if r.get("qtyChanged"))
    supplier_changed = sum(1 for r in filtered if r.get("supplierChanged"))
    design_changed = sum(1 for r in filtered if r.get("designChanged"))
    schedule_changed = sum(1 for r in filtered if r.get("scheduleChanged"))
    
    contribution = {
        "quantity": round(qty_changed / max(changed_count, 1) * 100, 1),
        "supplier": round(supplier_changed / max(changed_count, 1) * 100, 1),
        "design": round(design_changed / max(changed_count, 1) * 100, 1),
        "schedule": round(schedule_changed / max(changed_count, 1) * 100, 1),
    }
    
    # Identify top drivers
    drivers = {
        "primary": max(
            [("quantity", qty_changed), ("supplier", supplier_changed), 
             ("design", design_changed), ("schedule", schedule_changed)],
            key=lambda x: x[1]
        )[0],
        "changedCount": changed_count,
        "totalCount": total_count,
    }
    
    # Top contributing records (by absolute delta)
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

### 5. Answer Generation (Enhanced)

**Current**: Single `_generate_answer_from_context` function

**Enhancement**: Add mode-specific generation

```python
def _generate_answer_from_context(
    question: str,
    ctx: dict,
    answer_mode: str = "summary",
    scope_type: str = None,
    scope_value: str = None,
    scoped_metrics: dict = None
) -> str:
    """
    Generate answer based on mode and scope.
    
    answer_mode: "summary" | "investigate"
    """
    query_type = _classify_question(question)
    
    if answer_mode == "investigate":
        if query_type == "comparison":
            return _generate_comparison_answer(question, ctx, scoped_metrics)
        elif query_type == "root_cause":
            return _generate_root_cause_answer(question, ctx, scope_type, scope_value, scoped_metrics)
        elif query_type == "why_not":
            return _generate_why_not_answer(question, ctx, scope_type, scope_value, scoped_metrics)
        elif query_type == "traceability":
            return _generate_traceability_answer(question, ctx, scoped_metrics)
    
    # Default: summary mode (existing logic)
    return _generate_summary_answer(question, ctx)
```

### 6. Answer Templates

**New functions**: Template-specific answer generation

```python
def _generate_comparison_answer(question: str, ctx: dict, scoped_metrics: dict) -> str:
    """
    Template: 📊 [Entity A] vs [Entity B]
    [Entity A]: X changed (Y%), drivers: [list]
    [Entity B]: X changed (Y%), drivers: [list]
    → [Entity A] has more changes
    """
    # Extract two entities
    entities = _extract_comparison_entities(question)
    if len(entities) != 2:
        return "Could not extract two entities to compare."
    
    entity_a, entity_b = entities
    
    # Compute metrics for each
    metrics_a = _compute_scoped_metrics(ctx.get("detailRecords", []), "location", entity_a, ctx)
    metrics_b = _compute_scoped_metrics(ctx.get("detailRecords", []), "location", entity_b, ctx)
    
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
    """
    Template: In [entity], [what changed]. This is risky because [why]. [Action]
    """
    if not scope_value:
        return "Could not identify specific entity in question."
    
    metrics = scoped_metrics or _compute_scoped_metrics(
        ctx.get("detailRecords", []), scope_type, scope_value, ctx
    )
    
    what_changed = metrics['scopedDrivers']['primary']
    why_risky = f"{metrics['scopedMetrics']['changeRate']}% of records changed"
    action = ctx.get("recommendedActions", ["Monitor situation"])[0]
    
    return (
        f"In {scope_value}, {what_changed} changed. "
        f"This is risky because {why_risky}. "
        f"Recommended action: {action}"
    )

def _generate_why_not_answer(question: str, ctx: dict, scope_type: str, scope_value: str, scoped_metrics: dict) -> str:
    """
    Template: [Entity] is stable because [reasons]. Unlike [risky entity], [differences]
    """
    if not scope_value:
        return "Could not identify specific entity in question."
    
    metrics = scoped_metrics or _compute_scoped_metrics(
        ctx.get("detailRecords", []), scope_type, scope_value, ctx
    )
    
    if metrics['scopedMetrics']['changedCount'] == 0:
        return f"{scope_value} is stable because no records changed this cycle."
    
    change_rate = metrics['scopedMetrics']['changeRate']
    if change_rate < 10:
        return f"{scope_value} is stable because only {change_rate}% of records changed."
    
    return f"{scope_value} has {change_rate}% change rate, which is below risk threshold."

def _generate_traceability_answer(question: str, ctx: dict, scoped_metrics: dict) -> str:
    """
    Template: 📊 Top [N] contributing records:
    [Record 1]: [location] / [material] / Δ[delta] / [risk]
    ...
    """
    records = scoped_metrics.get("topContributingRecords", [])
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

### 7. Response Building (Enhanced)

**Current**: Single response structure

**Enhancement**: Add investigate mode fields

```python
def _build_explain_response(
    question: str,
    ctx: dict,
    answer_mode: str = "summary",
    scope_type: str = None,
    scope_value: str = None,
    scoped_metrics: dict = None
) -> dict:
    """
    Build explain response with investigate mode fields.
    """
    query_type = _classify_question(question)
    answer = _generate_answer_from_context(
        question, ctx, answer_mode, scope_type, scope_value, scoped_metrics
    )
    
    response = {
        "question": question,
        "answer": answer,
        "queryType": query_type,
        "answerMode": answer_mode,
        "aiInsight": ctx.get("aiInsight"),
        "rootCause": ctx.get("rootCause"),
        "recommendedActions": ctx.get("recommendedActions", []),
        "planningHealth": ctx.get("planningHealth"),
        "dataMode": ctx.get("dataMode", "cached"),
        "lastRefreshedAt": ctx.get("lastRefreshedAt"),
        "supportingMetrics": {
            "changedRecordCount": ctx.get("changedRecordCount"),
            "totalRecords": ctx.get("totalRecords"),
            "trendDelta": ctx.get("trendDelta"),
            "planningHealth": ctx.get("planningHealth"),
        },
        "explainability": _build_explainability(ctx, question),
        "suggestedActions": _build_suggested_actions(question, ctx),
        "followUpQuestions": _build_follow_ups(question, ctx),
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
        
        if query_type == "comparison":
            response["investigateMode"]["comparisonMetrics"] = scoped_metrics.get("comparisonMetrics")
    
    return response
```

## Data Flow

### Example 1: Comparison Question

```
Question: "Compare LOC001 vs LOC002"
    ↓
Classification: query_type="comparison", scope_type="location", scope_value=["LOC001", "LOC002"]
    ↓
Answer Mode: "investigate" (comparison always investigates)
    ↓
Scoped Metrics:
    - Filter detailRecords to LOC001 records
    - Compute: changed count, change rate, drivers
    - Filter detailRecords to LOC002 records
    - Compute: changed count, change rate, drivers
    ↓
Answer Generation:
    - Use comparison template
    - Show side-by-side metrics
    - Highlight differences
    ↓
Response:
    - answer: "📊 Comparison: LOC001 vs LOC002..."
    - investigateMode: {filteredRecordsCount, scopedDrivers, comparisonMetrics}
    - explainability: {confidence, freshness}
```

### Example 2: Root Cause Question

```
Question: "Why is LOC001 risky?"
    ↓
Classification: query_type="root_cause", scope_type="location", scope_value="LOC001"
    ↓
Answer Mode: "investigate" (root_cause with scope)
    ↓
Scoped Metrics:
    - Filter detailRecords to LOC001 records
    - Compute: changed count, change rate, drivers, risk distribution
    ↓
Answer Generation:
    - Use root cause template
    - Explain what changed in LOC001
    - Explain why it's risky
    - Suggest action
    ↓
Response:
    - answer: "In LOC001, [what changed]. This is risky because [why]..."
    - investigateMode: {filteredRecordsCount, scopedDrivers, topContributingRecords}
    - explainability: {confidence, freshness}
```

## Implementation Strategy

### Phase 1: Core Functions
1. Implement `_extract_scope()`
2. Implement `_determine_answer_mode()`
3. Implement `_compute_scoped_metrics()`

### Phase 2: Answer Templates
1. Implement `_generate_comparison_answer()`
2. Implement `_generate_root_cause_answer()`
3. Implement `_generate_why_not_answer()`
4. Implement `_generate_traceability_answer()`

### Phase 3: Integration
1. Update `_generate_answer_from_context()` to use new functions
2. Update `explain()` endpoint to use new response builder
3. Add investigate mode fields to response

### Phase 4: Testing
1. Unit tests for scope extraction
2. Unit tests for scoped metrics computation
3. Integration tests for each answer template
4. End-to-end tests for full flow

## Backward Compatibility

- Existing API contract unchanged
- New fields added to response (not replacing)
- Existing clients continue to work
- Summary mode is default for unscoped questions
- Investigate mode is opt-in (triggered by scope detection)

## Performance Considerations

- Scoped metrics computation: O(n) where n = detailRecords count
- Expected: < 100ms for typical datasets (1000-10000 records)
- No additional API calls
- Uses existing detailRecords, no data reload

## Error Handling

- If scope extraction fails: Fall back to summary mode
- If scoped metrics computation fails: Use global metrics
- If answer generation fails: Return generic answer
- All errors logged for debugging
