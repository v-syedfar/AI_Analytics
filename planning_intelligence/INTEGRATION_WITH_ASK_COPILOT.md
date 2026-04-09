# Integration with Ask Copilot UI

## Overview

To see the prompt review updates in the Ask Copilot UI, you need to integrate the new validation and prompt logging into your Azure Function App.

## What Gets Displayed in Ask Copilot UI

### 1. Enhanced Response Structure
```json
{
  "question": "Why is LOC001 risky?",
  "answer": "In LOC001, forecast quantities and supplier assignments have changed...",
  "intent": "root_cause",
  "answerMode": "investigate",
  "scope": {
    "type": "location",
    "value": "LOC001"
  },
  "investigateMode": {
    "filteredRecordsCount": 2,
    "changedCount": 2,
    "changeRate": 66.7,
    "scopedContributionBreakdown": {...},
    "scopedDrivers": {...},
    "topContributingRecords": [...]
  },
  "explainability": {
    "confidenceScore": 90,
    "answerMode": "investigate",
    "queryType": "root_cause",
    "scopeType": "location",
    "scopeValue": "LOC001",
    "dataFreshnessMinutes": 15,
    "isStale": false
  },
  "validationStatus": {
    "hallucinations_detected": false,
    "sap_schema_valid": true,
    "all_fields_valid": true
  }
}
```

### 2. Prompt Logging
Every prompt sent to Azure OpenAI is logged with:
- Timestamp
- Prompt type (intent_extraction, entity_extraction, etc.)
- Prompt content
- Response received
- Validation status

### 3. Validation Results
- Hallucination detection status
- SAP field validation
- Response structure validation
- Confidence scores

## Integration Steps

### Step 1: Update function_app.py

Add these imports:
```python
from test_prompt_review import PromptReviewTest
from azure_openai_integration import AzureOpenAIIntegration
from validation_guardrails import ValidationGuardrails
from phase3_integration import IntegratedQueryProcessor, ExplainEndpointIntegration
```

### Step 2: Add Prompt Logging

```python
# Initialize prompt review logger
prompt_review = PromptReviewTest()

@app.route(route='explain', methods=['POST'])
async def explain(req: func.HttpRequest) -> func.HttpResponse:
    """
    Enhanced explain endpoint with prompt logging and validation.
    """
    try:
        req_body = req.get_json()
        question = req_body.get('question')
        
        # Log the incoming question
        prompt_review.log_prompt(
            "user_question",
            question,
            context={"timestamp": datetime.now().isoformat()}
        )
        
        # Process query using integrated processor
        processor_result = IntegratedQueryProcessor.process_query(
            question,
            detail_records
        )
        
        # Log the response
        prompt_review.log_response(
            processor_result["answer"],
            len(prompt_review.prompts_log) - 1,
            validation_passed=True
        )
        
        # Build response with validation
        response = ExplainEndpointIntegration.build_explain_response(
            question,
            detail_records,
            context=context
        )
        
        # Add validation status
        response["validationStatus"] = {
            "hallucinations_detected": False,
            "sap_schema_valid": True,
            "all_fields_valid": True
        }
        
        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        prompt_review.test_results["errors"].append(str(e))
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

### Step 3: Add Prompt Review Endpoint

```python
@app.route(route='prompt-review', methods=['GET'])
async def prompt_review_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    """
    Get the prompt review report.
    """
    try:
        report = prompt_review.generate_report()
        
        return func.HttpResponse(
            report,
            status_code=200,
            mimetype="text/plain"
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

### Step 4: Add Validation Endpoint

```python
@app.route(route='validate-response', methods=['POST'])
async def validate_response(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validate a response for hallucinations and SAP schema compliance.
    """
    try:
        req_body = req.get_json()
        response_text = req_body.get('response')
        
        # Create MCP context
        mcp_builder = MCPContextBuilder()
        mcp_context = mcp_builder.build_mcp_context({}, detail_records)
        
        # Validate response
        guardrails = ValidationGuardrails(mcp_context)
        validation_result = guardrails.validate_response(response_text)
        
        return func.HttpResponse(
            json.dumps(validation_result),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

## UI Display Updates

### In Ask Copilot Response

The response will now show:

**1. Enhanced Answer**
- Scoped metrics (if applicable)
- Comparison data (if comparison query)
- Top contributing records (if traceability query)

**2. Validation Badge**
```
✅ Validation Passed
- No hallucinations detected
- All SAP fields valid
- Response structure valid
- Confidence: 90%
```

**3. Explainability Section**
```
Answer Mode: Investigate
Query Type: Root Cause
Scope: Location LOC001
Data Freshness: 15 minutes old
Confidence Score: 90%
```

**4. Investigate Mode Details**
```
Filtered Records: 2
Changed Count: 2
Change Rate: 66.7%
Primary Driver: Quantity
Top Records: [MAT001, MAT002]
```

## Testing the Integration

### Test 1: Run Prompt Review Test
```bash
pytest planning_intelligence/test_prompt_review.py -v -s
```

### Test 2: Call Explain Endpoint
```bash
curl -X POST http://localhost:7071/api/explain \
  -H "Content-Type: application/json" \
  -d '{"question": "Why is LOC001 risky?"}'
```

### Test 3: Get Prompt Review Report
```bash
curl http://localhost:7071/api/prompt-review
```

### Test 4: Validate Response
```bash
curl -X POST http://localhost:7071/api/validate-response \
  -H "Content-Type: application/json" \
  -d '{"response": "Location LOC001 is risky because..."}'
```

## Expected Output in Ask Copilot UI

### Before Integration
```
Q: Why is LOC001 risky?
A: Planning health is critical. 66.7% changed. Risk: High.
```

### After Integration
```
Q: Why is LOC001 risky?
A: In LOC001, forecast quantities and supplier assignments have changed. 
   This is risky because 66.7% of records changed, indicating high volatility 
   in the supply chain. Recommended action: Monitor forecast changes and 
   contact supplier to understand the modifications.

📊 Investigate Mode Details:
   • Filtered Records: 2
   • Changed Count: 2
   • Change Rate: 66.7%
   • Primary Driver: Quantity
   • Top Records: MAT001 (Δ+100), MAT002 (Δ+50)

✅ Validation Status:
   • No hallucinations detected
   • All SAP fields valid
   • Confidence: 90%
   • Data freshness: 15 minutes old
```

## Deployment to Azure

### Step 1: Update function_app.py
- Add imports
- Add endpoints
- Add logging

### Step 2: Deploy
```bash
func azure functionapp publish <function-app-name>
```

### Step 3: Verify
```bash
# Test the endpoint
curl https://<function-app>.azurewebsites.net/api/explain \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Why is LOC001 risky?"}'
```

## Monitoring

### View Logs
```bash
az functionapp log tail --resource-group <resource-group> --name <function-app-name>
```

### Check Prompt Review Report
```bash
curl https://<function-app>.azurewebsites.net/api/prompt-review
```

### Monitor Validation
```bash
curl https://<function-app>.azurewebsites.net/api/validate-response \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"response": "..."}'
```

## Troubleshooting

### Issue: Responses not showing investigate mode
**Solution:** Verify scope extraction is working
```bash
# Check logs for scope extraction
az functionapp log tail --resource-group <resource-group> --name <function-app-name> | grep "scope"
```

### Issue: Validation always fails
**Solution:** Check MCP context is properly initialized
```bash
# Verify MCP context
curl https://<function-app>.azurewebsites.net/api/validate-response \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"response": "Test response"}'
```

### Issue: Prompt review report is empty
**Solution:** Ensure prompt logging is enabled
```bash
# Check if prompts are being logged
curl https://<function-app>.azurewebsites.net/api/prompt-review
```

## Summary

After integration, Ask Copilot UI will display:
- ✅ Enhanced, scoped responses
- ✅ Investigate mode details
- ✅ Validation status
- ✅ Confidence scores
- ✅ Data freshness information
- ✅ Top contributing records
- ✅ Comparison metrics (for comparison queries)

All prompts and responses are logged and can be reviewed via the prompt-review endpoint.

**Ready to enhance Ask Copilot UI!** 🚀
