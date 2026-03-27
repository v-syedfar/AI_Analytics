# Planning Intelligence POC — Design Document

## 1. Overview

A Python Azure Function backend that receives planning data from Power Automate (Excel sheets),
performs normalization, comparison, analytics, and trend analysis, and returns structured JSON
responses to Copilot Studio or Power Automate flows.

---

## 2. Architecture

```
Excel Sheets (SharePoint)
        |
        v
Power Automate Flow
  - Reads current sheet rows
  - Reads previous sheet rows (or multiple snapshots for trend)
  - Sends JSON POST to Azure Function
        |
        v
Azure Function (HTTP Trigger)
  planning-intelligence-fn
  Python 3.13 | Linux | Premium Plan
        |
        ├── normalizer.py      - Maps SAP columns to clean fields
        ├── filters.py         - Filters by location / material group
        ├── comparator.py      - Compares current vs previous records
        ├── analytics.py       - Builds summary and analytical outputs
        └── trend_analyzer.py  - Multi-snapshot trend detection
        |
        v
JSON Response
        |
        v
Copilot Studio / Power Automate / Teams
```

---

## 3. Data Source — Excel Column Mapping

| SAP Column Code        | Business Description          | Internal Field         |
|------------------------|-------------------------------|------------------------|
| LOCID                  | Location ID                   | location_id            |
| PRDID                  | Material ID                   | material_id            |
| GSCEQUIPCAT            | Equipment Category            | material_group         |
| LOCFR                  | Supplier From                 | supplier               |
| LOCFRDESCR             | Supplier Description (fallback)| supplier              |
| GSCFSCTQTY             | Forecast Quantity (current)   | forecast_qty           |
| GSCPREVFCSTQTY         | Previous Forecast Quantity    | forecast_qty (prev)    |
| GSCCONROJDATE          | ROJ Need by Date (current)    | roj                    |
| GSCPREVROJNBD          | Previous ROJ Need By Date     | roj (prev)             |
| ZCOIBODVER             | BOD Version                   | bod                    |
| ZCOIFORMFACT           | Form Factor                   | ff                     |
| ROC                    | ROC Region                    | roc_region             |
| ZCOIDCID               | Facility / DC / Site Name     | dc_site                |
| ZCOIMETROID            | Planning Metro                | metro                  |
| ZCOICOUNTRY            | Country                       | country                |
| GSCSUPLDATE            | Supplier Date                 | supplier_date          |
| GSCPREVSUPLDATE        | Previous Supplier Date        | prev_supplier_date     |
| ZGSCPLANNINGEXCEPTION  | Planning Exception            | planning_exception     |
| ZGSCROJDATEREASONCODE  | ROJ Date Reason Code          | roj_reason_code        |
| ZGSCAUTOMATIONREASON   | Automation Reason             | automation_reason      |
| LASTMODIFIEDBY         | User who last modified        | last_modified_by       |
| LASTMODIFIEDDATE       | Last modified date            | last_modified_date     |
| CREATEDBY              | Created by user               | created_by             |
| CREATEDDATE            | Created date                  | created_date           |

---

## 4. Matching Key

Records are matched across current and previous sheets using a composite key:

```
location_id + material_group + material_id
(LOCID)       (GSCEQUIPCAT)    (PRDID)
```

---

## 5. Business Rules

### 5.1 Change Detection
A record is considered changed if any of these fields differ between current and previous:

| Field          | Change Flag        |
|----------------|--------------------|
| forecast_qty   | qty_changed        |
| roj            | roj_changed        |
| supplier       | supplier_changed   |
| bod or ff      | design_changed     |

### 5.2 Derived Fields

| Field        | Description                                      |
|--------------|--------------------------------------------------|
| qty_delta    | forecast_qty_current - forecast_qty_previous     |
| change_type  | Combination of changed flags e.g. "Qty + Design" |
| risk_level   | Derived from change flags (see below)            |

### 5.3 Risk Classification (priority order)

| Condition                                          | Risk Level                        |
|----------------------------------------------------|-----------------------------------|
| design_changed AND supplier_changed                | Design + Supplier Change Risk     |
| design_changed only                                | Design Change Risk                |
| supplier_changed only                              | Supplier Change Risk              |
| forecast_qty_current > 2 × forecast_qty_previous  | High Demand Spike                 |
| Any other change                                   | Normal                            |

---

## 6. API Design

### Endpoint
```
POST /api/planning-intelligence
```

### Authentication
Azure Function key (`?code=<key>` in URL or `x-functions-key` header)

### Request — Two-Snapshot Mode
```json
{
  "query_type": "summary",
  "location_id": "LOC001",
  "material_group": "PUMP",
  "current_rows": [ ...Excel rows as JSON... ],
  "previous_rows": [ ...Excel rows as JSON... ]
}
```

### Request — Trend Mode (multi-snapshot)
```json
{
  "query_type": "trend_analysis",
  "location_id": "LOC001",
  "material_group": "PUMP",
  "recurring_threshold": 3,
  "min_streak": 2,
  "snapshots": [
    { "snapshot_date": "2026-03-01", "rows": [ ...rows... ] },
    { "snapshot_date": "2026-03-08", "rows": [ ...rows... ] },
    { "snapshot_date": "2026-03-15", "rows": [ ...rows... ] }
  ]
}
```

---

## 7. Supported Query Types

### Two-Snapshot Queries

| query_type                | Question Answered                                  |
|---------------------------|----------------------------------------------------|
| summary (default)         | All six analytical questions in one response       |
| changed_count             | How many records changed?                          |
| changed_material_ids      | Which material IDs changed?                        |
| changed_records           | Show me the changed records                        |
| changes_by_location       | Which locations have the most changes?             |
| changes_by_material_group | Which equipment categories changed?                |
| change_driver_analysis    | Is it qty-, supplier-, or design-driven?           |
| high_risk_records         | Which records are high risk?                       |
| supplier_design_changes   | Supplier + design changed together                 |
| list_locations_and_groups | What locations and material groups are available?  |

### Trend Queries (multi-snapshot)

| query_type              | Question Answered                                        |
|-------------------------|----------------------------------------------------------|
| trend_analysis          | Full trend summary across all materials                  |
| consistently_increasing | Materials where qty went up every single snapshot        |
| recurring_changes       | Materials that changed in N+ snapshots (configurable)    |
| one_off_spikes          | Spiked once and recovered — not a pattern                |
| change_streaks          | Materials changed in N consecutive snapshots             |

---

## 8. Module Breakdown

### models.py
Typed dataclasses for all data structures:
- `PlanningRecord` — normalized single row from Excel
- `ComparedRecord` — result of comparing current vs previous record
- `SnapshotPoint` — one record at a specific point in time (for trend)
- `TrendRecord` — full trend analysis for a single material key

### normalizer.py
- Maps raw SAP column codes to clean field names
- Handles nulls, empty strings, type coercion
- Supports both current (`GSCFSCTQTY`) and previous (`GSCPREVFCSTQTY`) column variants

### filters.py
- Filters records by `location_id` and/or `material_group`
- Case-insensitive matching
- Returns available locations and material groups

### comparator.py
- Matches records by composite key
- Detects changes in qty, roj, supplier, bod, ff
- Derives `change_type` and `risk_level`
- New records (no previous match) are included with all change flags set

### analytics.py
- `build_summary` — full six-question analytical response
- `changes_by_location` — ranked location change counts
- `changes_by_material_group` — ranked material group change counts
- `change_driver_analysis` — qty / supplier / design / roj driver breakdown
- `high_risk_records` — filtered high risk records with risk level summary
- `filter_by_supplier_design_change` — records with both supplier and design changes

### trend_analyzer.py
- Accepts multiple dated snapshots
- Sorts snapshots chronologically
- Builds per-material timelines
- Detects: consistently increasing, consistently decreasing, volatile, stable
- Detects one-off spikes (spiked once, recovered)
- Counts change streaks (consecutive changed snapshots)
- Flags recurring changes (changed in N+ snapshots)

### function_app.py
- HTTP trigger entry point
- Routes `query_type` to the correct analytics function
- Handles both two-snapshot and multi-snapshot paths
- Returns JSON responses with proper status codes

---

## 9. Trend Detection Logic

### Qty Trend Classification
```
All diffs > 0  → "increasing"
All diffs < 0  → "decreasing"
All diffs = 0  → "stable"
Mixed          → "volatile"
```

### One-Off Spike Detection
```
1. Find snapshots where qty > 2x previous qty
2. If exactly one such snapshot exists
3. AND the value drops back down in the next snapshot
→ is_one_off_spike = True
```

### Change Streak
```
Count consecutive changed snapshots from the most recent end backwards
Resets to 0 when an unchanged snapshot is encountered
```

### Recurring Change
```
changed_snapshot_count >= recurring_threshold (default: 3)
```

---

## 10. Project Structure

```
planning_intelligence/
├── function_app.py          # HTTP trigger entry point
├── models.py                # Typed dataclasses
├── normalizer.py            # SAP column mapping + normalization
├── comparator.py            # Record comparison + risk derivation
├── filters.py               # Location / material group filtering
├── analytics.py             # Summary and analytical query builders
├── trend_analyzer.py        # Multi-snapshot trend detection
├── host.json                # Azure Functions runtime config
├── requirements.txt         # azure-functions>=1.18.0
├── local.settings.json      # Local dev config (not committed)
├── .funcignore              # Files excluded from deployment
├── samples/
│   ├── request.json         # Sample two-snapshot request
│   ├── response.json        # Sample two-snapshot response
│   └── trend_request.json   # Sample trend request
└── tests/
    ├── test_normalizer.py
    ├── test_comparator.py
    ├── test_filters.py
    ├── test_analytics.py
    └── test_trend_analyzer.py
```

---

## 11. Test Coverage

39 unit tests across 5 test files covering:
- Column normalization and null handling
- Supplier fallback (LOCFR → LOCFRDESCR)
- Change detection for all tracked fields
- Risk level derivation including combined Design + Supplier
- Case-insensitive filtering
- All six analytical query outputs
- Trend detection: increasing, volatile, recurring, one-off spike, streak
- Snapshot ordering regardless of input order
- Location filtering in trend mode

---

## 12. Deployment

- Platform: Azure Functions, Python 3.13, Linux
- Plan: Premium (EP1)
- Region: South India
- CI/CD: GitHub Actions (`.github/workflows/deploy.yml`)
- Repository: https://github.com/ShaikHafiz-1/AI_Analytics

---

## 13. Power Automate Integration

### Flow Structure (Two-Snapshot)
```
Trigger (scheduled or manual)
  → Excel: List rows from Current sheet
  → Excel: List rows from Previous sheet
  → HTTP POST to Azure Function
      Body: { query_type, location_id, material_group,
              current_rows, previous_rows }
  → Parse JSON response
  → Send to Copilot Studio / Teams / Email
```

### Flow Structure (Trend)
```
Trigger
  → For each Excel sheet in SharePoint folder:
      Append { snapshot_date, rows } to snapshots array
  → HTTP POST to Azure Function
      Body: { query_type: "trend_analysis", snapshots, ... }
  → Parse JSON response
  → Send to Copilot Studio
```

### Copilot Studio Query Mapping

| User says                              | query_type to send        |
|----------------------------------------|---------------------------|
| How many records changed?              | changed_count             |
| Show me what changed                   | changed_records           |
| Which locations changed most?          | changes_by_location       |
| Is this a spike or a pattern?          | trend_analysis            |
| Which materials keep changing?         | recurring_changes         |
| What's high risk?                      | high_risk_records         |
| Is demand consistently increasing?     | consistently_increasing   |
