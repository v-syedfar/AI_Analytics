# NLP/LLM Integration Issue - Analysis & Solution

**Status:** 🔴 CRITICAL ISSUE IDENTIFIED  
**Date:** April 9, 2026  
**Severity:** HIGH - Affects all natural language queries

---

## Problem Summary

The Copilot UI is sending **natural language questions**, but the backend is **not processing them through the NLP/LLM layer**. Instead, it's returning default responses.

### Evidence from Copilot Responses:

```
Query: "List suppliers for CYS20_F01C01"
Response: Same generic response repeated twice

Query: "Which materials are affected?"
Response: Ignored (no processing)

Query: "What is your name?"
Response: Planning summary (wrong response type)

Query: "Is this demand-driven or design-driven?"
Response: Ignored (no processing)
```

---

## Root Cause Analysis

### Current Architecture Issue:

```
Copilot UI
    ↓
Natural Language Question
    ↓
function_app.py (planning_intelligence endpoint)
    ↓
Expects: query_type = "summary" | "comparison" | "root_cause" etc.
    ↓
❌ PROBLEM: No NLP layer to convert natural language → query_type
    ↓
Returns: Default response (ignores actual question)
```

### What Should Happen:

```
Copilot UI
    ↓
Natural Language Question
    ↓
function_app.py (planning_intelligence endpoint)
    ↓
✅ NLP Layer: Extract intent & entities
    ↓
✅ LLM Layer: Classify question type
    ↓
✅ Route to appropriate handler
    ↓
Returns: Correct response for the question
```

---

## Current System Components

### ✅ Components That Exist:

1. **phase1_core_functions.py**
   - QuestionClassifier - Classifies questions into 5 types
   - ScopeExtractor - Extracts entities (location, supplier, material)
   - AnswerModeDecider - Determines summary vs investigate mode
   - ScopedMetricsComputer - Computes metrics for scoped records

2. **phase2_answer_templates.py**
   - SummaryAnswerTemplate
   - RootCauseAnswerTemplate
   - ComparisonAnswerTemplate
   - WhyNotAnswerTemplate
   - TraceabilityAnswerTemplate

3. **phase3_integration.py**
   - IntegratedQueryProcessor - Orchestrates the pipeline
   - process_query() - Main entry point

4. **azure_openai_integration.py**
   - AzureOpenAIIntegration - LLM integration
   - extract_intent_and_entities()
   - generate_response()

### ❌ Problem:

**These components are NOT being called by function_app.py!**

The `planning_intelligence` endpoint in `function_app.py` expects a structured `query_type` parameter, not natural language questions.

---

## Issues Identified

### Issue #1: No NLP Entry Point
- ❌ Copilot sends natural language question
- ❌ function_app.py doesn't have NLP processing
- ❌ Question is ignored or returns default response

### Issue #2: Structured Query Type Mismatch
- ❌ Backend expects: `{"query_type": "summary", "current_rows": [...]}`
- ❌ Copilot sends: `{"question": "List suppliers for CYS20_F01C01"}`
- ❌ No translation layer between them

### Issue #3: Multi-turn Context Lost
- ❌ Follow-up questions aren't tracked
- ❌ Conversation history not maintained
- ❌ Each question treated independently

### Issue #4: Intent Not Routed
- ❌ "List suppliers" should route to supplier analysis
- ❌ "Which materials" should route to material analysis
- ❌ "Design changes" should route to design filter
- ❌ Currently all route to default handler

### Issue #5: Entity Extraction Not Used
- ❌ "CYS20_F01C01" should be extracted as location
- ❌ "design changes" should be extracted as change type
- ❌ Currently ignored

---

## Solution Architecture

### New Integration Flow:

```
Copilot UI
    ↓
Natural Language Question
    ↓
function_app.py (NEW: planning_intelligence_nlp endpoint)
    ↓
Phase 1: Intent & Scope Extraction
├─ QuestionClassifier.classify_question()
├─ ScopeExtractor.extract_scope()
└─ AnswerModeDecider.determine_answer_mode()
    ↓
Phase 2: Metrics Computation
├─ Load data from Blob Storage
├─ Filter to scope
└─ Compute metrics
    ↓
Phase 3: Response Generation
├─ AnswerTemplateRouter.generate_answer()
└─ Format response
    ↓
Returns: Correct response for the question
```

---

## Implementation Plan

### Step 1: Create NLP Entry Point
**File:** `planning_intelligence/function_app.py`

Add new endpoint:
```python
@app.route(route="planning_intelligence_nlp", methods=["POST"])
def planning_intelligence_nlp(req: func.HttpRequest) -> func.HttpResponse:
    """
    Natural Language Processing endpoint for Copilot UI.
    
    Accepts:
    {
        "question": "List suppliers for CYS20_F01C01",
        "detail_records": [...],
        "conversation_history": [...]  # Optional
    }
    
    Returns:
    {
        "question": "List suppliers for CYS20_F01C01",
        "answer": "📊 CYS20_F01C01: 15 records total...",
        "queryType": "traceability",
        "scopeType": "location",
        "scopeValue": "CYS20_F01C01",
        "answerMode": "investigate"
    }
    """
```

### Step 2: Integrate NLP Pipeline
```python
from phase1_core_functions import (
    QuestionClassifier,
    ScopeExtractor,
    AnswerModeDecider,
    ScopedMetricsComputer
)
from phase2_answer_templates import AnswerTemplateRouter
from phase3_integration import IntegratedQueryProcessor

# Process question through NLP pipeline
query_type = QuestionClassifier.classify_question(question)
scope_type, scope_value = ScopeExtractor.extract_scope(question)
answer_mode = AnswerModeDecider.determine_answer_mode(query_type, scope_type)

# Compute metrics
metrics = ScopedMetricsComputer.compute_scoped_metrics(
    detail_records, scope_type, scope_value
)

# Generate response
answer = AnswerTemplateRouter.generate_answer(
    query_type, answer_mode, scope_value, metrics, scope_type
)
```

### Step 3: Handle Multi-turn Context
```python
# Track conversation history
conversation_history = req.get_json().get("conversation_history", [])

# Add current question to history
conversation_history.append({
    "question": question,
    "answer": answer,
    "queryType": query_type,
    "timestamp": datetime.now().isoformat()
})

# Return with history for next turn
return {
    "question": question,
    "answer": answer,
    "queryType": query_type,
    "scopeType": scope_type,
    "scopeValue": scope_value,
    "answerMode": answer_mode,
    "conversationHistory": conversation_history[-5:]  # Last 5 turns
}
```

### Step 4: Update Copilot UI Integration
**File:** `planning_intelligence/function_app.py`

Update the endpoint that Copilot calls:
```python
# OLD: Expects structured query_type
@app.route(route="planning_intelligence", methods=["POST"])

# NEW: Accepts natural language
@app.route(route="planning_intelligence_nlp", methods=["POST"])
```

---

## Expected Behavior After Fix

### Query: "List suppliers for CYS20_F01C01"
```
Before:
❌ Same generic response repeated twice

After:
✅ Query classified as: traceability
✅ Scope extracted: location = CYS20_F01C01
✅ Answer mode: investigate
✅ Response: Specific supplier list for CYS20_F01C01
```

### Query: "Which materials are affected?"
```
Before:
❌ Ignored (no processing)

After:
✅ Query classified as: traceability
✅ Scope extracted: material_group = (all)
✅ Answer mode: investigate
✅ Response: List of affected materials
```

### Query: "What is your name?"
```
Before:
❌ Returns planning summary (wrong response)

After:
✅ Query classified as: out_of_scope
✅ Response: "I'm a Planning Intelligence assistant. I can help with planning questions."
```

### Query: "Is this demand-driven or design-driven?"
```
Before:
❌ Ignored (no processing)

After:
✅ Query classified as: root_cause
✅ Scope extracted: change_type = design
✅ Answer mode: investigate
✅ Response: Analysis of design-driven changes
```

---

## Files to Modify

### 1. planning_intelligence/function_app.py
- Add `planning_intelligence_nlp` endpoint
- Integrate NLP pipeline
- Handle multi-turn context
- Add error handling for out-of-scope questions

### 2. planning_intelligence/phase1_core_functions.py
- Add out-of-scope question detection
- Improve entity extraction for follow-up questions
- Add context-aware classification

### 3. planning_intelligence/phase2_answer_templates.py
- Add out-of-scope response template
- Add follow-up question handler
- Add clarification template

### 4. planning_intelligence/phase3_integration.py
- Add conversation history tracking
- Add context-aware processing
- Add multi-turn support

---

## Testing Plan

### Test Cases:

1. **Basic Query**
   - Input: "What's the planning status?"
   - Expected: Summary response

2. **Scoped Query**
   - Input: "Why is LOC001 risky?"
   - Expected: Root cause response for LOC001

3. **Comparison Query**
   - Input: "Compare LOC001 vs LOC002"
   - Expected: Comparison response

4. **Follow-up Query**
   - Input 1: "What's the planning status?"
   - Input 2: "Which location has the most changes?"
   - Expected: Context-aware response using previous answer

5. **Out-of-Scope Query**
   - Input: "What is your name?"
   - Expected: Out-of-scope response

6. **Multi-turn Conversation**
   - Input 1: "List suppliers for CYS20_F01C01"
   - Input 2: "Which materials are affected?"
   - Input 3: "Are there design changes?"
   - Expected: Context-aware responses for each

---

## Implementation Timeline

### Phase 1: NLP Entry Point (1-2 hours)
- Create `planning_intelligence_nlp` endpoint
- Integrate NLP pipeline
- Add basic error handling

### Phase 2: Multi-turn Support (2-3 hours)
- Add conversation history tracking
- Implement context-aware processing
- Add follow-up question handling

### Phase 3: Testing & Validation (2-3 hours)
- Create comprehensive test suite
- Validate all query types
- Test multi-turn conversations

### Phase 4: Deployment (1 hour)
- Deploy to Azure
- Update Copilot UI integration
- Monitor for issues

**Total Estimated Time:** 6-9 hours

---

## Deployment Checklist

### Before Deployment:
- [ ] NLP endpoint created
- [ ] All query types tested
- [ ] Multi-turn context working
- [ ] Out-of-scope handling working
- [ ] Error handling comprehensive
- [ ] Performance acceptable
- [ ] Documentation updated

### After Deployment:
- [ ] Monitor Copilot responses
- [ ] Track query success rate
- [ ] Collect user feedback
- [ ] Monitor performance metrics
- [ ] Plan Phase 2 enhancements

---

## Success Criteria

### ✅ NLP Integration Working When:

1. **Natural language questions are processed** - Not ignored
2. **Intent is correctly classified** - Right query type
3. **Entities are extracted** - Location, supplier, material identified
4. **Correct response generated** - Matches the question
5. **Multi-turn context maintained** - Follow-ups work
6. **Out-of-scope handled gracefully** - No wrong responses
7. **Performance acceptable** - < 2s response time
8. **No duplicate responses** - Each question answered once

---

## Risk Assessment

### Low Risk:
- ✅ Adding new endpoint (doesn't affect existing)
- ✅ Using existing NLP components (already tested)
- ✅ Backward compatible (old endpoint still works)

### Medium Risk:
- ⚠️ Multi-turn context tracking (new feature)
- ⚠️ Out-of-scope detection (needs tuning)

### Mitigation:
- Comprehensive testing before deployment
- Gradual rollout to subset of users
- Easy rollback to old endpoint
- Monitoring and alerting

---

## Next Steps

1. **Immediate:** Review this analysis with team
2. **Today:** Create NLP endpoint implementation
3. **Tomorrow:** Implement multi-turn support
4. **Day 3:** Comprehensive testing
5. **Day 4:** Deploy to Azure
6. **Day 5:** Monitor and optimize

---

**Status:** 🔴 CRITICAL - Needs immediate implementation  
**Priority:** HIGH - Blocks Copilot integration  
**Effort:** 6-9 hours  
**Impact:** Enables full NLP/LLM integration

