# function_app.py Changes Required

**File:** `planning_intelligence/function_app.py`  
**Changes:** Add NLP endpoint integration  
**Effort:** 5 minutes  
**Impact:** Enables natural language processing

---

## Change 1: Add Import

**Location:** Top of file, with other imports

**Add this line:**
```python
from nlp_endpoint import handle_nlp_query
```

**Full imports section should look like:**
```python
import json
import logging
from typing import Optional, List
import azure.functions as func

from normalizer import normalize_rows
from filters import filter_records
from comparator import compare_records
from analytics import (
    build_summary,
    build_location_material_list,
    filter_by_supplier_design_change,
    changes_by_location,
    changes_by_material_group,
    change_driver_analysis,
    high_risk_records,
)
from trend_analyzer import (
    analyze_trends,
    build_trend_summary,
    get_consistently_increasing,
    get_recurring_changes,
    get_one_off_spikes,
    get_change_streaks,
)
from dashboard_builder import build_dashboard_response
from response_builder import build_response
from snapshot_store import load_snapshot, snapshot_exists, get_last_updated_time
from reasoning_engine import ReasoningEngine
from clarification_engine import ClarificationEngine
from enhanced_intent_parser import EnhancedIntentParser
from nlp_endpoint import handle_nlp_query  # ← ADD THIS LINE

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
```

---

## Change 2: Add NLP Endpoint

**Location:** After the existing `planning_intelligence` endpoint (around line 250)

**Add this new endpoint:**
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
    logging.info("Planning Intelligence NLP endpoint triggered.")
    return handle_nlp_query(req)
```

---

## Complete Example

Here's what the relevant section of function_app.py should look like:

```python
import json
import logging
from typing import Optional, List
import azure.functions as func

from normalizer import normalize_rows
from filters import filter_records
from comparator import compare_records
from analytics import (
    build_summary,
    build_location_material_list,
    filter_by_supplier_design_change,
    changes_by_location,
    changes_by_material_group,
    change_driver_analysis,
    high_risk_records,
)
from trend_analyzer import (
    analyze_trends,
    build_trend_summary,
    get_consistently_increasing,
    get_recurring_changes,
    get_one_off_spikes,
    get_change_streaks,
)
from dashboard_builder import build_dashboard_response
from response_builder import build_response
from snapshot_store import load_snapshot, snapshot_exists, get_last_updated_time
from reasoning_engine import ReasoningEngine
from clarification_engine import ClarificationEngine
from enhanced_intent_parser import EnhancedIntentParser
from nlp_endpoint import handle_nlp_query  # ← NEW IMPORT

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# ... existing code ...

@app.route(route="planning_intelligence", methods=["POST"])
def planning_intelligence(req: func.HttpRequest) -> func.HttpResponse:
    # ... existing implementation ...
    pass

# ← ADD NEW ENDPOINT HERE
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
    logging.info("Planning Intelligence NLP endpoint triggered.")
    return handle_nlp_query(req)

# ... rest of existing code ...
```

---

## Testing the Changes

### Test 1: Basic Query
```bash
curl -X POST http://localhost:7071/api/planning_intelligence_nlp \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the planning status?",
    "detail_records": [
      {
        "LOCID": "LOC001",
        "LOCFR": "SUP001",
        "PRDID": "MAT001",
        "GSCEQUIPCAT": "UPS",
        "changed": true,
        "qtyChanged": true,
        "supplierChanged": false,
        "designChanged": false,
        "scheduleChanged": false
      }
    ]
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

### Test 3: Out-of-Scope Query
```bash
curl -X POST http://localhost:7071/api/planning_intelligence_nlp \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your name?",
    "detail_records": [...]
  }'
```

---

## Verification Checklist

After making changes:

- [ ] Import added to top of file
- [ ] New endpoint added after existing endpoints
- [ ] Endpoint has correct route name: `planning_intelligence_nlp`
- [ ] Endpoint has correct HTTP method: `POST`
- [ ] Endpoint calls `handle_nlp_query(req)`
- [ ] File saves without syntax errors
- [ ] Local testing works
- [ ] Azure deployment successful

---

## Rollback Instructions

If you need to revert:

1. **Remove the import:**
   ```python
   from nlp_endpoint import handle_nlp_query  # ← DELETE THIS LINE
   ```

2. **Remove the endpoint:**
   ```python
   @app.route(route="planning_intelligence_nlp", methods=["POST"])
   def planning_intelligence_nlp(req: func.HttpRequest) -> func.HttpResponse:
       # ← DELETE THIS ENTIRE FUNCTION
   ```

3. **Save and redeploy**

---

## Expected Results

### Before Changes:
```
POST /api/planning_intelligence_nlp
Response: 404 Not Found (endpoint doesn't exist)
```

### After Changes:
```
POST /api/planning_intelligence_nlp
{
    "question": "What's the planning status?",
    "detail_records": [...]
}

Response: 200 OK
{
    "question": "What's the planning status?",
    "answer": "📊 Planning Intelligence Summary: ...",
    "queryType": "summary",
    "confidence": 0.95,
    ...
}
```

---

## Summary

**Changes Required:**
1. Add 1 import line
2. Add 1 new endpoint function (15 lines)

**Total Lines Added:** ~16 lines

**Time Required:** 5 minutes

**Impact:** Enables full NLP/LLM integration with Copilot UI

---

**Status:** ✅ READY TO IMPLEMENT  
**Complexity:** LOW  
**Risk:** LOW  
**Benefit:** HIGH

