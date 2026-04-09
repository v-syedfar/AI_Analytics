# Version 2 Design Note: Full Conversational Layer (DEFERRED)

**Status**: DESIGN ONLY - DO NOT IMPLEMENT YET

**Rationale**: Version 1.5 focuses on immediate answer quality improvements. Version 2 will add full conversational capabilities once the deterministic analytics Copilot is fully stable.

---

## What Version 2 Will Add

### 1. Conversation Persistence & State Management

**Components to build**:
- `ConversationState` class - Track multi-turn conversation history
- `ConversationTurn` class - Individual turn data
- Conversation storage layer (optional server-side or client-side)
- Conversation ID generation and lookup

**Capabilities**:
- Load conversation history from storage
- Save conversation state after each turn
- Maintain last 5-10 turns for context
- Track "current focus" (location, material_group, etc.)

**Files to create**:
- `planning_intelligence/conversation_manager.py` (new module)

---

### 2. Pronoun & Reference Resolution

**Components to build**:
- `resolve_references()` function
- Pronoun resolution (it, this, that, these, those)
- Implicit reference resolution (previous entity)
- "Tell me more" expansion
- "Compare this to X" resolution

**Capabilities**:
- Resolve pronouns to previous entities
- Expand implicit references
- Handle failed resolution gracefully
- Suggest clarification when ambiguous

**Files to modify**:
- `planning_intelligence/conversation_manager.py`

---

### 3. Personalization Manager

**Components to build**:
- `PersonalizationContext` class
- `generate_greeting()` function
- `personalize_response()` function
- User context extraction

**Capabilities**:
- Generate personalized greetings
- Include user name, role, location focus
- Vary tone based on health status
- Add context-aware touches to answers

**Files to create**:
- `planning_intelligence/personalization_manager.py` (new module)

---

### 4. New Conversational Endpoint

**Endpoint to create**:
- `/explain-conversational` (new route)
- Wraps existing `/explain` endpoint
- Adds conversation management
- Adds personalization
- Maintains backward compatibility

**Request structure**:
```json
{
  "question": "Why is LOC001 risky?",
  "conversation_id": "conv_123",
  "user_context": {
    "user_id": "user_456",
    "name": "John",
    "role": "planner"
  }
}
```

**Response structure**:
```json
{
  "personalization": {
    "greeting": "Hi John, I see you're focused on LOC001...",
    "conversation_id": "conv_123",
    "turn_number": 1
  },
  "question": "Why is LOC001 risky?",
  "answer": "In LOC001, quantity changed significantly...",
  "follow_up_questions": [...],
  "conversation_context": {...},
  ...existing fields...
}
```

**Files to modify**:
- `planning_intelligence/function_app.py` (add new route)

---

### 5. Async Follow-Up Generation

**Optimization to add**:
- Generate follow-ups asynchronously if needed
- Return answer immediately
- Return follow-ups in background or next request
- Implement async task queue

**Files to modify**:
- `planning_intelligence/function_app.py`

---

### 6. Caching Layer

**Optimizations to add**:
- Cache intent classifications for common questions
- Cache conversation summaries
- Cache follow-up suggestions
- Implement cache invalidation strategy

**Files to create**:
- `planning_intelligence/cache_manager.py` (new module)

---

## Architecture for Version 2

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         /explain-conversational Endpoint (NEW)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Conversation Manager                               │   │
│  │ • Personalization Manager                            │   │
│  │ • Reference Resolution                               │   │
│  │ • Async Follow-Up Generation                         │   │
│  │ • Caching Layer                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         /explain Endpoint (EXISTING - UNCHANGED)            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Intent Classification                              │   │
│  │ • Entity Extraction                                  │   │
│  │ • Response Formatting (Version 1.5 improvements)     │   │
│  │ • Follow-Up Suggestions (Version 1.5 improvements)   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap for Version 2

### Phase 1: Conversation Management (Week 1)
- Implement `ConversationState` and `ConversationTurn` classes
- Implement conversation storage and retrieval
- Implement conversation turn tracking
- Write unit tests

### Phase 2: Reference Resolution (Week 2)
- Implement pronoun resolution
- Implement implicit reference resolution
- Implement "Tell me more" expansion
- Write unit tests

### Phase 3: Personalization (Week 2)
- Implement `PersonalizationContext` class
- Implement greeting generation
- Implement response personalization
- Write unit tests

### Phase 4: Integration (Week 3)
- Create `/explain-conversational` endpoint
- Integrate conversation manager
- Integrate personalization manager
- Implement backward compatibility

### Phase 5: Optimization (Week 3)
- Implement async follow-up generation
- Implement caching layer
- Performance testing
- Optimization

### Phase 6: Testing & Deployment (Week 4)
- Integration tests
- Backward compatibility tests
- Performance tests
- Deployment

---

## Success Criteria for Version 2

- ✓ Multi-turn conversations work correctly
- ✓ Pronouns resolved accurately
- ✓ Personalization feels natural
- ✓ Greetings include user context
- ✓ Follow-ups generated asynchronously
- ✓ Caching improves performance
- ✓ 100% backward compatible
- ✓ All tests passing
- ✓ Response time < 500ms

---

## Dependencies for Version 2

- Version 1.5 must be complete and stable
- Deterministic analytics Copilot must be fully stable
- User context must be available in requests
- Conversation storage infrastructure must be available

---

## Future Enhancements Beyond Version 2

1. **LLM-Based Personalization**
   - Use LLM for more natural greetings
   - Generate more varied follow-ups
   - Improve response formatting

2. **Multi-User Conversations**
   - Support team discussions
   - Track who asked what
   - Maintain shared context

3. **Conversation Export**
   - Export conversation as report
   - Share conversation with team
   - Archive for audit trail

4. **Predictive Follow-Ups**
   - Learn from user behavior
   - Suggest questions users typically ask next
   - Personalize suggestions per user

5. **Conversation Analytics**
   - Track common question patterns
   - Identify knowledge gaps
   - Improve system based on usage

---

## Notes

- Version 2 is a design note only - do not implement yet
- Version 1.5 must be complete and stable first
- Version 2 will be a separate spec when ready
- All Version 2 components will be optional (backward compatible)
- Version 2 will not break existing clients
- Version 2 will build on top of Version 1.5 improvements
