# Version 1.5 Expanded Scope: Business-Critical Capabilities

## Executive Summary

**Decision**: Expand Version 1.5 to include deterministic comparison and supplier-intelligence capabilities.

**Rationale**: Current highest-value need is correct, scoped, business-useful analysis from current planning data—not multi-turn conversation.

**Impact**: 
- Adds business-critical comparison capability
- Adds supplier-intelligence capability
- Adds record-level comparison capability
- Maintains simple architecture (no conversational complexity)
- Estimated effort: 24 hours → 36 hours

---

## Mandatory Domain Rule

**Planning Record Composite Key**: `(LOCID, MaterialGroup, PRDID)`

This composite key must be used consistently in:
- Compare logic
- Changed record detection
- New demand detection
- Cancelled demand detection
- Record-level comparison
- Copilot scoped answers

---

## Version 1.5 Expanded Scope

### Core Capabilities (Original)

1. **Intent Classification & Entity Extraction**
   - Improve entity extraction
   - Improve intent classification
   - Add prompt validation and routing

2. **Response Formatting & Quality**
   - Improve response filtering
   - Enhance answer formatting
   - Improve follow-up suggestions

3. **Response Structure & UI**
   - Add response structure fields
   - Update CopilotPanel.tsx rendering

### NEW: Business-Critical Capabilities

4. **Deterministic Comparison**
   - Location vs location comparison
   - Material group vs material group comparison
   - Material ID vs material ID comparison
   - Record vs record comparison (using composite key)
   - Side-by-side metrics (never fall back to global summary)

5. **Supplier-by-Location Intelligence**
   - List suppliers for a location
   - Enumerate suppliers active at a location
   - Show supplier summary for a location
   - Supplier-level metrics (affected records, forecast impact, risk level)

6. **Supplier Behavior Analysis**
   - Design change involvement
   - BOD change involvement
   - Form Factor change involvement
   - Availability / supplier date issues
   - Missing supplier date
   - Changed supplier date
   - Supplier delay patterns
   - Needed date / ROJ behavior
   - ROJ movement
   - NBD delta days
   - Forecast impact (increases, decreases)
   - Mismatch between demand and supplier readiness

7. **Record-Level Comparison**
   - Current vs previous comparison
   - Composite key enforcement (LOCID, MaterialGroup, PRDID)
   - Forecast previous vs current
   - ROJ previous vs current
   - Supplier date previous vs current
   - BOD previous vs current
   - Form Factor previous vs current
   - Flags: new demand, cancelled, supplier date missing, risk

---

## Question Types to Support in Version 1.5

### Comparison Queries
- "Compare LOC001 vs LOC002"
- "Compare PUMP vs VALVE"
- "Compare MAT-100 vs MAT-102"

### Supplier-by-Location Queries
- "List suppliers for LOC001"
- "Which supplier at LOC001 has most design changes?"
- "Which supplier at LOC001 has availability issues?"
- "Which supplier at LOC001 is failing needed date?"
- "Which supplier at LOC001 is most impacted by forecast increase?"

### Record-Detail Queries
- "What changed for MAT-100 at LOC001?"
- "Compare this material current vs previous"
- "Why is this record risky?"

### Existing Query Types (Enhanced)
- "Why is LOC001 risky?"
- "Why is LOC001 not risky?"
- "Show top contributing records"
- "What should the planner do next?"

---

## Comparison Capability Design

### Comparison Metrics (Side-by-Side)

For any comparison (location, material group, material ID, record), compute:

**Record Counts**:
- Total records
- Changed records
- Unchanged records

**Demand Changes**:
- New demand count
- Cancelled count
- Forecast delta

**Change Types**:
- Design change count
- Supplier change count
- ROJ / needed date change count
- Supplier date / availability issue count

**Risk**:
- Risk count
- Dominant driver

### Comparison Response Format

```
📊 Comparison: [Entity1] vs [Entity2]

[Entity1]:
  • Total records: X
  • Changed: Y (Z%)
  • Forecast delta: +/- N
  • Primary driver: [driver]
  • Risk level: [level]

[Entity2]:
  • Total records: X
  • Changed: Y (Z%)
  • Forecast delta: +/- N
  • Primary driver: [driver]
  • Risk level: [level]

→ [Entity1] has [more/fewer] changes
→ Primary difference: [difference]
→ Recommended action: [action]
```

### Comparison Query Routing

**Query Detection**:
- Keywords: "compare", "vs", "versus", "difference", "similar"
- Pattern: "[Entity1] vs [Entity2]"
- Extract both entities using improved `_extract_scope()`

**Comparison Types**:
- Location vs location: Compare LOC001 vs LOC002
- Material group vs material group: Compare PUMP vs VALVE
- Material ID vs material ID: Compare MAT-100 vs MAT-102
- Record vs record: Compare MAT-100 at LOC001 vs MAT-100 at LOC002

**Fallback Prevention**:
- Comparison queries must NEVER fall back to global summary
- If comparison fails, return specific error with suggestion
- Example: "Could not compare LOC001 vs LOC002. Try asking about a specific location."

---

## Supplier-by-Location Capability Design

### Supplier Enumeration

For a given location, return supplier-level view including:

**Supplier Identification**:
- Supplier name / identifier
- Number of affected records

**Impact Metrics**:
- Forecast impact (total delta)
- Design change involvement (count, %)
- Supplier date / availability issues (count)
- ROJ / needed date behavior (count, %)
- Risk level (count, %)

### Supplier Behavior Analysis

For any location, explain supplier behavior in terms of:

**Change Types**:
- Design change (count, %)
- BOD change (count, %)
- Form Factor change (count, %)

**Availability Issues**:
- Missing supplier date (count)
- Changed supplier date (count)
- Supplier delay patterns (description)

**Needed Date / ROJ**:
- ROJ movement (count, direction)
- NBD delta days (average, range)
- ROJ reason codes (if available)

**Forecast**:
- Forecast increases (count, total delta)
- Forecast decreases (count, total delta)
- Mismatch between demand and supplier readiness (description)

### Supplier Query Response Format

```
📊 Suppliers at [Location]:

[Supplier1]:
  • Affected records: X
  • Forecast impact: +/- N
  • Design changes: Y (Z%)
  • Availability issues: A
  • ROJ issues: B
  • Risk level: [level]

[Supplier2]:
  • Affected records: X
  • Forecast impact: +/- N
  • Design changes: Y (Z%)
  • Availability issues: A
  • ROJ issues: B
  • Risk level: [level]

→ [Supplier1] has most impact
→ Primary issue: [issue]
→ Recommended action: [action]
```

---

## Record-Level Comparison Design

### Composite Key Enforcement

**Record Identification**: `(LOCID, MaterialGroup, PRDID)`

**Comparison Scope**: Only compare records with same composite key

**Current vs Previous**:
- Forecast previous vs current
- ROJ previous vs current
- Supplier date previous vs current
- BOD previous vs current
- Form Factor previous vs current

### Record Comparison Response Format

```
📊 Record Comparison: [Material] at [Location]

Current:
  • Forecast: X units
  • ROJ: [date]
  • Supplier date: [date]
  • BOD: [value]
  • Form Factor: [value]

Previous:
  • Forecast: X units
  • ROJ: [date]
  • Supplier date: [date]
  • BOD: [value]
  • Form Factor: [value]

Changes:
  • Forecast: [delta] units
  • ROJ: [delta] days
  • Supplier date: [delta] days
  • BOD: [changed/unchanged]
  • Form Factor: [changed/unchanged]

Flags:
  • New demand: [yes/no]
  • Cancelled: [yes/no]
  • Supplier date missing: [yes/no]
  • Risk: [level]

→ Primary change: [change]
→ Recommended action: [action]
```

---

## Implementation Files & Functions

### Files to Modify

**Backend**:
- `planning_intelligence/function_app.py`
  - Enhance `_extract_scope()` - Add comparison entity extraction
  - Enhance `_classify_question()` - Add comparison and supplier query detection
  - Enhance `_generate_answer_from_context()` - Add comparison and supplier logic
  - Add `_generate_comparison_answer()` - Side-by-side comparison
  - Add `_generate_supplier_by_location_answer()` - Supplier enumeration
  - Add `_generate_record_comparison_answer()` - Record-level comparison
  - Enhance `_build_follow_ups()` - Add contextual suggestions

- `planning_intelligence/response_builder.py`
  - Add `_compute_comparison_metrics()` - Compute side-by-side metrics
  - Add `_get_suppliers_for_location()` - Enumerate suppliers
  - Add `_compute_supplier_metrics()` - Supplier-level metrics
  - Add `_get_record_comparison()` - Record-level comparison

**Frontend**:
- `frontend/src/components/CopilotPanel.tsx`
  - Render comparison side-by-side
  - Render supplier list
  - Render record comparison

**Tests**:
- `planning_intelligence/tests/test_copilot_realtime.py`
  - Add comparison tests
  - Add supplier tests
  - Add record comparison tests

- `planning_intelligence/tests/test_blob_integration.py`
  - Integration tests with real blob data

### Files NOT to Create

- ❌ `conversational_layer.py`
- ❌ `conversation_manager.py`
- ❌ `personalization_manager.py`
- ❌ `cache_manager.py`

---

## Testing Requirements

### Comparison Tests

**Location vs Location**:
- Compare LOC001 vs LOC002
- Verify side-by-side metrics
- Verify no fallback to global summary
- Verify composite key enforcement

**Material Group vs Material Group**:
- Compare PUMP vs VALVE
- Verify side-by-side metrics
- Verify correct grouping

**Material ID vs Material ID**:
- Compare MAT-100 vs MAT-102
- Verify side-by-side metrics
- Verify correct filtering

**Record vs Record**:
- Compare MAT-100 at LOC001 vs MAT-100 at LOC002
- Verify composite key enforcement
- Verify current vs previous values

### Supplier Tests

**Supplier Enumeration**:
- List suppliers for LOC001
- Verify all suppliers returned
- Verify metrics correct for that location only

**Supplier Metrics**:
- Design change count correct
- Availability issues correct
- ROJ issues correct
- Risk level correct

**Supplier Behavior**:
- Design change behavior explained
- Availability / supplier-date issues explained
- ROJ / needed-date behavior explained
- Forecast-related behavior explained

### Record Comparison Tests

**Current vs Previous**:
- Forecast previous vs current
- ROJ previous vs current
- Supplier date previous vs current
- BOD previous vs current
- Form Factor previous vs current

**Composite Key Enforcement**:
- Only compare records with same (LOCID, MaterialGroup, PRDID)
- Reject comparisons with different composite keys

**Fallback Prevention**:
- Scoped queries must not return generic global summary
- Comparison queries must not fall back to global summary
- Supplier queries must not fall back to global summary

---

## Success Criteria

### Comparison Capability
- ✓ Location vs location comparison works
- ✓ Material group vs material group comparison works
- ✓ Material ID vs material ID comparison works
- ✓ Record vs record comparison works
- ✓ Side-by-side metrics computed correctly
- ✓ Never falls back to global summary
- ✓ Composite key enforced correctly

### Supplier-by-Location Capability
- ✓ Supplier listing by location works
- ✓ Supplier enumeration correct
- ✓ Supplier metrics correct for that location only
- ✓ Supplier behavior analysis accurate
- ✓ Design change behavior explained
- ✓ Availability issues explained
- ✓ ROJ behavior explained
- ✓ Forecast behavior explained

### Record-Level Comparison
- ✓ Current vs previous comparison works
- ✓ Composite key enforced
- ✓ All fields compared correctly
- ✓ Flags computed correctly
- ✓ Changes highlighted clearly

### Overall
- ✓ All tests passing
- ✓ 100% backward compatible
- ✓ Response time < 500ms
- ✓ No unnecessary conversational complexity
- ✓ Business-useful responses

---

## Effort Estimate

### Phase 1: Intent Classification & Entity Extraction (4 hours)
- Improve entity extraction for comparison queries
- Improve intent classification for supplier queries
- Add prompt validation and routing

### Phase 2: Comparison Capability (8 hours)
- Implement comparison metrics computation
- Implement comparison answer generation
- Add comparison tests

### Phase 3: Supplier-by-Location Capability (8 hours)
- Implement supplier enumeration
- Implement supplier metrics computation
- Implement supplier behavior analysis
- Add supplier tests

### Phase 4: Record-Level Comparison (6 hours)
- Implement record comparison logic
- Enforce composite key
- Add record comparison tests

### Phase 5: Response Formatting & UI (4 hours)
- Update response structure
- Update CopilotPanel.tsx rendering
- Add UI tests

### Phase 6: Integration & Validation (6 hours)
- Integration tests with real blob data
- Backward compatibility tests
- Performance tests
- Final validation

**Total Effort**: ~36 hours

---

## Version 2 Still Deferred

**NOT in Version 1.5**:
- ❌ Conversation persistence
- ❌ Pronoun resolution
- ❌ Personalization manager
- ❌ New `/explain-conversational` endpoint
- ❌ Async follow-up generation
- ❌ Cache manager

These remain future features for Version 2.

---

## Conclusion

Version 1.5 expanded scope adds business-critical comparison and supplier-intelligence capabilities while maintaining simple architecture and backward compatibility. This delivers immediate business value without introducing unnecessary conversational complexity.
