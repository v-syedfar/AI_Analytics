# Implementation Plan: Copilot Personalization & Conversational AI

## Overview - VERSION 1.5 (SCOPED)

**IMPORTANT: This is a scoped Version 1.5 implementation focused on immediate answer quality improvements.**

This plan focuses on enhancing the existing Copilot with better intent classification, entity extraction, response formatting, and follow-up suggestions—WITHOUT building a full conversational architecture.

**Version 1.5 Goals**:
- Improve answer correctness and specificity
- Better handle comparison, why-not, traceability, and root cause prompts
- Stricter question-specific routing
- Better response formatting and follow-up suggestions
- Maintain backward compatibility with existing `/explain` endpoint

**Version 2 (Deferred)**: Full conversational memory, pronoun resolution, personalization manager, and new endpoints will be designed for future implementation.

**Implementation Strategy**:
- Extend existing `function_app.py` and `response_builder.py`
- Improve existing `explain()` logic
- Enhance `CopilotPanel.tsx` rendering
- Avoid creating parallel architecture
- Keep changes focused and incremental

## Tasks - VERSION 1.5 (IMPLEMENT NOW)

### Phase 1: Intent Classification & Entity Extraction (Extend existing code)

- [ ] 1. Improve entity extraction in existing `_extract_scope()` function
  - **Status**: IMPLEMENT NOW
  - Enhance regex patterns for LOC\d+, SUP\d+, MAT\d+, material groups
  - Add validation for extracted entities
  - Test with real questions from blob data
  - **File**: `planning_intelligence/function_app.py` (extend `_extract_scope()`)
  - **Tests**: Add to `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 2. Improve question classification in existing `_classify_question()` function
  - **Status**: IMPLEMENT NOW
  - Enhance keyword mappings for: comparison, root_cause, why_not, traceability, summary
  - Add confidence scoring (0.0-1.0) based on keyword match strength
  - Handle ambiguous questions gracefully
  - **File**: `planning_intelligence/function_app.py` (extend `_classify_question()`)
  - **Tests**: Add unit tests for each question type

- [ ] 3. Add prompt validation and routing logic
  - **Status**: IMPLEMENT NOW
  - Validate question before routing to backend
  - Detect malformed or ambiguous questions early
  - Route to appropriate answer template based on intent
  - **File**: `planning_intelligence/function_app.py` (in `explain()` function)
  - **Tests**: Add validation tests

### Phase 2: Response Formatting & Quality (Extend existing code)

- [ ] 4. Improve response filtering in existing `_generate_answer_from_context()` function
  - **Status**: IMPLEMENT NOW
  - Filter responses to show only answer to current question
  - Remove unrelated metrics and suggestions
  - Keep answer and supporting metrics for current scope
  - **File**: `planning_intelligence/function_app.py` (extend `_generate_answer_from_context()`)
  - **Tests**: Add response filtering tests

- [ ] 5. Enhance answer formatting for each question type
  - **Status**: IMPLEMENT NOW
  - Improve comparison answer formatting (side-by-side metrics)
  - Improve root cause answer formatting (what changed, why risky, action)
  - Improve why-not answer formatting (stability explanation)
  - Improve traceability answer formatting (top contributing records)
  - **File**: `planning_intelligence/function_app.py` (enhance existing answer templates)
  - **Tests**: Add formatting tests for each type

- [ ] 6. Improve follow-up suggestion generation
  - **Status**: IMPLEMENT NOW
  - Generate 2-3 contextual suggestions per answer
  - Implement patterns for each intent type
  - Guide toward deeper analysis (drill-down, comparison, root cause)
  - **File**: `planning_intelligence/function_app.py` (enhance `_build_follow_ups()`)
  - **Tests**: Add follow-up generation tests

### Phase 3: Response Structure & Backward Compatibility

- [ ] 7. Enhance response structure for better clarity
  - **Status**: IMPLEMENT NOW
  - Add `answerMode` field (summary vs investigate)
  - Add `scopeType` and `scopeValue` fields
  - Add `supportingMetrics` section
  - Keep all existing fields unchanged (backward compatible)
  - **File**: `planning_intelligence/function_app.py` (in `explain()` response building)
  - **Tests**: Backward compatibility tests

- [ ] 8. Update CopilotPanel.tsx rendering
  - **Status**: IMPLEMENT NOW
  - Render greeting (if provided)
  - Render answer clearly separated from suggestions
  - Render follow-up suggestions one at a time (not all mixed together)
  - Show supporting metrics when relevant
  - **File**: `frontend/src/components/CopilotPanel.tsx`
  - **Tests**: Manual UI testing with real responses

### Phase 4: Testing & Validation

- [ ] 9. Write unit tests for improved entity extraction
  - **Status**: IMPLEMENT NOW
  - Test LOC\d+ pattern matching
  - Test SUP\d+, MAT\d+, material group patterns
  - Test edge cases (no entities, multiple entities)
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 10. Write unit tests for improved question classification
  - **Status**: IMPLEMENT NOW
  - Test each intent type (summary, comparison, root_cause, why_not, traceability)
  - Test confidence score computation
  - Test ambiguous questions
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 11. Write unit tests for response formatting
  - **Status**: IMPLEMENT NOW
  - Test comparison answer formatting
  - Test root cause answer formatting
  - Test why-not answer formatting
  - Test traceability answer formatting
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 12. Write unit tests for follow-up suggestions
  - **Status**: IMPLEMENT NOW
  - Test suggestions for each intent type
  - Test suggestion relevance
  - Test top-3 selection
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 13. Write integration tests with real blob data
  - **Status**: IMPLEMENT NOW
  - Test with real questions from blob storage
  - Test comparison prompts
  - Test why-not prompts
  - Test traceability prompts
  - Test root cause prompts
  - **File**: `planning_intelligence/tests/test_blob_integration.py`

- [ ] 14. Write backward compatibility tests
  - **Status**: IMPLEMENT NOW
  - Test existing clients without new fields
  - Verify all existing fields present and unchanged
  - Test response structure with and without new fields
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

- [ ] 15. Write response quality tests
  - **Status**: IMPLEMENT NOW
  - Test that answers are specific to question
  - Test that answers are not generic summaries
  - Test that answers use scoped metrics
  - Test that answers feel targeted and relevant
  - **File**: `planning_intelligence/tests/test_copilot_realtime.py`

### Phase 5: Documentation & Deployment

- [ ] 16. Update API documentation
  - **Status**: IMPLEMENT NOW
  - Document new response fields (answerMode, scopeType, scopeValue, supportingMetrics)
  - Document improved answer templates
  - Document follow-up suggestion patterns
  - **File**: `planning_intelligence/API_DOCUMENTATION_COPILOT.md`

- [ ] 17. Create Version 1.5 implementation guide
  - **Status**: IMPLEMENT NOW
  - Document changes to `function_app.py`
  - Document changes to `CopilotPanel.tsx`
  - Document testing approach
  - **File**: Create `.kiro/specs/copilot-personalization-conversational/VERSION_1_5_GUIDE.md`

- [ ] 18. Verify backward compatibility
  - **Status**: IMPLEMENT NOW
  - Test with real existing client requests
  - Verify all existing fields present
  - Verify new fields optional
  - **File**: Run backward compatibility tests

- [ ] 19. Final validation with blob data
  - **Status**: IMPLEMENT NOW
  - Run all tests with real blob storage data
  - Verify response quality improvements
  - Verify performance (< 500ms total response time)
  - **File**: Run integration tests

## Success Criteria - VERSION 1.5

- ✓ Comparison prompts handled better (side-by-side metrics)
- ✓ Why-not prompts handled better (stability explanation)
- ✓ Traceability prompts handled better (top contributing records)
- ✓ Root cause prompts handled better (what changed, why risky, action)
- ✓ Responses are specific to question (not generic summaries)
- ✓ Follow-up suggestions are contextual and relevant
- ✓ 100% backward compatible with existing clients
- ✓ All tests passing with real blob data
- ✓ Response time < 500ms
- ✓ No new parallel architecture introduced

## Notes - VERSION 1.5

- All changes are additive (no breaking changes)
- Existing `/explain` endpoint remains primary
- New response fields are optional
- No conversation persistence or pronoun resolution
- No new endpoints created
- Focus on answer quality and prompt handling
- Keep implementation simple and focused
