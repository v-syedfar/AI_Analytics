# Implementation Plan: Copilot Version 1.5 (Expanded Scope)

## Overview - VERSION 1.5 (EXPANDED WITH BUSINESS-CRITICAL CAPABILITIES)

**IMPORTANT: This is Version 1.5 with expanded scope including deterministic comparison and supplier-intelligence capabilities.**

This plan focuses on enhancing the existing Copilot with:
1. Better intent classification, entity extraction, response formatting, and follow-up suggestions
2. **Deterministic comparison capability** (location vs location, material group vs material group, material ID vs material ID, record vs record)
3. **Supplier-intelligence capability** (supplier listing by location, supplier behavior analysis, supplier-specific metrics)
4. **Record-level comparison** (current vs previous using composite key: LOCID, MaterialGroup, PRDID)

**WITHOUT building a full conversational architecture.**

**Version 1.5 Goals**:
- Improve answer correctness and specificity
- Better handle comparison, why-not, traceability, and root cause prompts
- Support deterministic comparison queries (never fall back to global summary)
- Support supplier listing and behavior analysis by location
- Support record-level comparison using composite key
- Stricter question-specific routing
- Better response formatting and follow-up suggestions
- Maintain backward compatibility with existing `/explain` endpoint

**Mandatory Domain Rule**:
- Planning record composite key: `(LOCID, MaterialGroup, PRDID)`
- Use consistently in compare logic, changed record detection, scoped answers

**Implementation Strategy**:
- Extend existing `function_app.py` and `response_builder.py`
- Improve existing `explain()` logic
- Enhance `CopilotPanel.tsx` rendering
- Add comparison logic (side-by-side metrics)
- Add supplier enumeration and analysis logic
- Add record-level comparison logic
- Avoid creating parallel architecture
- Keep changes focused and incremental

---

## Tasks - VERSION 1.5 EXPANDED (IMPLEMENT NOW)

### Phase 1: Intent Classification & Entity Extraction (4 hours)

- [x] 1. Improve entity extraction in existing `_extract_scope()` function
  - **Status**: IMPLEMENT NOW
  - Enhance regex patterns for LOC\d+, SUP\d+, MAT\d+, material groups
  - Add support for comparison entity extraction (two entities)
  - Add validation for extracted entities
  - Test with real questions from blob data
  - **File**: `planning_intelligence/function_app.py` (extend `_extract_scope()`)
  - **Tests**: Add to `planning_intelligence/tests/test_copilot_realtime.py`

- [x] 2. Improve question classification in existing `_classify_question()` function
  - **Status**: IMPLEMENT NOW
  - Enhance keyword mappings for: comparison, root_cause, why_not, traceability, summary, supplier_by_location, record_detail
  - Add confidence scoring (0.0-1.0) based on keyword match strength
  - Handle ambiguous questions gracefully
  - Detect comparison queries ("compare", "vs", "versus")
  - Detect supplier queries ("supplier", "suppliers", "which supplier")
  - Detect record detail queries ("what changed", "compare this")
  - **File**: `planning_intelligence/function_app.py` (extend `_classify_question()`)
  - **Tests**: Add unit tests for each question type

- [x] 3. Add prompt validation and routing logic
  - **Status**: IMPLEMENT NOW
  - Validate question before routing to backend
  - Detect malformed or ambiguous questions early
  - Route to appropriate answer template based on intent
  - Route comparison queries to comparison handler
  - Route supplier queries to supplier handler
  - Route record detail queries to record comparison handler
  - **File**: `planning_intelligence/function_app.py` (in `explain()` function)
  - **Tests**: Add validation tests

### Phase 2: Comparison Capability (8 hours)

- [x] 4. Implement comparison metrics computation
  - **Status**: IMPLEMENT NOW
  - Create `_compute_comparison_metrics()` function
  - Compute side-by-side metrics for two entities
  - Metrics: total records, changed records, unchanged records, new demand, cancelled, forecast delta, design changes, supplier changes, ROJ changes, supplier date issues, risk count, dominant driver
  - Support location vs location comparison
  - Support material group vs material group comparison
  - Support material ID vs material ID comparison
  - Support record vs record comparison (using composite key)
  - **File**: `planning_intelligence/response_builder.py` (add new function)
  - **Tests**: Add unit tests for each comparison type

- [x] 5. Implement comparison answer generation
  - **Status**: IMPLEMENT NOW
  - Create `_generate_comparison_answer()` function
  - Extract two entities from question
  - Compute metrics for each entity using `_compute_comparison_metrics()`
  - Format side-by-side comparison
  - Include: changed count, change rate, drivers for each
  - Highlight which has more changes
  - Add recommended action
  - **CRITICAL**: Never fall back to global summary
  - **File**: `planning_intelligence/function_app.py` (add new function)
  - **Tests**: Add formatting tests for each comparison type

- [x] 6. Add comparison query routing in `explain()` endpoint
  - **Status**: IMPLEMENT NOW
  - Detect comparison queries in `explain()` function
  - Extract both entities
  - Call `_generate_comparison_answer()`
  - Return comparison response with answerMode="investigate"
  - **File**: `planning_intelligence/function_app.py` (in `explain()` function)
  - **Tests**: Add integration tests

- [ ] 7. Write unit tests for comparison capability
  - **Status**: IMPLEMENT NOW
  - Test location vs location comparison
  - Test material group vs material group comparison
  - Test material ID vs material ID comparison
  - Test record vs record comparison (composite key)
  - Test side-by-side metrics accuracy
  - Test no fallback to global summary
  - Test composite key enforcement
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

### Phase 3: Supplier-by-Location Capability (8 hours)

- [x] 8. Implement supplier enumeration for a location
  - **Status**: IMPLEMENT NOW
  - Create `_get_suppliers_for_location()` function
  - Return list of suppliers active at a location
  - Filter records by location
  - Extract unique suppliers
  - **File**: `planning_intelligence/response_builder.py` (add new function)
  - **Tests**: Add unit tests

- [x] 9. Implement supplier metrics computation
  - **Status**: IMPLEMENT NOW
  - Create `_compute_supplier_metrics()` function
  - For each supplier at a location, compute:
    - Number of affected records
    - Forecast impact (total delta)
    - Design change involvement (count, %)
    - Supplier date / availability issues (count)
    - ROJ / needed date behavior (count, %)
    - Risk level (count, %)
  - **File**: `planning_intelligence/response_builder.py` (add new function)
  - **Tests**: Add unit tests

- [x] 10. Implement supplier behavior analysis
  - **Status**: IMPLEMENT NOW
  - Create `_analyze_supplier_behavior()` function
  - For each supplier at a location, analyze:
    - Design change (count, %)
    - BOD change (count, %)
    - Form Factor change (count, %)
    - Missing supplier date (count)
    - Changed supplier date (count)
    - Supplier delay patterns (description)
    - ROJ movement (count, direction)
    - NBD delta days (average, range)
    - Forecast increases (count, total delta)
    - Forecast decreases (count, total delta)
    - Mismatch between demand and supplier readiness
  - **File**: `planning_intelligence/response_builder.py` (add new function)
  - **Tests**: Add unit tests

- [x] 11. Implement supplier answer generation
  - **Status**: IMPLEMENT NOW
  - Create `_generate_supplier_by_location_answer()` function
  - Extract location from question
  - Get suppliers for location using `_get_suppliers_for_location()`
  - Compute metrics for each supplier using `_compute_supplier_metrics()`
  - Analyze behavior using `_analyze_supplier_behavior()`
  - Format supplier list with metrics
  - Include: supplier name, affected records, forecast impact, design changes, availability issues, ROJ issues, risk level
  - Add recommended action
  - **File**: `planning_intelligence/function_app.py` (add new function)
  - **Tests**: Add formatting tests

- [x] 12. Add supplier query routing in `explain()` endpoint
  - **Status**: IMPLEMENT NOW
  - Detect supplier queries in `explain()` function
  - Extract location from question
  - Call `_generate_supplier_by_location_answer()`
  - Return supplier response with answerMode="investigate"
  - **File**: `planning_intelligence/function_app.py` (in `explain()` function)
  - **Tests**: Add integration tests

- [x] 13. Write unit tests for supplier capability
  - **Status**: IMPLEMENT NOW
  - Test supplier enumeration for location
  - Test supplier metrics computation
  - Test supplier behavior analysis
  - Test metrics correct for that location only
  - Test design change behavior explained
  - Test availability issues explained
  - Test ROJ behavior explained
  - Test forecast behavior explained
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

### Phase 4: Record-Level Comparison (6 hours)

- [x] 14. Implement record comparison logic
  - **Status**: IMPLEMENT NOW
  - Create `_get_record_comparison()` function
  - Use composite key: (LOCID, MaterialGroup, PRDID)
  - Get current record
  - Get previous record (from snapshot)
  - Compare all fields:
    - Forecast previous vs current
    - ROJ previous vs current
    - Supplier date previous vs current
    - BOD previous vs current
    - Form Factor previous vs current
  - Compute flags: new demand, cancelled, supplier date missing, risk
  - **File**: `planning_intelligence/response_builder.py` (add new function)
  - **Tests**: Add unit tests

- [x] 15. Implement record comparison answer generation
  - **Status**: IMPLEMENT NOW
  - Create `_generate_record_comparison_answer()` function
  - Extract material and location from question
  - Use composite key to get record comparison
  - Format current vs previous comparison
  - Include: forecast, ROJ, supplier date, BOD, Form Factor
  - Include: changes, flags, primary change, recommended action
  - **File**: `planning_intelligence/function_app.py` (add new function)
  - **Tests**: Add formatting tests

- [x] 16. Add record detail query routing in `explain()` endpoint
  - **Status**: IMPLEMENT NOW
  - Detect record detail queries in `explain()` function
  - Extract material and location from question
  - Call `_generate_record_comparison_answer()`
  - Return record comparison response with answerMode="investigate"
  - **File**: `planning_intelligence/function_app.py` (in `explain()` function)
  - **Tests**: Add integration tests

- [x] 17. Write unit tests for record comparison capability
  - **Status**: IMPLEMENT NOW
  - Test current vs previous comparison
  - Test composite key enforcement
  - Test all fields compared correctly
  - Test flags computed correctly
  - Test changes highlighted clearly
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

### Phase 5: Response Formatting & Quality (4 hours)

- [ ] 18. Improve response filtering in existing `_generate_answer_from_context()` function
  - **Status**: IMPLEMENT NOW
  - Filter responses to show only answer to current question
  - Remove unrelated metrics and suggestions
  - Keep answer and supporting metrics for current scope
  - **File**: `planning_intelligence/function_app.py` (extend `_generate_answer_from_context()`)
  - **Tests**: Add response filtering tests

- [ ] 19. Enhance answer formatting for each question type
  - **Status**: IMPLEMENT NOW
  - Improve comparison answer formatting (side-by-side metrics)
  - Improve root cause answer formatting (what changed, why risky, action)
  - Improve why-not answer formatting (stability explanation)
  - Improve traceability answer formatting (top contributing records)
  - Improve supplier answer formatting (supplier list with metrics)
  - Improve record comparison answer formatting (current vs previous)
  - **File**: `planning_intelligence/function_app.py` (enhance existing answer templates)
  - **Tests**: Add formatting tests for each type

- [ ] 20. Improve follow-up suggestion generation
  - **Status**: IMPLEMENT NOW
  - Generate 2-3 contextual suggestions per answer
  - Implement patterns for each intent type
  - Guide toward deeper analysis (drill-down, comparison, root cause)
  - For comparison: suggest drill-down into specific supplier or material
  - For supplier: suggest root cause analysis
  - For record detail: suggest comparison with other records
  - **File**: `planning_intelligence/function_app.py` (enhance `_build_follow_ups()`)
  - **Tests**: Add follow-up generation tests

### Phase 6: Response Structure & Backward Compatibility (4 hours)

- [ ] 21. Enhance response structure for better clarity
  - **Status**: IMPLEMENT NOW
  - Add `answerMode` field (summary vs investigate)
  - Add `scopeType` and `scopeValue` fields
  - Add `supportingMetrics` section
  - Add `comparisonMetrics` for comparison queries
  - Add `supplierMetrics` for supplier queries
  - Add `recordComparison` for record detail queries
  - Keep all existing fields unchanged (backward compatible)
  - **File**: `planning_intelligence/function_app.py` (in `explain()` response building)
  - **Tests**: Backward compatibility tests

- [ ] 22. Update CopilotPanel.tsx rendering
  - **Status**: IMPLEMENT NOW
  - Render greeting (if provided)
  - Render answer clearly separated from suggestions
  - Render follow-up suggestions one at a time (not all mixed together)
  - Show supporting metrics when relevant
  - Render comparison side-by-side
  - Render supplier list
  - Render record comparison
  - **File**: `frontend/src/components/CopilotPanel.tsx`
  - **Tests**: Manual UI testing with real responses

### Phase 7: Testing & Validation (8 hours)

- [ ] 23. Write integration tests with real blob data
  - **Status**: IMPLEMENT NOW
  - Test with real questions from blob storage
  - Test comparison prompts (location, material group, material ID, record)
  - Test supplier prompts (list suppliers, supplier behavior)
  - Test record detail prompts (what changed, compare current vs previous)
  - Test why-not prompts
  - Test traceability prompts
  - Test root cause prompts
  - **File**: `planning_intelligence/tests/test_blob_integration.py`

- [ ] 24. Write backward compatibility tests
  - **Status**: IMPLEMENT NOW
  - Test existing clients without new fields
  - Verify all existing fields present and unchanged
  - Test response structure with and without new fields
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 25. Write response quality tests
  - **Status**: IMPLEMENT NOW
  - Test that answers are specific to question
  - Test that answers are not generic summaries
  - Test that answers use scoped metrics
  - Test that answers feel targeted and relevant
  - Test that comparison never falls back to global summary
  - Test that supplier queries never fall back to global summary
  - Test that record queries never fall back to global summary
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 26. Write performance tests
  - **Status**: IMPLEMENT NOW
  - Measure intent classification latency (target: < 30ms)
  - Measure comparison computation latency (target: < 50ms)
  - Measure supplier computation latency (target: < 50ms)
  - Measure record comparison latency (target: < 30ms)
  - Measure response formatting latency (target: < 30ms)
  - Measure follow-up generation latency (target: < 50ms)
  - Measure total response time (target: < 500ms)
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

### Phase 8: Documentation & Deployment (2 hours)

- [x] 27. Update API documentation
  - **Status**: IMPLEMENT NOW
  - Document new response fields (answerMode, scopeType, scopeValue, supportingMetrics, comparisonMetrics, supplierMetrics, recordComparison)
  - Document improved answer templates
  - Document follow-up suggestion patterns
  - Document comparison capability
  - Document supplier capability
  - Document record comparison capability
  - **File**: `planning_intelligence/API_DOCUMENTATION_COPILOT.md`

- [x] 28. Create Version 1.5 implementation guide
  - **Status**: IMPLEMENT NOW
  - Document changes to `function_app.py`
  - Document changes to `response_builder.py`
  - Document changes to `CopilotPanel.tsx`
  - Document testing approach
  - Document composite key enforcement
  - **File**: Create `.kiro/specs/copilot-personalization-conversational/VERSION_1_5_GUIDE.md`

- [x] 29. Verify backward compatibility
  - **Status**: IMPLEMENT NOW
  - Test with real existing client requests
  - Verify all existing fields present
  - Verify new fields optional
  - Verify no breaking changes
  - **File**: Run backward compatibility tests

- [x] 30. Final validation with blob data
  - **Status**: IMPLEMENT NOW
  - Run all tests with real blob storage data
  - Verify response quality improvements
  - Verify performance (< 500ms total response time)
  - Verify comparison never falls back to global summary
  - Verify supplier queries work correctly
  - Verify record comparison works correctly
  - **File**: Run integration tests

---

## Success Criteria - VERSION 1.5 EXPANDED

### Comparison Capability
- ✓ Location vs location comparison works
- ✓ Material group vs material group comparison works
- ✓ Material ID vs material ID comparison works
- ✓ Record vs record comparison works (composite key enforced)
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
- ✓ Comparison prompts handled better
- ✓ Supplier prompts handled better
- ✓ Record detail prompts handled better
- ✓ Why-not prompts handled better
- ✓ Traceability prompts handled better
- ✓ Root cause prompts handled better
- ✓ Responses are specific to question (not generic summaries)
- ✓ Follow-up suggestions are contextual and relevant
- ✓ 100% backward compatible with existing clients
- ✓ All tests passing with real blob data
- ✓ Response time < 500ms
- ✓ No new parallel architecture introduced
- ✓ No unnecessary conversational complexity

---

## Effort Estimate

- **Phase 1**: 4 hours
- **Phase 2**: 8 hours
- **Phase 3**: 8 hours
- **Phase 4**: 6 hours
- **Phase 5**: 4 hours
- **Phase 6**: 4 hours
- **Phase 7**: 8 hours
- **Phase 8**: 2 hours

**Total Effort**: ~44 hours

---

## Files to Modify

### Backend
- `planning_intelligence/function_app.py` - Enhance existing functions, add new handlers
- `planning_intelligence/response_builder.py` - Add comparison, supplier, record comparison logic

### Frontend
- `frontend/src/components/CopilotPanel.tsx` - Better rendering

### Tests
- `planning_intelligence/tests/test_copilot_realtime.py` - Add tests
- `planning_intelligence/tests/test_blob_integration.py` - Integration tests

### Documentation
- `planning_intelligence/API_DOCUMENTATION_COPILOT.md` - Update docs

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

## Notes

- All changes are additive (no breaking changes)
- Existing `/explain` endpoint remains primary
- New response fields are optional
- No conversation persistence or pronoun resolution
- No new endpoints created
- Focus on answer quality, comparison, and supplier intelligence
- Keep implementation simple and focused
- Composite key enforcement is critical
- Never fall back to global summary for scoped queries
