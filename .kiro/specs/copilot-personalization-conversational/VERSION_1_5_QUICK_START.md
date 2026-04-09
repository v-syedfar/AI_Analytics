# Version 1.5 Quick Start Guide

## What is Version 1.5?

Version 1.5 is a **scoped implementation** focused on immediate improvements to Copilot answer quality and prompt handling.

**NOT included**: Full conversational architecture, conversation persistence, pronoun resolution, personalization manager, new endpoints.

**Included**: Better entity extraction, intent classification, response formatting, follow-up suggestions.

---

## What Gets Better in Version 1.5?

### 1. Comparison Prompts
**Before**: Generic summary, doesn't compare
**After**: Side-by-side metrics for both entities

### 2. Why-Not Prompts
**Before**: Generic summary, doesn't explain stability
**After**: Clear explanation of why entity is stable

### 3. Traceability Prompts
**Before**: Generic summary, no records shown
**After**: Top contributing records with metrics

### 4. Root Cause Prompts
**Before**: Generic summary, doesn't explain why risky
**After**: What changed, why it's risky, recommended action

### 5. Response Specificity
**Before**: All suggestions mixed together
**After**: Clear answer + contextual follow-ups

---

## Implementation Strategy

### Files to Modify

**Backend**:
- `planning_intelligence/function_app.py` - Enhance existing functions
  - Improve `_extract_scope()` for better entity extraction
  - Improve `_classify_question()` for better intent classification
  - Improve `_generate_answer_from_context()` for better response formatting
  - Improve `_build_follow_ups()` for better suggestions

**Frontend**:
- `frontend/src/components/CopilotPanel.tsx` - Better rendering
  - Render greeting (if provided)
  - Render answer clearly
  - Render follow-ups one at a time (not mixed together)

**Tests**:
- `planning_intelligence/tests/test_copilot_realtime.py` - Add tests
- `planning_intelligence/tests/test_blob_integration.py` - Integration tests

### Files NOT to Create

- ❌ `conversational_layer.py`
- ❌ `conversation_manager.py`
- ❌ `personalization_manager.py`
- ❌ `cache_manager.py`
- ❌ New `/explain-conversational` endpoint

---

## Implementation Phases

### Phase 1: Intent Classification & Entity Extraction (Tasks 1-3)
- Improve `_extract_scope()` function
- Improve `_classify_question()` function
- Add prompt validation and routing

**Effort**: ~4 hours
**Files**: `function_app.py`

### Phase 2: Response Formatting & Quality (Tasks 4-6)
- Improve response filtering
- Enhance answer formatting for each type
- Improve follow-up suggestions

**Effort**: ~6 hours
**Files**: `function_app.py`

### Phase 3: Response Structure & UI (Tasks 7-8)
- Add new response fields (answerMode, scopeType, supportingMetrics)
- Update CopilotPanel.tsx rendering

**Effort**: ~4 hours
**Files**: `function_app.py`, `CopilotPanel.tsx`

### Phase 4: Testing & Validation (Tasks 9-19)
- Write unit tests
- Write integration tests
- Write backward compatibility tests
- Write performance tests

**Effort**: ~8 hours
**Files**: `test_copilot_realtime.py`, `test_blob_integration.py`

### Phase 5: Documentation & Deployment (Tasks 16-19)
- Update API documentation
- Create implementation guide
- Verify backward compatibility
- Final validation

**Effort**: ~2 hours
**Files**: `API_DOCUMENTATION_COPILOT.md`, `VERSION_1_5_GUIDE.md`

**Total Effort**: ~24 hours

---

## Key Principles

### 1. Backward Compatibility
- All existing fields remain unchanged
- New fields are optional
- Existing clients continue to work
- No breaking changes

### 2. Incremental Changes
- Extend existing functions, don't replace them
- Keep changes focused and testable
- Test each change independently
- Integrate gradually

### 3. Answer Quality Focus
- Improve specificity to question
- Remove generic summaries
- Add supporting metrics
- Make responses feel targeted

### 4. Simple Architecture
- No new parallel architecture
- No conversation persistence
- No pronoun resolution
- No personalization manager
- Keep it simple and focused

---

## Testing Strategy

### Unit Tests
- Entity extraction (LOC\d+, SUP\d+, MAT\d+)
- Intent classification (each type)
- Response formatting (each type)
- Follow-up suggestions (each type)

### Integration Tests
- Full flow with real blob data
- Comparison prompts
- Why-not prompts
- Traceability prompts
- Root cause prompts

### Backward Compatibility Tests
- Existing clients without new fields
- Response includes all existing fields
- New fields don't break existing clients

### Performance Tests
- Intent classification < 30ms
- Response formatting < 30ms
- Follow-up generation < 50ms
- Total response time < 500ms

---

## Success Criteria

- ✓ Comparison prompts handled better
- ✓ Why-not prompts handled better
- ✓ Traceability prompts handled better
- ✓ Root cause prompts handled better
- ✓ Responses are specific to question
- ✓ Follow-up suggestions are contextual
- ✓ 100% backward compatible
- ✓ All tests passing
- ✓ Response time < 500ms
- ✓ No new architecture introduced

---

## What's NOT in Version 1.5

- ❌ Conversation persistence
- ❌ Pronoun resolution ("Tell me more" → previous entity)
- ❌ Personalization (greetings, user context)
- ❌ Multi-turn conversation tracking
- ❌ New `/explain-conversational` endpoint
- ❌ Async follow-up generation
- ❌ Caching layer
- ❌ Conversation storage

These will be in **Version 2** (future).

---

## What's in Version 2 (Future)

See `VERSION_2_DESIGN_NOTE.md` for details on:
- Conversation persistence
- Pronoun resolution
- Personalization manager
- New `/explain-conversational` endpoint
- Async follow-up generation
- Caching layer

---

## Getting Started

1. Read this guide
2. Review `TASK_CLASSIFICATION.md` to understand what's in/out
3. Open `tasks.md` to see the Version 1.5 task list
4. Start with Phase 1 (Tasks 1-3)
5. Run tests frequently
6. Verify backward compatibility

---

## Questions?

- See `VERSION_2_DESIGN_NOTE.md` for deferred features
- See `TASK_CLASSIFICATION.md` for task breakdown
- See `tasks.md` for detailed task list
- See `design.md` for full design (includes Version 2 concepts)
