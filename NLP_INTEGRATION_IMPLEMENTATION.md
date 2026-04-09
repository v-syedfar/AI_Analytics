# NLP/LLM Integration Implementation Guide

**Status:** ✅ READY TO IMPLEMENT  
**Date:** April 9, 2026  
**Effort:** 30 minutes to integrate

---

## What Was Created

### New File: `planning_intelligence/nlp_endpoint.py`

This file contains:
- `NLPEndpointHandler` class - Orchestrates NLP processing
- `handle_nlp_query()` function - HTTP endpoint handler
- Out-of-scope detection
- Conversation history tracking
- Multi-turn support

**Key Features:**
- ✅ Natural language question processing
- ✅ Intent classification
- ✅ Entity extraction
- ✅ Multi-turn conversation support
- ✅ Out-of-scope question handling
- ✅ Conversation history tracking

---

## How to Integrate into function_app.py

### Step 1: Add Import

Add this to the imports section of `planning_intelligence/function_app.py`:

```python
from nlp_endpoint import handle_nlp_query
```

### Step 2: Add HTTP Route

Add this new endpoint to `planning_intelligence/function_app.py`:

```python
@app.route(route="planning_intelligence_nlp", methods=["POST"])
def planning_intelligence_nlp(req: func.HttpRequest) -> func.HttpResponse:
    """
    Natural Language Processing endpoint for Copilot UI.
    
    Accepts natural language questions and processes them through the NLP pipeline.
    
    Request body:
    {
        "question": "List suppliers for CYS20_F01C01",
        "detail_records": [...],
        "conversation_history": [...]  # Optional
    }
    
    Response:
    {
        "question": "List suppliers for CYS20_F01C01",
        "answer": "📊 CYS20_F01C01: 15 records total...",
        "queryType": "traceability",
        "scopeType": "location",
        "scopeValue": "CYS20_F01C01",
        "answerMode": "investigate",
        "confidence": 0.95,
        "conversationHistory": [...]
    }
    """
    return handle_nlp_query(req)
```

### Step 3: Update Copilot UI Integration

Update the Copilot UI to call the new endpoint:

**Old:**
```
POST /api/planning_intelligence
{
    "query_type": "summary",
    "current_rows": [...]
}
```

**New:**
```
POST /api/planning_intelligence_nlp
{
    "question": "What's the planning status?",
    "detail_records": [...],
    "conversation_history": [...]
}
```

---

## How It Works

### Example 1: Simple Query

**Input:**
```json
{
    "question": "What's the planning status?",
    "detail_records": [...]
}
```

**Processing:**
1. ✅ Classify question → "summary"
2. ✅ Extract scope → None (global)
3. ✅ Determine mode → "summary"
4. ✅ Compute metrics → Global metrics
5. ✅ Generate response → Summary template

**Output:**
```json
{
    "question": "What's the planning status?",
    "answer": "📊 Planning Intelligence Summary:\n\n**Overall Metrics:**\n  • Total Records: 13,148\n  • Changed Records: 5,150 (39.2% change rate)\n  • Primary Driver: Quantity\n\n...",
    "queryType": "summary",
    "scopeType": null,
    "scopeValue": null,
    "answerMode": "summary",
    "confidence": 0.95,
    "conversationHistory": [...]
}
```

### Example 2: Scoped Query

**Input:**
```json
{
    "question": "Why is LOC001 risky?",
    "detail_records": [...]
}
```

**Processing:**
1. ✅ Classify question → "root_cause"
2. ✅ Extract scope → location = "LOC001"
3. ✅ Determine mode → "investigate"
4. ✅ Compute metrics → Scoped metrics for LOC001
5. ✅ Generate response → Root cause template

**Output:**
```json
{
    "question": "Why is LOC001 risky?",
    "answer": "⚠️ Risk Analysis for LOC001:\n\n**What Changed:** 2 of 3 records have changed (66.7%)\n\n**Why It's Risky:** The primary driver is quantity changes\n\n...",
    "queryType": "root_cause",
    "scopeType": "location",
    "scopeValue": "LOC001",
    "answerMode": "investigate",
    "confidence": 0.95,
    "conversationHistory": [...]
}
```

### Example 3: Out-of-Scope Query

**Input:**
```json
{
    "question": "What is your name?",
    "detail_records": [...]
}
```

**Processing:**
1. ✅ Detect out-of-scope → True
2. ✅ Generate out-of-scope response

**Output:**
```json
{
    "question": "What is your name?",
    "answer": "I'm a Planning Intelligence assistant specialized in analyzing planning data.\n\nI can help you with questions like:\n- \"What's the planning status?\"\n- \"Why is LOC001 risky?\"\n...",
    "queryType": "out_of_scope",
    "scopeType": null,
    "scopeValue": null,
    "answerMode": "summary",
    "confidence": 1.0,
    "conversationHistory": [...]
}
```

### Example 4: Multi-turn Conversation

**Turn 1 Input:**
```json
{
    "question": "What's the planning status?",
    "detail_records": [...]
}
```

**Turn 1 Output:**
```json
{
    "question": "What's the planning status?",
    "answer": "📊 Planning Intelligence Summary: ...",
    "queryType": "summary",
    "conversationHistory": [
        {
            "question": "What's the planning status?",
            "answer": "📊 Planning Intelligence Summary: ...",
            "queryType": "summary",
            "timestamp": "2026-04-09T10:00:00"
        }
    ]
}
```

**Turn 2 Input:**
```json
{
    "question": "Which location has the most changes?",
    "detail_records": [...],
    "conversation_history": [
        {
            "question": "What's the planning status?",
            "answer": "📊 Planning Intelligence Summary: ...",
            "queryType": "summary",
            "timestamp": "2026-04-09T10:00:00"
        }
    ]
}
```

**Turn 2 Output:**
```json
{
    "question": "Which location has the most changes?",
    "answer": "📊 Location Analysis: ...",
    "queryType": "traceability",
    "conversationHistory": [
        {
            "question": "What's the planning status?",
            "answer": "📊 Planning Intelligence Summary: ...",
            "queryType": "summary",
            "timestamp": "2026-04-09T10:00:00"
        },
        {
            "question": "Which location has the most changes?",
            "answer": "📊 Location Analysis: ...",
            "queryType": "traceability",
            "timestamp": "2026-04-09T10:00:05"
        }
    ]
}
```

---

## Supported Query Types

### 1. Summary
**Pattern:** "What's the planning status?"
**Response:** Overall metrics and drivers

### 2. Root Cause
**Pattern:** "Why is LOC001 risky?"
**Response:** Risk analysis for specific entity

### 3. Comparison
**Pattern:** "Compare LOC001 vs LOC002"
**Response:** Side-by-side comparison

### 4. Why-Not
**Pattern:** "Why is LOC002 not risky?"
**Response:** Stability analysis

### 5. Traceability
**Pattern:** "Show top contributing records"
**Response:** List of top records

### 6. Out-of-Scope
**Pattern:** "What is your name?"
**Response:** Clarification about capabilities

---

## Testing the Integration

### Test 1: Basic Query
```bash
curl -X POST http://localhost:7071/api/planning_intelligence_nlp \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the planning status?",
    "detail_records": [...]
  }'
```

### Test 2: Scoped Query
```bash
curl -X POST http://localhost:7071/api/planning_intelligence_nlp \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Why is LOC001 risky?",
    "detail_records": [...]
  }'
```

### Test 3: Multi-turn
```bash
# Turn 1
curl -X POST http://localhost:7071/api/planning_intelligence_nlp \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the planning status?",
    "detail_records": [...]
  }' > response1.json

# Turn 2 (use conversation_history from response1)
curl -X POST http://localhost:7071/api/planning_intelligence_nlp \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Which location has the most changes?",
    "detail_records": [...],
    "conversation_history": <from response1>
  }'
```

---

## Expected Results After Integration

### ✅ Before Integration (Current Issue):
```
Query: "List suppliers for CYS20_F01C01"
Response: Same generic response repeated twice ❌
```

### ✅ After Integration (Fixed):
```
Query: "List suppliers for CYS20_F01C01"
Response: Specific supplier list for CYS20_F01C01 ✅
```

### ✅ Before Integration (Current Issue):
```
Query: "Which materials are affected?"
Response: Ignored (no processing) ❌
```

### ✅ After Integration (Fixed):
```
Query: "Which materials are affected?"
Response: List of affected materials ✅
```

### ✅ Before Integration (Current Issue):
```
Query: "What is your name?"
Response: Planning summary (wrong response) ❌
```

### ✅ After Integration (Fixed):
```
Query: "What is your name?"
Response: Out-of-scope clarification ✅
```

---

## Performance Expectations

### Response Time:
- Query processing: < 500ms
- Response generation: < 1s
- Total end-to-end: < 2s

### Scalability:
- 1,000 records: < 1 second
- 10,000 records: < 5 seconds
- 100,000 records: < 30 seconds

---

## Deployment Steps

### Step 1: Add nlp_endpoint.py
- Copy `planning_intelligence/nlp_endpoint.py` to Azure

### Step 2: Update function_app.py
- Add import: `from nlp_endpoint import handle_nlp_query`
- Add route: `@app.route(route="planning_intelligence_nlp", methods=["POST"])`
- Add handler function

### Step 3: Update Copilot UI
- Change endpoint from `/api/planning_intelligence` to `/api/planning_intelligence_nlp`
- Update request format to include `question` instead of `query_type`

### Step 4: Test
- Run integration tests
- Test multi-turn conversations
- Monitor performance

### Step 5: Deploy
- Deploy to Azure
- Monitor for issues
- Collect user feedback

---

## Rollback Plan

If issues occur:

1. **Keep old endpoint** - `planning_intelligence` endpoint still works
2. **Revert Copilot UI** - Switch back to old endpoint
3. **Debug** - Identify and fix issues
4. **Re-deploy** - Deploy fixed version

---

## Success Criteria

### ✅ Integration Successful When:

1. Natural language questions are processed (not ignored)
2. Intent is correctly classified
3. Entities are extracted properly
4. Correct response generated for each question
5. Multi-turn context maintained
6. Out-of-scope handled gracefully
7. Performance < 2s response time
8. No duplicate responses

---

## Next Steps

1. **Today:** Review this implementation guide
2. **Today:** Add nlp_endpoint.py to planning_intelligence/
3. **Today:** Update function_app.py with new endpoint
4. **Tomorrow:** Test integration locally
5. **Tomorrow:** Deploy to Azure
6. **Tomorrow:** Update Copilot UI
7. **Tomorrow:** Monitor and optimize

---

## Files Involved

### New Files:
- ✅ `planning_intelligence/nlp_endpoint.py` - NLP endpoint handler

### Modified Files:
- `planning_intelligence/function_app.py` - Add import and route
- Copilot UI configuration - Update endpoint URL

### Unchanged Files:
- `planning_intelligence/phase1_core_functions.py` - Already correct
- `planning_intelligence/phase2_answer_templates.py` - Already correct
- `planning_intelligence/phase3_integration.py` - Already correct

---

## Support & Troubleshooting

### Issue: "Module not found: nlp_endpoint"
**Solution:** Ensure `nlp_endpoint.py` is in the same directory as `function_app.py`

### Issue: "Question not being processed"
**Solution:** Check that question is not empty and detail_records is provided

### Issue: "Wrong response type"
**Solution:** Check question classification in QuestionClassifier

### Issue: "Performance slow"
**Solution:** Check detail_records size and optimize metrics computation

---

**Status:** ✅ READY FOR IMPLEMENTATION  
**Effort:** 30 minutes  
**Impact:** Enables full NLP/LLM integration with Copilot UI

