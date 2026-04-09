# Copilot Real-Time Answers - API Documentation

## Overview

The Copilot Real-Time Answers feature enhances the `/explain` endpoint to provide question-specific, dynamic answers instead of generic summaries. The system intelligently extracts scope from questions, determines the appropriate answer mode, and generates targeted responses.

## Endpoint: `/explain`

### Request

```json
{
  "question": "Why is LOC001 risky?",
  "location_id": "optional_location_filter",
  "material_group": "optional_material_group_filter",
  "context": {
    "detailRecords": [...],
    "planningHealth": 65,
    "changedRecordCount": 245,
    "totalRecords": 700,
    "aiInsight": "...",
    "rootCause": "...",
    "recommendedActions": [...],
    "drivers": {...},
    "riskSummary": {...},
    "contributionBreakdown": {...},
    "kpis": {...},
    "datacenterSummary": [...],
    "materialGroupSummary": [...],
    "lastRefreshedAt": "2026-04-05T10:30:00Z",
    "dataMode": "cached"
  }
}
```

### Response

```json
{
  "question": "Why is LOC001 risky?",
  "answer": "In LOC001, design changed. This is risky because 37.5% of records changed (45/120). Recommended action: Review design change impact on schedule.",
  "queryType": "root_cause",
  "answerMode": "investigate",
  "aiInsight": "Design changes are driving risk",
  "rootCause": "Supplier changed design specs",
  "recommendedActions": ["Review design changes", "Monitor supplier"],
  "planningHealth": 65,
  "dataMode": "cached",
  "lastRefreshedAt": "2026-04-05T10:30:00Z",
  "supportingMetrics": {
    "changedRecordCount": 245,
    "totalRecords": 700,
    "trendDelta": 1500,
    "planningHealth": 65
  },
  "contextUsed": ["detailRecords", "aiInsight", "rootCause", "recommendedActions"],
  "explainability": {
    "confidenceScore": 85,
    "dataCoverage": 35.0,
    "dataSource": "cached",
    "lastRefreshedAt": "2026-04-05T10:30:00Z",
    "dataFreshnessMinutes": 45.0,
    "isStale": false,
    "queryType": "root_cause",
    "fieldsUsed": ["detailRecords", "aiInsight", "rootCause", "recommendedActions"]
  },
  "suggestedActions": [
    {
      "action": "open_drill_down",
      "label": "Review design changes",
      "type": "material"
    }
  ],
  "followUpQuestions": [
    "What changed most?",
    "Show KPI summary",
    "What should the planner do next?"
  ],
  "investigateMode": {
    "filteredRecordsCount": 120,
    "scopedContributionBreakdown": {
      "quantity": 25.0,
      "supplier": 35.0,
      "design": 35.0,
      "schedule": 5.0
    },
    "scopedDrivers": {
      "primary": "design",
      "changedCount": 45,
      "totalCount": 120
    },
    "topContributingRecords": [
      {
        "locationId": "LOC001",
        "materialGroup": "Electronics",
        "materialId": "MAT001",
        "qtyDelta": 500,
        "changeType": "Qty Increase",
        "riskLevel": "High Risk"
      }
    ],
    "scopeType": "location",
    "scopeValue": "LOC001"
  }
}
```

## Scope Extraction

The system automatically extracts scope from questions using pattern matching.

### Supported Scope Types

#### Location
- **Pattern**: `LOC001`, `location Boston`, `site Seattle`
- **Example**: "Why is LOC001 risky?"
- **Extracted**: `scope_type="location"`, `scope_value="LOC001"`

#### Supplier
- **Pattern**: `SUP001`, `supplier Acme`, `vendor XYZ`
- **Example**: "Which supplier SUP001 has design changes?"
- **Extracted**: `scope_type="supplier"`, `scope_value="SUP001"`

#### Material Group
- **Pattern**: `material group Electronics`, `category Mechanical`
- **Example**: "Which material group Electronics has changes?"
- **Extracted**: `scope_type="material_group"`, `scope_value="ELECTRONICS"`

#### Material ID
- **Pattern**: `MAT001`, `material MAT001`
- **Example**: "Show material MAT001 details"
- **Extracted**: `scope_type="material_id"`, `scope_value="MAT001"`

#### Risk Type
- **Pattern**: `high risk`, `low risk`, `critical`, `normal`
- **Example**: "Show high risk records"
- **Extracted**: `scope_type="risk_type"`, `scope_value=None`

### No Scope
- **Example**: "What is the planning health?"
- **Extracted**: `scope_type=None`, `scope_value=None`

## Answer Modes

### Summary Mode (Default)

Used for general questions without specific scope. Returns high-level insights.

**Triggers**:
- No scope detected
- Summary query type
- Provenance query type

**Example Response**:
```
Planning health is 65/100 (At Risk). 35% of records changed (245/700). 
Risk level: Design + Supplier. Breakdown: Qty 20%, Supplier 40%, Design 35%, Schedule 5%.
```

### Investigate Mode

Used for specific, scoped questions. Returns targeted analysis with scoped metrics.

**Triggers**:
- Comparison questions (always)
- Traceability questions (always)
- Root cause questions (with scope)
- Why-not questions (with scope)
- Any scoped question

**Example Response**:
```
In LOC001, design changed. This is risky because 37.5% of records changed (45/120). 
Recommended action: Review design change impact on schedule.
```

## Query Types

### Comparison
- **Keywords**: "compare", "vs", "versus", "difference between"
- **Example**: "Compare LOC001 vs LOC002"
- **Mode**: Always investigate
- **Response**: Side-by-side metrics for two entities

### Root Cause
- **Keywords**: "why", "cause", "reason", "root"
- **Example**: "Why is LOC001 risky?"
- **Mode**: Investigate if scoped, summary otherwise
- **Response**: Entity-specific analysis with drivers and actions

### Why-Not
- **Keywords**: "why not", "why isn't", "not risky", "stable"
- **Example**: "Why is LOC002 not risky?"
- **Mode**: Investigate if scoped, summary otherwise
- **Response**: Stability explanation with metrics

### Traceability
- **Keywords**: "top record", "contributing", "impacted material", "show record"
- **Example**: "Show top contributing records"
- **Mode**: Always investigate
- **Response**: Top 5 records sorted by impact

### Risk
- **Keywords**: "risk", "high risk", "danger"
- **Example**: "What is the risk level?"
- **Mode**: Summary
- **Response**: Risk summary and high-risk records

### Action
- **Keywords**: "action", "do next", "recommend", "planner"
- **Example**: "What should the planner do next?"
- **Mode**: Summary
- **Response**: Recommended actions list

### Provenance
- **Keywords**: "source", "blob", "mock", "refresh", "stale"
- **Example**: "Where does this data come from?"
- **Mode**: Summary
- **Response**: Data source and freshness information

### Summary (Default)
- **Example**: "What is the planning health?"
- **Mode**: Summary
- **Response**: General insights and metrics

## Scoped Metrics

When in investigate mode with scope, the response includes `investigateMode` object with scoped metrics.

### filteredRecordsCount
Number of records matching the scope.

```json
"filteredRecordsCount": 120
```

### scopedContributionBreakdown
Percentage breakdown of change drivers within the scope.

```json
"scopedContributionBreakdown": {
  "quantity": 25.0,
  "supplier": 35.0,
  "design": 35.0,
  "schedule": 5.0
}
```

### scopedDrivers
Primary driver and change counts for the scope.

```json
"scopedDrivers": {
  "primary": "design",
  "changedCount": 45,
  "totalCount": 120
}
```

### topContributingRecords
Top 5 records by absolute forecast delta within the scope.

```json
"topContributingRecords": [
  {
    "locationId": "LOC001",
    "materialGroup": "Electronics",
    "materialId": "MAT001",
    "qtyDelta": 500,
    "changeType": "Qty Increase",
    "riskLevel": "High Risk"
  }
]
```

### scopeType and scopeValue
The extracted scope information.

```json
"scopeType": "location",
"scopeValue": "LOC001"
```

## Answer Templates

### Comparison Template

**Format**: Side-by-side metrics for two entities

**Example**:
```
📊 Comparison: LOC001 vs LOC002

LOC001: 45/120 changed (37.5%). Primary driver: design
LOC002: 28/95 changed (29.5%). Primary driver: quantity

→ LOC001 has more changes.
```

**Includes**:
- Changed count and percentage for each entity
- Primary driver for each entity
- Comparison indicator (which has more changes)

### Root Cause Template

**Format**: Entity-specific analysis with drivers and actions

**Example**:
```
In LOC001, design changed. This is risky because 37.5% of records changed (45/120). 
Recommended action: Review design change impact on schedule.
```

**Includes**:
- Entity name
- What changed (primary driver)
- Why it's risky (change rate and count)
- Recommended action

### Why-Not Template

**Format**: Stability explanation

**Example**:
```
LOC002 is stable because only 29.5% of records changed (28/95).
```

**Includes**:
- Entity name
- Reason for stability (change rate or no changes)
- Supporting metrics

### Traceability Template

**Format**: Top contributing records list

**Example**:
```
📊 Top 5 contributing records (by forecast delta):
  LOC001 / Electronics / MAT001 — Δ+500 [Qty Increase] [High Risk]
  LOC002 / Mechanical / MAT002 — Δ+300 [Design Change] [Medium Risk]
  LOC001 / Electronics / MAT003 — Δ+200 [Supplier Change] [High Risk]
  LOC003 / Mechanical / MAT004 — Δ-150 [Qty Decrease] [Low Risk]
  LOC002 / Electronics / MAT005 — Δ-100 [Schedule Change] [Medium Risk]
```

**Includes**:
- Location / Material Group / Material ID
- Forecast delta (Δ) with sign
- Change type
- Risk level

## New Response Fields (Version 1.5)

### answerMode
Indicates the mode used to generate the answer.

**Values**:
- `"summary"` - General insights without specific scope
- `"investigate"` - Targeted analysis with scoped metrics

**Example**:
```json
"answerMode": "investigate"
```

### scopeType
The type of scope extracted from the question.

**Values**:
- `"location"` - Location-scoped query
- `"supplier"` - Supplier-scoped query
- `"material_group"` - Material group-scoped query
- `"material_id"` - Material ID-scoped query
- `"risk_type"` - Risk type-scoped query
- `null` - No scope detected

**Example**:
```json
"scopeType": "location",
"scopeValue": "LOC001"
```

### scopeValue
The specific value of the extracted scope.

**Example**:
```json
"scopeValue": "LOC001"
```

### supportingMetrics
Key metrics supporting the answer.

**Fields**:
- `changedRecordCount` - Number of records that changed
- `totalRecords` - Total records in scope
- `trendDelta` - Total forecast delta
- `planningHealth` - Planning health score

**Example**:
```json
"supportingMetrics": {
  "changedRecordCount": 245,
  "totalRecords": 700,
  "trendDelta": 1500,
  "planningHealth": 65
}
```

### comparisonMetrics
Metrics for comparison queries (when answerMode="investigate" and queryType="comparison").

**Fields**:
- `entity1` - First entity in comparison
  - `name` - Entity name
  - `totalRecords` - Total records
  - `changedRecords` - Changed records
  - `changePercentage` - Change percentage
  - `forecastDelta` - Forecast delta
  - `primaryDriver` - Primary change driver
  - `riskLevel` - Risk level
- `entity2` - Second entity in comparison (same structure as entity1)
- `comparison` - Comparison result
  - `hasMoreChanges` - Which entity has more changes
  - `primaryDifference` - Main difference between entities

**Example**:
```json
"comparisonMetrics": {
  "entity1": {
    "name": "LOC001",
    "totalRecords": 120,
    "changedRecords": 45,
    "changePercentage": 37.5,
    "forecastDelta": 500,
    "primaryDriver": "design",
    "riskLevel": "High Risk"
  },
  "entity2": {
    "name": "LOC002",
    "totalRecords": 95,
    "changedRecords": 28,
    "changePercentage": 29.5,
    "forecastDelta": 300,
    "primaryDriver": "quantity",
    "riskLevel": "Medium Risk"
  },
  "comparison": {
    "hasMoreChanges": "LOC001",
    "primaryDifference": "LOC001 has more design changes"
  }
}
```

### supplierMetrics
Metrics for supplier-by-location queries (when answerMode="investigate" and queryType="supplier_by_location").

**Fields**:
- `location` - Location being analyzed
- `suppliers` - Array of supplier metrics
  - `name` - Supplier name
  - `affectedRecords` - Number of affected records
  - `forecastImpact` - Total forecast delta
  - `designChangeCount` - Design changes
  - `designChangePercentage` - Design change percentage
  - `availabilityIssues` - Availability issue count
  - `rojIssues` - ROJ/needed date issue count
  - `riskLevel` - Risk level
  - `behavior` - Supplier behavior analysis
    - `designChanges` - Design change details
    - `availabilityIssues` - Availability issue details
    - `rojBehavior` - ROJ behavior details
    - `forecastBehavior` - Forecast behavior details

**Example**:
```json
"supplierMetrics": {
  "location": "LOC001",
  "suppliers": [
    {
      "name": "SUP-A",
      "affectedRecords": 15,
      "forecastImpact": 450,
      "designChangeCount": 8,
      "designChangePercentage": 53.3,
      "availabilityIssues": 2,
      "rojIssues": 3,
      "riskLevel": "High Risk",
      "behavior": {
        "designChanges": "8 records with design changes (53.3%)",
        "availabilityIssues": "2 records missing supplier date",
        "rojBehavior": "3 records with ROJ movement",
        "forecastBehavior": "Forecast increased by 450 units"
      }
    }
  ]
}
```

### recordComparison
Metrics for record-level comparison queries (when answerMode="investigate" and queryType="record_detail").

**Fields**:
- `location` - Location of record
- `materialGroup` - Material group
- `materialId` - Material ID
- `current` - Current record values
  - `forecast` - Current forecast
  - `roj` - Current ROJ date
  - `supplierDate` - Current supplier date
  - `bod` - Current BOD
  - `formFactor` - Current form factor
- `previous` - Previous record values (same structure as current)
- `changes` - Changes from previous to current
  - `forecastDelta` - Forecast change
  - `rojDelta` - ROJ change (days)
  - `supplierDateDelta` - Supplier date change (days)
  - `bodChanged` - BOD changed (boolean)
  - `formFactorChanged` - Form factor changed (boolean)
- `flags` - Record flags
  - `isNewDemand` - New demand (boolean)
  - `isCancelled` - Cancelled (boolean)
  - `supplierDateMissing` - Supplier date missing (boolean)
  - `riskLevel` - Risk level

**Example**:
```json
"recordComparison": {
  "location": "LOC001",
  "materialGroup": "Electronics",
  "materialId": "MAT001",
  "current": {
    "forecast": 1500,
    "roj": "2026-05-15",
    "supplierDate": "2026-05-10",
    "bod": "2026-04-01",
    "formFactor": "Standard"
  },
  "previous": {
    "forecast": 1000,
    "roj": "2026-05-20",
    "supplierDate": "2026-05-15",
    "bod": "2026-04-01",
    "formFactor": "Standard"
  },
  "changes": {
    "forecastDelta": 500,
    "rojDelta": -5,
    "supplierDateDelta": -5,
    "bodChanged": false,
    "formFactorChanged": false
  },
  "flags": {
    "isNewDemand": false,
    "isCancelled": false,
    "supplierDateMissing": false,
    "riskLevel": "High Risk"
  }
}
```

## Backward Compatibility

### Existing Clients
- Existing API contract unchanged
- New fields added (not replacing)
- Summary mode is default for unscoped questions
- Existing clients continue to work without modification

### Migration Path
1. Existing clients receive new `answerMode` and `investigateMode` fields
2. Clients can ignore new fields (backward compatible)
3. Clients can opt-in to using new fields for enhanced UX
4. No breaking changes to existing response structure

### New Optional Fields
- `answerMode` - Always present (summary or investigate)
- `scopeType` - Optional (null if no scope)
- `scopeValue` - Optional (null if no scope)
- `supportingMetrics` - Always present
- `comparisonMetrics` - Optional (only for comparison queries)
- `supplierMetrics` - Optional (only for supplier queries)
- `recordComparison` - Optional (only for record detail queries)

## Comparison Capability (Version 1.5)

### Overview
The Copilot now supports deterministic comparison queries for locations, material groups, material IDs, and records. Comparisons always return side-by-side metrics and never fall back to global summary.

### Comparison Query Types

#### Location vs Location
**Example**: "Compare LOC001 vs LOC002"

**Response**:
```json
{
  "question": "Compare LOC001 vs LOC002",
  "answer": "📊 Comparison: LOC001 vs LOC002\n\nLOC001: 45/120 changed (37.5%). Primary driver: design\nLOC002: 28/95 changed (29.5%). Primary driver: quantity\n\n→ LOC001 has more changes.",
  "queryType": "comparison",
  "answerMode": "investigate",
  "comparisonMetrics": {
    "entity1": {
      "name": "LOC001",
      "totalRecords": 120,
      "changedRecords": 45,
      "changePercentage": 37.5,
      "forecastDelta": 500,
      "primaryDriver": "design",
      "riskLevel": "High Risk"
    },
    "entity2": {
      "name": "LOC002",
      "totalRecords": 95,
      "changedRecords": 28,
      "changePercentage": 29.5,
      "forecastDelta": 300,
      "primaryDriver": "quantity",
      "riskLevel": "Medium Risk"
    },
    "comparison": {
      "hasMoreChanges": "LOC001",
      "primaryDifference": "LOC001 has more design changes"
    }
  }
}
```

#### Material Group vs Material Group
**Example**: "Compare PUMP vs VALVE"

**Response**: Same structure as location comparison, with material group names.

#### Material ID vs Material ID
**Example**: "Compare MAT-100 vs MAT-102"

**Response**: Same structure as location comparison, with material IDs.

#### Record vs Record (Composite Key)
**Example**: "Compare MAT-100 at LOC001 vs MAT-100 at LOC002"

**Response**: Same structure as location comparison, with record identifiers.

### Comparison Metrics

**Side-by-Side Metrics**:
- Total records
- Changed records
- Change percentage
- Forecast delta
- Primary driver
- Risk level

**Comparison Result**:
- Which entity has more changes
- Primary difference between entities

### Fallback Prevention

Comparison queries **never fall back to global summary**. If a comparison cannot be computed:
- Return specific error message
- Suggest alternative query
- Example: "Could not compare LOC001 vs LOC002. Try asking about a specific location."

---

## Supplier-by-Location Capability (Version 1.5)

### Overview
The Copilot now supports supplier-by-location queries to analyze supplier behavior and impact at specific locations.

### Supplier Query Types

#### List Suppliers for Location
**Example**: "List suppliers for LOC001"

**Response**:
```json
{
  "question": "List suppliers for LOC001",
  "answer": "📊 Suppliers at LOC001:\n\nSUP-A: 15 records, Δ+450, Design: 8 (53%), Availability: 2, ROJ: 3, Risk: High\nSUP-B: 12 records, Δ+300, Design: 5 (42%), Availability: 1, ROJ: 2, Risk: Medium\n\n→ SUP-A has most impact",
  "queryType": "supplier_by_location",
  "answerMode": "investigate",
  "supplierMetrics": {
    "location": "LOC001",
    "suppliers": [
      {
        "name": "SUP-A",
        "affectedRecords": 15,
        "forecastImpact": 450,
        "designChangeCount": 8,
        "designChangePercentage": 53.3,
        "availabilityIssues": 2,
        "rojIssues": 3,
        "riskLevel": "High Risk",
        "behavior": {
          "designChanges": "8 records with design changes (53.3%)",
          "availabilityIssues": "2 records missing supplier date",
          "rojBehavior": "3 records with ROJ movement",
          "forecastBehavior": "Forecast increased by 450 units"
        }
      }
    ]
  }
}
```

#### Supplier Behavior Analysis
**Example**: "Which supplier at LOC001 has most design changes?"

**Response**: Supplier list filtered and sorted by design changes.

**Example**: "Which supplier at LOC001 has availability issues?"

**Response**: Supplier list filtered and sorted by availability issues.

### Supplier Metrics

**Per-Supplier Metrics**:
- Affected records count
- Forecast impact (total delta)
- Design change count and percentage
- Availability issues count
- ROJ/needed date issues count
- Risk level

**Supplier Behavior Analysis**:
- Design change details
- Availability issue details
- ROJ behavior details
- Forecast behavior details

### Supplier Behavior Patterns

**Design Changes**:
- Count and percentage of records with design changes
- Example: "8 records with design changes (53.3%)"

**Availability Issues**:
- Missing supplier date count
- Changed supplier date count
- Supplier delay patterns
- Example: "2 records missing supplier date"

**ROJ/Needed Date Behavior**:
- ROJ movement count and direction
- NBD delta days (average, range)
- Example: "3 records with ROJ movement"

**Forecast Behavior**:
- Forecast increases (count, total delta)
- Forecast decreases (count, total delta)
- Example: "Forecast increased by 450 units"

---

## Record-Level Comparison Capability (Version 1.5)

### Overview
The Copilot now supports record-level comparison using composite key (LOCID, MaterialGroup, PRDID) to compare current vs previous record state.

### Record Comparison Query Types

#### What Changed for Material
**Example**: "What changed for MAT-100 at LOC001?"

**Response**:
```json
{
  "question": "What changed for MAT-100 at LOC001?",
  "answer": "📊 Record Comparison: MAT-100 at LOC001\n\nCurrent: Forecast 1500, ROJ 2026-05-15, Supplier Date 2026-05-10\nPrevious: Forecast 1000, ROJ 2026-05-20, Supplier Date 2026-05-15\n\nChanges: Forecast +500, ROJ -5 days, Supplier Date -5 days\n→ Primary change: Forecast increase\n→ Recommended action: Review supplier readiness",
  "queryType": "record_detail",
  "answerMode": "investigate",
  "recordComparison": {
    "location": "LOC001",
    "materialGroup": "Electronics",
    "materialId": "MAT001",
    "current": {
      "forecast": 1500,
      "roj": "2026-05-15",
      "supplierDate": "2026-05-10",
      "bod": "2026-04-01",
      "formFactor": "Standard"
    },
    "previous": {
      "forecast": 1000,
      "roj": "2026-05-20",
      "supplierDate": "2026-05-15",
      "bod": "2026-04-01",
      "formFactor": "Standard"
    },
    "changes": {
      "forecastDelta": 500,
      "rojDelta": -5,
      "supplierDateDelta": -5,
      "bodChanged": false,
      "formFactorChanged": false
    },
    "flags": {
      "isNewDemand": false,
      "isCancelled": false,
      "supplierDateMissing": false,
      "riskLevel": "High Risk"
    }
  }
}
```

#### Record Comparison
**Example**: "Compare this material current vs previous"

**Response**: Same structure as "What changed" query.

### Record Comparison Metrics

**Composite Key**: `(LOCID, MaterialGroup, PRDID)`

**Current vs Previous Comparison**:
- Forecast previous vs current
- ROJ previous vs current
- Supplier date previous vs current
- BOD previous vs current
- Form Factor previous vs current

**Changes**:
- Forecast delta
- ROJ delta (days)
- Supplier date delta (days)
- BOD changed (boolean)
- Form Factor changed (boolean)

**Flags**:
- New demand (boolean)
- Cancelled (boolean)
- Supplier date missing (boolean)
- Risk level

### Composite Key Enforcement

The composite key `(LOCID, MaterialGroup, PRDID)` is used to:
- Uniquely identify a planning record
- Enforce record-level comparison scope
- Prevent cross-location or cross-material-group comparisons
- Ensure data integrity

---

## Performance (Version 1.5)

### Component Latency

**Intent Classification**:
- **Target**: < 30ms
- **Typical**: 5-15ms

**Comparison Computation**:
- **Target**: < 50ms
- **Typical**: 10-30ms

**Supplier Computation**:
- **Target**: < 50ms
- **Typical**: 10-30ms

**Record Comparison**:
- **Target**: < 30ms
- **Typical**: 5-15ms

**Response Formatting**:
- **Target**: < 30ms
- **Typical**: 5-15ms

**Scoped Metrics Computation**:
- **Target**: < 50ms
- **Typical**: 10-30ms for 1000 records
- **Worst case**: 50ms for 10000 records

### Total Response Time
- **Target**: < 500ms
- **Typical**: 50-150ms
- **Worst case**: 200-300ms with large datasets

---

## Error Handling

### Missing Context
```json
{
  "error": "No cached snapshot available. Run daily-refresh to load data from Blob Storage."
}
```

### Invalid Question
```json
{
  "error": "question is required"
}
```

### Invalid JSON
```json
{
  "error": "Invalid JSON body."
}
```

## Examples

### Example 1: Comparison Question

**Request**:
```json
{
  "question": "Compare LOC001 vs LOC002",
  "context": {...}
}
```

**Response**:
```json
{
  "question": "Compare LOC001 vs LOC002",
  "answer": "📊 Comparison: LOC001 vs LOC002\n\nLOC001: 45/120 changed (37.5%). Primary driver: design\nLOC002: 28/95 changed (29.5%). Primary driver: quantity\n\n→ LOC001 has more changes.",
  "queryType": "comparison",
  "answerMode": "investigate",
  "investigateMode": {
    "filteredRecordsCount": 120,
    "scopedContributionBreakdown": {...},
    "scopedDrivers": {...},
    "topContributingRecords": [...],
    "scopeType": "location",
    "scopeValue": "LOC001"
  }
}
```

### Example 2: Root Cause Question

**Request**:
```json
{
  "question": "Why is LOC001 risky?",
  "context": {...}
}
```

**Response**:
```json
{
  "question": "Why is LOC001 risky?",
  "answer": "In LOC001, design changed. This is risky because 37.5% of records changed (45/120). Recommended action: Review design change impact on schedule.",
  "queryType": "root_cause",
  "answerMode": "investigate",
  "investigateMode": {
    "filteredRecordsCount": 120,
    "scopedContributionBreakdown": {...},
    "scopedDrivers": {...},
    "topContributingRecords": [...],
    "scopeType": "location",
    "scopeValue": "LOC001"
  }
}
```

### Example 3: Why-Not Question

**Request**:
```json
{
  "question": "Why is LOC002 not risky?",
  "context": {...}
}
```

**Response**:
```json
{
  "question": "Why is LOC002 not risky?",
  "answer": "LOC002 is stable because only 29.5% of records changed (28/95).",
  "queryType": "why_not",
  "answerMode": "investigate",
  "investigateMode": {
    "filteredRecordsCount": 95,
    "scopedContributionBreakdown": {...},
    "scopedDrivers": {...},
    "topContributingRecords": [...],
    "scopeType": "location",
    "scopeValue": "LOC002"
  }
}
```

### Example 4: Traceability Question

**Request**:
```json
{
  "question": "Show top contributing records",
  "context": {...}
}
```

**Response**:
```json
{
  "question": "Show top contributing records",
  "answer": "📊 Top 5 contributing records (by forecast delta):\n  LOC001 / Electronics / MAT001 — Δ+500 [Qty Increase] [High Risk]\n  LOC002 / Mechanical / MAT002 — Δ+300 [Design Change] [Medium Risk]\n  ...",
  "queryType": "traceability",
  "answerMode": "investigate",
  "investigateMode": {
    "filteredRecordsCount": 700,
    "scopedContributionBreakdown": {...},
    "scopedDrivers": {...},
    "topContributingRecords": [...],
    "scopeType": null,
    "scopeValue": null
  }
}
```

### Example 5: Summary Question

**Request**:
```json
{
  "question": "What is the planning health?",
  "context": {...}
}
```

**Response**:
```json
{
  "question": "What is the planning health?",
  "answer": "Planning health is 65/100 (At Risk). 35% of records changed (245/700). Risk level: Design + Supplier. Breakdown: Qty 20%, Supplier 40%, Design 35%, Schedule 5%.",
  "queryType": "summary",
  "answerMode": "summary"
}
```

## Testing

### Unit Tests
- Scope extraction for all entity types
- Scoped metrics computation for all scope types
- Answer mode determination for all query types
- Answer template generation

### Integration Tests
- Answer generation with different modes
- Explain endpoint with context and without context
- Response structure validation

### End-to-End Tests
- Real prompt categories with realistic data
- Answer specificity validation
- Response variety validation

### Performance Tests
- Scoped metrics computation time (< 100ms)
- Answer generation time (< 50ms)
- Total response time (< 500ms)

### Determinism Tests
- Same question produces same answer
- Metrics computation is deterministic
- No randomness in answer generation

## Troubleshooting

### Answer is too generic
- Check if scope was extracted correctly
- Verify `answerMode` is "investigate"
- Check if `investigateMode` fields are populated

### Scoped metrics are empty
- Verify `detailRecords` are present in context
- Check if scope_value matches records in detailRecords
- Verify record field names match expected format

### Performance is slow
- Check number of records in detailRecords
- Monitor scoped metrics computation time
- Consider caching scoped metrics for frequently asked questions

---

**Last Updated**: April 5, 2026
**Version**: 1.0
**Status**: Production Ready
