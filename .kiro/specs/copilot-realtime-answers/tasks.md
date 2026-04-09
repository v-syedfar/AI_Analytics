# Copilot Real-Time Answers - Implementation Tasks

## Phase 0: Azure OpenAI + MCP Foundation (NEW)

### Task 0.1: Create MCP Context Builder
- [x] Create `mcp_context_builder.py` module
- [x] Implement `MCPContextBuilder` class
- [x] Implement `get_sap_field_dictionary()` method
- [x] Implement `get_semantic_mapping()` method
- [x] Implement `get_domain_rules()` method
- [x] Implement `build_mcp_context()` method
- [x] Add unit tests for each method
- [x] Verify SAP field dictionary completeness
- [x] Verify semantic mapping correctness
- [x] Verify domain rules enforcement

### Task 0.2: Create Azure OpenAI Integration Layer
- [x] Create `azure_openai_integration.py` module
- [x] Implement `AzureOpenAIIntegration` class
- [x] Implement `extract_intent_and_entities()` method
- [x] Implement `generate_clarification_prompt()` method
- [x] Implement `generate_response()` method
- [x] Add system prompt with SAP schema
- [x] Add validation guardrails (prevent hallucination)
- [x] Add error handling and fallback logic
- [x] Add unit tests for each method
- [x] Test with sample queries

### Task 0.3: Integrate MCP Context with ReasoningEngine
- [x] Update `ReasoningEngine.process_query()` to accept MCP context
- [x] Update `ReasoningEngine` to validate against SAP schema
- [x] Update `ReasoningEngine` to use semantic mapping
- [x] Update `ReasoningEngine` to enforce domain rules
- [x] Add unit tests for MCP integration
- [x] Verify backward compatibility

### Task 0.4: Integrate Azure OpenAI with Explain Endpoint
- [x] Update `explain()` endpoint to use Azure OpenAI for intent extraction
- [x] Update `explain()` endpoint to use MCP context builder
- [x] Update `explain()` endpoint to use Azure OpenAI for response generation
- [x] Add validation guardrails before returning response
- [x] Add error handling and fallback to deterministic engine
- [x] Add unit tests for endpoint integration
- [x] Test with sample queries

### Task 0.5: Create Validation Guardrails Module
- [x] Create `validation_guardrails.py` module
- [x] Implement field validation (verify SAP fields)
- [x] Implement value validation (verify numbers exist in MCP)
- [x] Implement hallucination detection (check for invented values)
- [x] Implement response regeneration logic
- [x] Add unit tests for each validation
- [x] Test with invalid inputs

## Phase 1: Core Functions

### Task 1.1: Implement Scope Extraction
- [x] Create `_extract_scope()` function
- [x] Handle location patterns (LOC001, "location X")
- [x] Handle supplier patterns (SUP001, "supplier X")
- [x] Handle material group patterns
- [x] Handle material ID patterns
- [x] Handle risk type patterns
- [x] Add unit tests for each pattern
- [x] Test edge cases (multiple entities, no entities)

### Task 1.2: Implement Question Classification with Scope
- [x] Create `_classify_question_and_extract_scope()` function
- [x] Integrate with existing `_classify_question()`
- [x] Return tuple: (query_type, scope_type, scope_value)
- [x] Add unit tests
- [x] Test all 8 query types with and without scope

### Task 1.3: Implement Answer Mode Determination
- [x] Create `_determine_answer_mode()` function
- [x] Return "summary" or "investigate"
- [x] Comparison always investigates
- [x] Traceability always investigates
- [x] Root cause investigates if scoped
- [x] Why-not investigates if scoped
- [x] Add unit tests for all combinations

### Task 1.4: Implement Scoped Metrics Computation
- [x] Create `_compute_scoped_metrics()` function
- [x] Filter detailRecords by scope_type and scope_value
- [x] Compute: changed count, change rate, contribution breakdown
- [x] Compute: drivers (primary, secondary)
- [x] Identify: top 5 contributing records
- [x] Return: filteredRecordsCount, scopedContributionBreakdown, scopedDrivers, topContributingRecords
- [x] Add unit tests for each scope type
- [x] Test with empty filtered results
- [x] Test performance (< 100ms)

## Phase 2: Answer Templates

### Task 2.1: Implement Comparison Answer Template
- [x] Create `_generate_comparison_answer()` function
- [x] Extract two entities from question
- [x] Compute metrics for each entity
- [x] Format side-by-side comparison
- [x] Include: changed count, change rate, drivers for each
- [x] Highlight which has more changes
- [x] Add unit tests
- [x] Test with locations, suppliers, material groups

### Task 2.2: Implement Root Cause Answer Template
- [x] Create `_generate_root_cause_answer()` function
- [x] Extract entity from question
- [x] Compute scoped metrics
- [x] Format: "In [entity], [what changed]. This is risky because [why]. [Action]"
- [x] Include: what changed, why it's risky, recommended action
- [x] Add unit tests
- [x] Test with different risk levels

### Task 2.3: Implement Why-Not Answer Template
- [x] Create `_generate_why_not_answer()` function
- [x] Extract entity from question
- [x] Compute scoped metrics
- [x] Format: "[Entity] is stable because [reasons]"
- [x] Compare to risky entities if applicable
- [x] Add unit tests
- [x] Test with stable and unstable entities

### Task 2.4: Implement Traceability Answer Template
- [x] Create `_generate_traceability_answer()` function
- [x] Extract top contributing records from scoped metrics
- [x] Format: "📊 Top [N] contributing records:"
- [x] Include: location, material, delta, change type, risk level
- [x] Sort by absolute delta
- [x] Add unit tests
- [x] Test with different record counts

### Task 2.5: Implement Summary Answer Template
- [x] Create `_generate_summary_answer()` function
- [x] Refactor existing answer generation logic
- [x] Keep existing templates for summary mode
- [x] Add unit tests
- [x] Ensure backward compatibility

## Phase 3: Integration

### Task 3.1: Update Answer Generation Function
- [x] Refactor `_generate_answer_from_context()` to use new functions
- [x] Add parameters: answer_mode, scope_type, scope_value, scoped_metrics
- [x] Route to appropriate template based on mode and query_type
- [x] Maintain backward compatibility
- [x] Add unit tests
- [x] Test all combinations of mode and query_type

### Task 3.2: Update Explain Endpoint
- [x] Update `explain()` function to use new classification
- [x] Extract scope from question
- [x] Determine answer mode
- [x] Compute scoped metrics if needed
- [x] Build response with investigate mode fields
- [x] Integrate ClarificationEngine for missing context detection
- [x] Return clarification response when context is incomplete
- [x] Proceed with ReasoningEngine when context is complete
- [x] Add unit tests
- [x] Test with context and without context

### Task 3.3: Add Investigate Mode Fields to Response
- [x] Add `investigateMode` object to response
- [x] Include: filteredRecordsCount, scopedContributionBreakdown, scopedDrivers, topContributingRecords
- [x] Include: scopeType, scopeValue
- [x] Add comparisonMetrics for comparison questions
- [x] Maintain backward compatibility
- [x] Add unit tests

### Task 3.4: Update Explainability Metadata
- [x] Update `_build_explainability()` to include answer mode
- [x] Add: answerMode, scopeType, scopeValue
- [x] Distinguish: data freshness vs answer specificity
- [x] Add freshness warning if data > 24h old
- [x] Add unit tests

## Phase 4: Testing

### Task 4.1: Unit Tests - Scope Extraction
- [x] Test location extraction (LOC001, "location X")
- [x] Test supplier extraction (SUP001, "supplier X")
- [x] Test material group extraction
- [x] Test material ID extraction
- [x] Test risk type extraction
- [x] Test no scope extraction
- [x] Test multiple entities
- [x] Test edge cases (special characters, case sensitivity)

### Task 4.2: Unit Tests - Scoped Metrics
- [x] Test filtering by location
- [x] Test filtering by supplier
- [x] Test filtering by material group
- [x] Test filtering by material ID
- [x] Test filtering by risk type
- [x] Test empty filtered results
- [x] Test metrics computation accuracy
- [x] Test performance (< 100ms)

### Task 4.3: Integration Tests - Answer Templates
- [x] Test comparison template with locations
- [x] Test comparison template with suppliers
- [x] Test root cause template with different risk levels
- [x] Test why-not template with stable entities
- [x] Test why-not template with unstable entities
- [x] Test traceability template with different record counts
- [x] Test summary template (backward compatibility)

### Task 4.4: Integration Tests - Explain Endpoint
- [x] Test comparison question
- [x] Test root cause question
- [x] Test why-not question
- [x] Test traceability question
- [x] Test summary question
- [x] Test with context provided
- [x] Test without context (cached snapshot)
- [x] Test with stale data

### Task 4.5: End-to-End Tests
- [x] Test: "Compare LOC001 vs LOC002"
- [x] Test: "Why is LOC001 risky?"
- [x] Test: "Why is LOC001 not risky?"
- [x] Test: "Which supplier has frequent design changes?"
- [x] Test: "Which supplier is failing ROJ need-by dates?"
- [x] Test: "Show top contributing records"
- [x] Test: "What should the planner do next?"
- [x] Verify answer is specific to question
- [x] Verify answer is not generic summary
- [x] Verify answer uses scoped metrics
- [x] Verify answer feels dynamic and targeted

### Task 4.6: Response Variety Tests
- [x] Verify comparison answers differ from summary
- [x] Verify root cause answers differ from comparison
- [x] Verify why-not answers differ from root cause
- [x] Verify traceability answers differ from why-not
- [x] Verify no template reuse across types
- [x] Verify each type has unique formatting

### Task 4.7: Freshness Tests
- [x] Test with fresh data (< 1 hour old)
- [x] Test with stale data (> 24 hours old)
- [x] Verify freshness confirmation for fresh data
- [x] Verify freshness warning for stale data
- [x] Verify warning doesn't replace analysis

### Task 4.8: Determinism Tests
- [x] Test same question twice → same answer
- [x] Test different data → different answer
- [x] Verify no randomness in answer generation
- [x] Verify metrics are deterministic
- [x] Test with different random seeds (if applicable)

## Phase 5: Documentation & Validation

### Task 5.1: Update API Documentation
- [x] Document new `investigateMode` response fields
- [x] Document scope extraction patterns
- [x] Document answer modes (summary vs investigate)
- [x] Document answer templates
- [x] Add examples for each question type

### Task 5.2: Create Test Data
- [x] Create sample questions for each type
- [x] Create expected answers for each question
- [x] Create test fixtures with known data
- [x] Document test scenarios

### Task 5.3: Performance Validation
- [x] Measure scoped metrics computation time
- [x] Measure answer generation time
- [x] Measure total response time
- [x] Verify < 100ms for scoped computation
- [x] Verify < 500ms for total response

### Task 5.4: Final Validation
- [x] Verify all requirements met
- [x] Verify all acceptance criteria passed
- [x] Verify backward compatibility
- [x] Verify determinism
- [x] Verify trust (provenance visible)
- [x] Verify performance
- [x] Get stakeholder sign-off

## Success Criteria

### SC1: Scope Extraction
- [x] 100% of location patterns extracted correctly
- [x] 100% of supplier patterns extracted correctly
- [x] 100% of material group patterns extracted correctly
- [x] 100% of material ID patterns extracted correctly
- [x] 100% of risk type patterns extracted correctly

### SC2: Scoped Metrics
- [x] 100% of comparison questions use scoped metrics
- [x] 100% of root cause questions use scoped metrics (if scoped)
- [x] 100% of why-not questions use scoped metrics (if scoped)
- [x] 100% of traceability questions use scoped metrics
- [x] All metrics computed from detailRecords (no invented numbers)

### SC3: Answer Variety
- [x] 100% of comparison answers use comparison template
- [x] 100% of root cause answers use root cause template
- [x] 100% of why-not answers use why-not template
- [x] 100% of traceability answers use traceability template
- [x] No two answer types sound identical

### SC4: Freshness Awareness
- [x] 100% of responses include freshness metadata
- [x] Fresh data: Freshness confirmation included
- [x] Stale data: Freshness warning included
- [x] Warning doesn't replace analysis

### SC5: Determinism
- [x] 100% of answers deterministic (same input = same output)
- [x] All metrics traceable to detailRecords
- [x] No randomness in answer generation
- [x] No LLM-based variation

### SC6: Performance
- [x] Scoped metrics computation < 100ms
- [x] Answer generation < 50ms
- [x] Total response time < 500ms

### SC7: Backward Compatibility
- [x] Existing API contract unchanged
- [x] New fields added (not replacing)
- [x] Existing clients continue to work
- [x] Summary mode is default for unscoped questions

### SC8: Azure OpenAI Integration (NEW)
- [x] 100% of queries use Azure OpenAI for intent extraction
- [x] 100% of queries use Azure OpenAI for entity extraction
- [x] 100% of responses use Azure OpenAI for natural language generation
- [x] 0% hallucination rate (all values validated against MCP)
- [x] All responses grounded in deterministic engine output

### SC9: MCP as Single Source of Truth (NEW)
- [x] 100% of queries use MCP context
- [x] 100% of responses include MCP provenance
- [x] 100% of SAP fields validated against field dictionary
- [x] 100% of domain rules enforced
- [x] 0% invalid field references

### SC10: Interactive Clarification (NEW)
- [x] 100% of incomplete queries trigger clarification
- [x] 100% of options are data-driven (from detailRecords)
- [x] 0% hardcoded values in options
- [x] 100% of context tracked across conversation turns
- [x] 100% of queries proceed to reasoning after context complete

### SC11: Validation Guardrails (NEW)
- [x] 100% of responses validated before returning
- [x] 0% hallucinated values
- [x] 0% invalid SAP field references
- [x] 0% null values when data exists
- [x] 100% of invalid responses regenerated or rejected

## Estimated Effort

- Phase 0 (Azure OpenAI + MCP Foundation): 16 hours
- Phase 1 (Core Functions): 8 hours
- Phase 2 (Answer Templates): 12 hours
- Phase 3 (Integration): 8 hours
- Phase 4 (Testing): 16 hours
- Phase 5 (Documentation): 4 hours
- **Total: 64 hours**

## Dependencies

- Existing `detailRecords` structure must be available
- Existing analytics functions must be accessible
- No external dependencies required

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Scope extraction too aggressive | Comprehensive unit tests, conservative patterns |
| Scoped metrics computation slow | Performance testing, optimize filtering |
| Answer templates too similar | Response variety tests, unique formatting |
| Backward compatibility broken | Comprehensive integration tests |
| Determinism violated | Determinism tests, no randomness |

## Notes

- All changes are additive (no breaking changes)
- Existing summary mode remains default
- Investigate mode is opt-in (triggered by scope detection)
- All metrics computed from existing data (no new data sources)
- No LLM-based answer generation (deterministic only)
