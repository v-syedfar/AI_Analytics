# Copilot Real-Time Answers - Requirements

## Problem Statement

Current Copilot answers feel precomputed, generic, and repetitive. Even when grounded in real data, they don't feel like dynamic analysis. Users perceive answers as dashboard summaries rather than targeted responses to their specific questions. Additionally, the system lacks intelligent understanding of user intent and cannot guide users through incomplete queries.

### Current Issues
- Answers use global dashboard metrics regardless of question specificity
- Comparison prompts fall back to global summary instead of computing side-by-side metrics
- Root cause and why-not prompts don't filter to relevant scope
- All answer templates sound similar, lacking variety
- No distinction between data freshness and answer specificity
- Traceability prompts don't compute scoped metrics
- System cannot understand user intent or extract entities intelligently
- No interactive guidance when user queries lack required context
- LLM is not integrated for natural language understanding and response generation
- MCP is not used as single source of truth for context and schema

## Goals

1. **Make answers feel real-time** - Compute metrics specifically for each question
2. **Improve specificity** - Filter and recalculate for scoped entities (location, supplier, material group)
3. **Vary response style** - Different templates for different question types
4. **Maintain determinism** - Keep analytics as source of truth, no invented numbers
5. **Preserve trust** - Keep provenance visible, distinguish data freshness from answer quality
6. **Add intelligent intent understanding** - Use Azure OpenAI to classify intent and extract entities
7. **Enable interactive guidance** - Guide users through incomplete queries with data-driven options
8. **Implement hybrid architecture** - Use MCP as single source of truth, Azure OpenAI for intelligence layer
9. **Enforce SAP domain logic** - Prevent hallucination by validating against SAP schema
10. **Generate conversational responses** - Use Azure OpenAI to create natural language responses grounded in deterministic analysis

## User Stories

### Story 1: Comparison Analysis
**As a** planner  
**I want to** compare two locations side-by-side  
**So that** I can see specific differences, not just global metrics

**Acceptance Criteria:**
- When asking "Compare LOC001 vs LOC002", system computes metrics for each location
- Answer shows side-by-side comparison (not global summary)
- Answer includes: changed count, change rate, top drivers for each location
- Answer feels like fresh analysis, not precomputed

### Story 2: Root Cause Analysis
**As a** planner  
**I want to** understand why a specific location is risky  
**So that** I can take targeted action

**Acceptance Criteria:**
- When asking "Why is LOC001 risky?", system filters to LOC001 records
- Answer shows LOC001-specific metrics (not global)
- Answer explains: what changed, why it's risky, what to do
- Answer feels targeted to LOC001, not generic

### Story 3: Why-Not Reasoning
**As a** planner  
**I want to** understand why something is NOT risky  
**So that** I can trust the analysis

**Acceptance Criteria:**
- When asking "Why is LOC001 not risky?", system explains LOC001-specific reasons
- Answer shows: what didn't change, why it's stable, what's different from risky locations
- Answer feels like analysis, not just "no risk detected"

### Story 4: Supplier Analysis
**As a** planner  
**I want to** know which supplier has frequent design changes  
**So that** I can manage supplier relationships

**Acceptance Criteria:**
- When asking about supplier design changes, system filters to supplier records
- Answer shows: supplier-specific design change rate, affected materials, trend
- Answer feels like supplier-specific analysis

### Story 5: Traceability
**As a** planner  
**I want to** see top contributing records  
**So that** I can drill into details

**Acceptance Criteria:**
- When asking "Show top contributing records", system returns scoped records
- Answer shows: top 5 records with highest impact, sorted by delta
- Answer includes: location, material, change type, risk level
- Answer feels like targeted drill-down, not generic list

### Story 6: Intelligent Intent Understanding
**As a** planner  
**I want to** ask questions in natural language  
**So that** I don't need to learn special syntax

**Acceptance Criteria:**
- System understands various phrasings of the same question
- System extracts entities (locations, suppliers, materials) automatically
- System classifies intent (comparison, root cause, why-not, etc.)
- System responds with natural language, not templated text

### Story 7: Interactive Guidance for Incomplete Queries
**As a** planner  
**I want to** get guided through incomplete queries  
**So that** I can provide necessary context step-by-step

**Acceptance Criteria:**
- When query lacks required context, system asks for it
- System provides data-driven options (from actual data, not hardcoded)
- System remembers my selections across conversation turns
- System only proceeds to analysis after context is complete

### Story 8: Conversational Responses
**As a** planner  
**I want to** receive responses that feel like talking to an analyst  
**So that** I trust the insights and feel engaged

**Acceptance Criteria:**
- Responses are natural language, not bullet points
- Responses include decision, key metrics, drivers, risk profile, actions
- Responses are grounded in data (no hallucination)
- Responses feel intelligent and enterprise-grade

## Functional Requirements

### FR1: Query-Specific Computation
- For each question, identify scope (location, supplier, material group, material ID, risk type)
- Filter detailRecords to scope
- Recompute metrics for scoped records
- Answer from scoped metrics, not global

### FR2: Answer Modes
- **Summary Mode**: For overall questions (default)
- **Investigate Mode**: For comparison, root cause, why-not, entity-specific, traceability
- Each mode has different computation and response template

### FR3: Scoped Recalculation
When question mentions specific entity:
- Filter detailRecords to matching records
- Recompute: changed count, change rate, drivers, risk distribution
- Include: filteredRecordsCount, scopedContributionBreakdown, scopedDrivers, topContributingRecords

### FR4: Comparison Responses
- Extract two entities from question (e.g., "LOC001" vs "LOC002")
- Compute metrics for each entity separately
- Generate side-by-side comparison (not global summary)
- Show: changed count, change rate, top drivers, risk level for each

### FR5: Root Cause Responses
- Extract entity from question
- Filter to entity records
- Compute: what changed, why it changed, impact
- Answer: "In [entity], [what changed]. This is risky because [why]. [Recommended action]."

### FR6: Why-Not Responses
- Extract entity from question
- Filter to entity records
- Compute: what didn't change, why it's stable, comparison to risky entities
- Answer: "[Entity] is stable because [reasons]. Unlike [risky entity], [differences]."

### FR7: Response Shaping
- Summary: "Planning health is X. Y% changed. Risk: Z."
- Comparison: "📊 [Entity A] vs [Entity B]: [metrics side-by-side]"
- Root Cause: "In [entity], [what changed]. This is risky because [why]. [Action]."
- Why-Not: "[Entity] is stable because [reasons]. [Comparison to risky]."
- Traceability: "📊 Top [N] contributing records: [list with metrics]"

### FR8: Freshness Awareness
- Distinguish: data freshness vs answer specificity
- If data > 24h old: "⚠️ Data is 2 days old. Analysis based on [date]."
- If data fresh: "✅ Analysis based on latest data ([time] ago)."
- Stale data warning should not replace targeted analysis

### FR9: Investigate Mode Fields
Response includes:
- `filteredRecordsCount`: How many records matched the scope
- `scopedContributionBreakdown`: Breakdown for scoped records only
- `scopedDrivers`: Top drivers for scoped records
- `topContributingRecords`: Top 5 records by impact in scope
- `comparisonMetrics`: If applicable (for comparison questions)

### FR10: Azure OpenAI Integration (Intent & Entity Extraction)
- Use Azure OpenAI ONLY for:
  - Intent classification (what type of question is this?)
  - Entity extraction (what entities are mentioned?)
  - Clarification prompts (what context is missing?)
  - Natural language response generation (how to phrase the answer?)
- DO NOT use Azure OpenAI for:
  - Calculations or aggregations
  - Accessing raw blob data
  - Computing metrics
  - Making business decisions

### FR11: MCP as Single Source of Truth
- MCP must provide complete context including:
  - **Query Context**: intent, entities (LOCID, GSCEQUIPCAT, PRDID, LOCFR), selectedContext
  - **Analytics Context**: planningHealth, forecastNew/Old, trendDelta, changedRecordCount, totalRecords, drivers, riskSummary, supplierSummary, materialGroupSummary, datacenterSummary, detailRecords (filtered)
  - **Provenance**: dataSource, lastRefreshedAt, blobFileNamesUsed, recordsAnalyzed
  - **SAP Schema**: sapFieldDictionary with all valid SAP fields and their meanings
  - **Semantic Mapping**: forecast_change, design_change, supplier_issue, schedule_issue definitions

### FR12: SAP Field Dictionary (Mandatory)
MCP must include complete SAP field dictionary:
- LOCID: Location ID
- PRDID: Material ID
- GSCEQUIPCAT: Material Group
- GSCPREVFCSTQTY: Previous Forecast
- GSCFSCTQTY: Current Forecast
- FCST_Delta Qty: Forecast Change
- GSCPREVROJNBD: Previous ROJ
- GSCCONROJDATE: Current ROJ
- NBD_DeltaDays: ROJ Shift
- LOCFR: Supplier
- GSCPREVSUPLDATE: Previous Supplier Date
- GSCSUPLDATE: Current Supplier Date
- Is_SupplierDateMissing: Supplier Missing Flag
- ZCOIBODVER: BOD Version
- ZCOIFORMFACT: Form Factor
- Is_New Demand: New Demand
- Is_cancelled: Cancelled
- Risk_Flag: Risk

### FR13: Semantic Mapping (Mandatory)
MCP must include semantic mapping for domain logic:
- forecast_change: "GSCFSCTQTY - GSCPREVFCSTQTY"
- design_change: "ZCOIBODVER changed OR ZCOIFORMFACT changed"
- supplier_issue: "GSCSUPLDATE changed OR Is_SupplierDateMissing"
- schedule_issue: "NBD_DeltaDays > 0"

### FR14: Domain Rules (Strict)
- Composite Key: (LOCID, GSCEQUIPCAT, PRDID)
- Design Change: TRUE only if BOD change OR Form Factor change (exclude new demand, cancelled)
- Supplier grouping: LOCFR
- All computations must follow SAP domain rules strictly

### FR15: Hybrid Architecture Flow
Strict flow for all queries:
1. User Query → Azure OpenAI (intent + entity extraction)
2. Context validation (check missing inputs)
3. MCP (structured context + SAP schema)
4. Deterministic Engine (compute results)
5. MCP (final structured output)
6. Azure OpenAI (response generation)
7. UI (display response)

### FR16: Interactive Clarification
When required context is missing:
- Detect missing context using ClarificationEngine
- Generate data-driven options from actual detailRecords
- Present options to user (never hardcoded values)
- Track selectedContext across conversation turns
- Only proceed to reasoning after context is complete

### FR17: Validation Guardrails
Before final response:
- Verify fields are valid SAP fields
- Verify numbers exist in MCP context
- Prevent hallucination by validating against schema
- If invalid: regenerate response or return error

### FR18: Response Rules (Strict)
- NEVER fallback to global summary for scoped query
- NEVER show "Unknown" supplier if LOCFR exists
- NEVER output null if data exists
- ALWAYS use MCP context
- ALWAYS show decision, key metrics, drivers, risk profile, actions

## Non-Functional Requirements

### NR1: Determinism
- All metrics computed from detailRecords
- No invented numbers
- Provenance always visible
- Same question always produces same answer (given same data)

### NR2: Performance
- Scoped recalculation should be fast (< 100ms)
- No additional API calls
- Use existing detailRecords, don't reload data

### NR3: Backward Compatibility
- Existing API contract unchanged
- New fields added to response (not replacing existing)
- Existing clients continue to work

### NR4: Trustworthiness
- Answer always cites source (dashboard context or blob data)
- Confidence score reflects data availability
- Explainability shows which fields were used

## Acceptance Criteria

### AC1: Comparison Prompts
- "Compare LOC001 vs LOC002" → Side-by-side metrics, not global summary
- "Which supplier is failing ROJ?" → Supplier-specific metrics, not global
- Answer includes: entity-specific changed count, change rate, drivers

### AC2: Root Cause Prompts
- "Why is planning health critical?" → Scoped analysis if entity mentioned
- "Why is LOC001 risky?" → LOC001-specific metrics and explanation
- Answer feels targeted, not generic

### AC3: Why-Not Prompts
- "Why is LOC001 not risky?" → LOC001-specific reasons
- "Why is this supplier not failing?" → Supplier-specific analysis
- Answer explains stability, not just "no risk detected"

### AC4: Traceability Prompts
- "Show top contributing records" → Top 5 records with scoped metrics
- "Which materials are impacted?" → Material-specific list with metrics
- Answer includes: location, material, change type, delta, risk level

### AC5: Response Variety
- Comparison answers use different template than summary
- Root cause answers use different template than comparison
- Why-not answers use different template than root cause
- No two answer types sound identical

### AC6: Freshness Awareness
- If data stale: Answer includes freshness warning
- If data fresh: Answer includes freshness confirmation
- Warning doesn't replace analysis

### AC7: Determinism
- Same question + same data = same answer
- All metrics traceable to detailRecords
- No randomness or LLM-based variation

## Testing Strategy

### Test Categories

1. **Comparison Tests**
   - Compare two locations
   - Compare two suppliers
   - Compare two material groups
   - Verify side-by-side metrics, not global

2. **Root Cause Tests**
   - Why is location risky?
   - Why is supplier failing?
   - Why is material group impacted?
   - Verify scoped metrics, targeted explanation

3. **Why-Not Tests**
   - Why is location not risky?
   - Why is supplier not failing?
   - Why is material group stable?
   - Verify stability explanation, comparison to risky

4. **Traceability Tests**
   - Show top contributing records
   - Show impacted materials
   - Show affected suppliers
   - Verify scoped records, sorted by impact

5. **Response Variety Tests**
   - Verify comparison answers differ from summary
   - Verify root cause answers differ from comparison
   - Verify why-not answers differ from root cause
   - Verify no template reuse

6. **Freshness Tests**
   - Fresh data: Verify freshness confirmation
   - Stale data: Verify freshness warning
   - Verify warning doesn't replace analysis

7. **Determinism Tests**
   - Same question twice: Same answer
   - Different data: Different answer
   - Verify no randomness

## Success Metrics

1. **Specificity**: 100% of comparison prompts use scoped metrics
2. **Variety**: 100% of answer types have unique templates
3. **Freshness**: 100% of responses include freshness awareness
4. **Determinism**: 100% of answers deterministic (same input = same output)
5. **Trust**: 100% of metrics traceable to source
6. **Performance**: Scoped recalculation < 100ms
7. **User Perception**: Answers feel targeted, not generic (qualitative)

## Out of Scope

- Changing API contract (only adding fields)
- Rewriting analytics engine
- Adding LLM-based answer generation
- Changing dashboard summary computation
- Modifying detailRecords structure
