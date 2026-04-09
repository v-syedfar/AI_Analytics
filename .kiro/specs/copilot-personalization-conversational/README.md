# Copilot Personalization & Conversational AI - Spec Overview

## Quick Navigation

**Start Here**:
1. `SCOPING_DECISION.md` - Why Version 1.5 instead of full plan
2. `VERSION_1_5_QUICK_START.md` - Quick reference for Version 1.5
3. `tasks.md` - Detailed task list for Version 1.5

**Reference**:
- `TASK_CLASSIFICATION.md` - Which tasks are in/out
- `VERSION_2_DESIGN_NOTE.md` - What's deferred to Version 2
- `requirements.md` - Full requirements (includes Version 2)
- `design.md` - Full design (includes Version 2)

---

## What is This Spec?

This spec documents the enhancement of the Copilot with better intent classification, entity extraction, response formatting, and follow-up suggestions.

**Version 1.5** (Implement Now): Immediate answer quality improvements
**Version 2** (Defer): Full conversational architecture

---

## Version 1.5 at a Glance

### What Gets Better
- ✓ Comparison prompts (side-by-side metrics)
- ✓ Why-not prompts (stability explanation)
- ✓ Traceability prompts (top contributing records)
- ✓ Root cause prompts (what changed, why risky, action)
- ✓ Response specificity (not generic summaries)
- ✓ Follow-up suggestions (contextual, not mixed together)

### What Gets Implemented
- Improve entity extraction in `_extract_scope()`
- Improve intent classification in `_classify_question()`
- Improve response filtering in `_generate_answer_from_context()`
- Improve follow-up suggestions in `_build_follow_ups()`
- Add response structure fields (answerMode, scopeType, supportingMetrics)
- Update CopilotPanel.tsx rendering
- Write comprehensive tests

### What Does NOT Get Implemented
- ❌ Conversation persistence
- ❌ Pronoun resolution
- ❌ Personalization manager
- ❌ New `/explain-conversational` endpoint
- ❌ Async follow-up generation
- ❌ Caching layer

### Implementation Effort
- **Time**: 24 hours
- **Complexity**: Low (extend existing code)
- **Risk**: Low (backward compatible)
- **Files Modified**: 5
- **Files Created**: 0 (no new modules)

### Success Criteria
- ✓ Comparison prompts handled better
- ✓ Why-not prompts handled better
- ✓ Traceability prompts handled better
- ✓ Root cause prompts handled better
- ✓ Responses are specific to question
- ✓ Follow-up suggestions are contextual
- ✓ 100% backward compatible
- ✓ All tests passing
- ✓ Response time < 500ms

---

## Version 2 at a Glance (Deferred)

### What Gets Deferred
- Conversation persistence and state management
- Pronoun and reference resolution
- Personalization manager
- New `/explain-conversational` endpoint
- Async follow-up generation
- Caching layer

### Why Defer?
- Requires stable Version 1.5 foundation
- Adds architectural complexity
- Not critical for current needs
- Can be added later without breaking changes
- Allows time to gather user feedback

### When to Implement?
- After Version 1.5 is stable and proven
- After user feedback informs design
- After deterministic analytics Copilot is fully mature
- Timeline: 2-3 weeks after Version 1.5

---

## Files in This Spec

### Documentation
- `README.md` - This file
- `SCOPING_DECISION.md` - Why Version 1.5 instead of full plan
- `VERSION_1_5_QUICK_START.md` - Quick reference for Version 1.5
- `TASK_CLASSIFICATION.md` - Which tasks are in/out
- `VERSION_2_DESIGN_NOTE.md` - What's deferred to Version 2

### Spec Documents
- `requirements.md` - Full requirements (includes Version 2)
- `design.md` - Full design (includes Version 2)
- `tasks.md` - Detailed task list (Version 1.5 only)

### Config
- `.config.kiro` - Spec metadata

---

## How to Use This Spec

### For Implementation
1. Read `SCOPING_DECISION.md` to understand the decision
2. Read `VERSION_1_5_QUICK_START.md` for quick reference
3. Open `tasks.md` to see the Version 1.5 task list
4. Start with Phase 1 (Tasks 1-3)
5. Run tests frequently
6. Verify backward compatibility

### For Reference
1. See `TASK_CLASSIFICATION.md` for task breakdown
2. See `VERSION_2_DESIGN_NOTE.md` for deferred features
3. See `requirements.md` for full requirements
4. See `design.md` for full design

### For Future Planning
1. Read `VERSION_2_DESIGN_NOTE.md` for Version 2 scope
2. Plan Version 2 after Version 1.5 is stable
3. Gather user feedback on Version 1.5
4. Use feedback to refine Version 2 design

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

## Implementation Phases

### Phase 1: Intent Classification & Entity Extraction (Tasks 1-3)
- Improve `_extract_scope()` function
- Improve `_classify_question()` function
- Add prompt validation and routing
- **Effort**: ~4 hours

### Phase 2: Response Formatting & Quality (Tasks 4-6)
- Improve response filtering
- Enhance answer formatting for each type
- Improve follow-up suggestions
- **Effort**: ~6 hours

### Phase 3: Response Structure & UI (Tasks 7-8)
- Add new response fields
- Update CopilotPanel.tsx rendering
- **Effort**: ~4 hours

### Phase 4: Testing & Validation (Tasks 9-19)
- Write unit tests
- Write integration tests
- Write backward compatibility tests
- Write performance tests
- **Effort**: ~8 hours

### Phase 5: Documentation & Deployment (Tasks 16-19)
- Update API documentation
- Create implementation guide
- Verify backward compatibility
- Final validation
- **Effort**: ~2 hours

**Total Effort**: ~24 hours

---

## Files to Modify

### Backend
- `planning_intelligence/function_app.py` - Enhance existing functions
  - Improve `_extract_scope()`
  - Improve `_classify_question()`
  - Improve `_generate_answer_from_context()`
  - Improve `_build_follow_ups()`

### Frontend
- `frontend/src/components/CopilotPanel.tsx` - Better rendering

### Tests
- `planning_intelligence/tests/test_copilot_realtime.py` - Add tests
- `planning_intelligence/tests/test_blob_integration.py` - Integration tests

### Documentation
- `planning_intelligence/API_DOCUMENTATION_COPILOT.md` - Update docs

---

## Success Metrics

### Version 1.5 Success
- ✓ Comparison prompts handled better (user feedback)
- ✓ Why-not prompts handled better (user feedback)
- ✓ Traceability prompts handled better (user feedback)
- ✓ Root cause prompts handled better (user feedback)
- ✓ Responses are specific to question (user feedback)
- ✓ Follow-up suggestions are contextual (user feedback)
- ✓ 100% backward compatible (automated tests)
- ✓ All tests passing (automated tests)
- ✓ Response time < 500ms (performance tests)
- ✓ No new architecture introduced (code review)

---

## Next Steps

1. **Review**: Read `SCOPING_DECISION.md` to understand the decision
2. **Understand**: Read `VERSION_1_5_QUICK_START.md` for quick reference
3. **Plan**: Review `tasks.md` to see the Version 1.5 task list
4. **Implement**: Start with Phase 1 (Tasks 1-3)
5. **Test**: Run tests frequently
6. **Verify**: Verify backward compatibility
7. **Deploy**: Deploy Version 1.5
8. **Gather**: Gather user feedback
9. **Plan**: Plan Version 2 based on feedback

---

## Questions?

- **Why Version 1.5?** See `SCOPING_DECISION.md`
- **What's in Version 1.5?** See `VERSION_1_5_QUICK_START.md`
- **What's deferred?** See `VERSION_2_DESIGN_NOTE.md`
- **Which tasks?** See `TASK_CLASSIFICATION.md`
- **How to implement?** See `tasks.md`
- **Full requirements?** See `requirements.md`
- **Full design?** See `design.md`

---

## Document Versions

- **Spec Version**: 1.5 (Scoped)
- **Created**: 2026-04-07
- **Status**: Ready for Implementation
- **Next Review**: After Version 1.5 deployment
