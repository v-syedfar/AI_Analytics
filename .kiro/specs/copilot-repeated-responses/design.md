# Route Natural Language Questions Through NLP Layer - Bugfix Design

## Overview

The Copilot UI's `/api/explain` endpoint is not properly routing natural language questions through the NLP layer, causing repeated/generic responses instead of properly processed, context-aware answers. The NLP/LLM integration exists in `nlp_endpoint.py` with proper intent classification, entity extraction, and response generation, but the `explain` endpoint in `function_app.py` bypasses this layer and uses ReasoningEngine directly. This design formalizes the bug condition and outlines the fix to integrate the NLP layer into the explain endpoint.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when a user asks a natural language question through the Copilot UI and the explain endpoint fails to route it through the NLP layer
- **Property (P)**: The desired behavior when the bug condition is met - questions should be processed through the NLP layer with proper intent classification, entity extraction, and response generation
- **Preservation**: Existing behavior for non-buggy inputs (context parameters, error handling, response structure) that must remain unchanged
- **explain endpoint**: The `/api/explain` function in `planning_intelligence/function_app.py` that processes natural language questions from the Copilot UI
- **NLP layer**: The `NLPEndpointHandler.process_question()` method in `planning_intelligence/nlp_endpoint.py` that provides intent classification, entity extraction, and response generation
- **ReasoningEngine**: The current engine used by explain endpoint that processes queries without proper NLP preprocessing
- **intent classification**: The process of determining the type of question (e.g., "list", "root_cause", "comparison", "out_of_scope")
- **entity extraction**: The process of identifying relevant entities in the question (e.g., location IDs like "CYS20_F01C01", material groups, suppliers)
- **scope determination**: The process of identifying what the question is scoped to (e.g., a specific location, material group, or global)

## Bug Details

### Bug Condition

The bug manifests when a user asks a natural language question through the Copilot UI and the `/api/explain` endpoint receives the question. The endpoint currently uses ReasoningEngine directly without first processing the question through the NLP layer (`NLPEndpointHandler.process_question()`). This causes:

1. Questions to be processed without proper intent classification
2. Entity extraction to fail or be incomplete
3. Generic responses to be returned instead of specific ones
4. Duplicate responses when the same question is asked multiple times
5. Out-of-scope questions to receive planning summaries instead of clarification

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type HttpRequest with JSON body containing "question"
  OUTPUT: boolean
  
  RETURN input.method == "POST"
         AND input.body.question is not empty
         AND input.body.question is a natural language question
         AND explain_endpoint_called(input)
         AND NOT nlp_layer_called_first(input)
         AND reasoning_engine_called_directly(input)
END FUNCTION
```

### Examples

**Example 1: Entity-Specific Query**
- User asks: "List suppliers for CYS20_F01C01"
- Current behavior: Returns generic supplier list or duplicate response
- Expected behavior: NLP layer extracts location entity "CYS20_F01C01", classifies intent as "list", computes location-specific metrics, returns specific supplier list for that location

**Example 2: Entity Extraction Query**
- User asks: "Which materials are affected?"
- Current behavior: Question is ignored, no processing result returned
- Expected behavior: NLP layer extracts relevant entities, classifies intent correctly, computes appropriate metrics, returns specific list of affected materials

**Example 3: Out-of-Scope Question**
- User asks: "What is your name?"
- Current behavior: Returns planning summary response
- Expected behavior: NLP layer detects question is out of scope, returns clarification response explaining Copilot is designed for planning intelligence questions

**Example 4: Analysis Question**
- User asks: "Is this demand-driven or design-driven?"
- Current behavior: Question is ignored, no meaningful response
- Expected behavior: NLP layer extracts entities, classifies intent as "root_cause" or "analysis", computes relevant metrics, returns meaningful analysis

**Example 5: Conversation Context**
- User asks: "List suppliers for CYS20_F01C01" then asks "What about CYS20_F01C02?"
- Current behavior: May return duplicate responses or fail to maintain context
- Expected behavior: NLP layer maintains conversation history, processes each question independently, avoids duplicates

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Dashboard context parameters (location_id, material_group, context data) must continue to be used to scope queries appropriately
- Error handling for missing data snapshots must continue to return appropriate error messages without crashing
- Response structure with fields like "question", "answer", "intent", "entities", "timestamp" must remain unchanged
- Follow-up suggestions and recommended actions must continue to be displayed
- API request timeout handling must continue to preserve user's question and allow retry
- Suggested prompts and starter questions must continue to work without changes to the prompt suggestion mechanism

**Scope:**
All inputs that do NOT involve natural language questions (e.g., direct API calls with pre-computed answers, dashboard data requests) should be completely unaffected by this fix. This includes:
- Direct context-based queries that already have answers
- Dashboard refresh operations
- Data snapshot loading
- Error responses for missing data

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Bypassing NLP Layer**: The explain endpoint calls ReasoningEngine directly without first calling `NLPEndpointHandler.process_question()`. This means:
   - Intent classification is not performed before processing
   - Entity extraction is incomplete or incorrect
   - Out-of-scope detection is not applied
   - Conversation history is not maintained

2. **Missing Intent Classification**: Without NLP preprocessing, the endpoint cannot properly classify question types, leading to:
   - Generic responses instead of specific ones
   - Incorrect answer modes (summary vs. detailed)
   - Failure to detect out-of-scope questions

3. **Incomplete Entity Extraction**: The ReasoningEngine's entity extraction may not match the NLP layer's extraction, causing:
   - Entities to be missed or misidentified
   - Scope determination to fail
   - Metrics computation to use wrong scope

4. **No Conversation History Tracking**: Without NLP layer integration, conversation history is not maintained, causing:
   - Duplicate responses when same question is asked
   - Loss of context across turns
   - Inability to detect repeated questions

5. **No Out-of-Scope Detection**: The endpoint doesn't check if questions are out of scope before processing, causing:
   - Non-planning questions to receive planning summaries
   - Confusion about what the Copilot can answer

## Correctness Properties

Property 1: Bug Condition - NLP Layer Integration for Natural Language Questions

_For any_ natural language question received by the explain endpoint where the bug condition holds (isBugCondition returns true), the fixed explain endpoint SHALL route the question through the NLP layer first by calling `NLPEndpointHandler.process_question()`, which SHALL perform intent classification, entity extraction, scope determination, and return a properly processed response with correct intent, entities, and answer.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - Non-NLP Inputs and Error Handling

_For any_ input that is NOT a natural language question (missing question field, empty question, or direct context-based queries), the fixed explain endpoint SHALL produce the same behavior as the original endpoint, preserving error handling, response structure, and context parameter usage.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the fix involves integrating the NLP layer into the explain endpoint:

**File**: `planning_intelligence/function_app.py`

**Function**: `explain(req: func.HttpRequest) -> func.HttpResponse`

**Specific Changes**:

1. **Add NLP Layer Call**: After validating the question and loading detail records, call `NLPEndpointHandler.process_question()` before using ReasoningEngine
   - Import NLPEndpointHandler from nlp_endpoint.py
   - Call `nlp_handler.process_question(question, detail_records, conversation_history)`
   - Extract queryType, scopeType, scopeValue, confidence from NLP response

2. **Handle Out-of-Scope Detection**: Check if NLP layer detected an out-of-scope question
   - If queryType == "out_of_scope", return the NLP response directly
   - If queryType == "clarification_needed", return clarification response from NLP layer

3. **Use NLP Results for ReasoningEngine**: Pass NLP classification results to ReasoningEngine
   - Use NLP's queryType to determine answer mode
   - Use NLP's scopeType and scopeValue for scoped metrics computation
   - Use NLP's confidence score in response

4. **Maintain Conversation History**: Track conversation history to detect duplicates
   - Store previous questions and answers
   - Check if current question is duplicate of recent question
   - If duplicate, return cached response instead of reprocessing

5. **Update Response Structure**: Include NLP metadata in response
   - Add "nlpProcessed": true to indicate NLP layer was used
   - Include NLP's queryType, scopeType, scopeValue in response
   - Include confidence score from NLP layer
   - Include conversation history if available

6. **Preserve Backward Compatibility**: Ensure existing context parameters still work
   - Continue to accept location_id, material_group, context parameters
   - Continue to use context data if provided
   - Continue to return same response structure

### Implementation Pseudocode

```
FUNCTION explain(req: HttpRequest) -> HttpResponse
  // Validate input
  body := req.get_json()
  question := body.get("question", "").strip()
  IF question is empty THEN
    RETURN error("question is required", 400)
  END IF
  
  // Load detail records
  detail_records := load_detail_records(body)
  IF detail_records is empty THEN
    RETURN error("No detail records available", 404)
  END IF
  
  // NEW: Call NLP layer first
  nlp_handler := NLPEndpointHandler()
  nlp_response := nlp_handler.process_question(
    question,
    detail_records,
    conversation_history
  )
  
  // NEW: Handle out-of-scope questions
  IF nlp_response.queryType == "out_of_scope" THEN
    RETURN build_response(nlp_response)
  END IF
  
  // NEW: Handle clarification needed
  IF nlp_response.queryType == "clarification_needed" THEN
    RETURN build_response(nlp_response)
  END IF
  
  // NEW: Check for duplicate questions
  IF is_duplicate_question(question, conversation_history) THEN
    RETURN get_cached_response(question)
  END IF
  
  // Use NLP results to guide ReasoningEngine
  query_type := nlp_response.queryType
  scope_type := nlp_response.scopeType
  scope_value := nlp_response.scopeValue
  confidence := nlp_response.confidence
  
  // Process through ReasoningEngine with NLP guidance
  engine := ReasoningEngine()
  answer := engine.process_query(question, detail_records)
  
  // Build response with NLP metadata
  response := {
    "question": question,
    "answer": answer,
    "intent": query_type,
    "entities": extract_entities(question),
    "nlpProcessed": true,
    "scopeType": scope_type,
    "scopeValue": scope_value,
    "confidence": confidence,
    "timestamp": get_last_updated_time()
  }
  
  // Add context if available
  IF body.context exists THEN
    response.contextUsed := [keys from context]
    response.aiInsight := body.context.aiInsight
    response.rootCause := body.context.rootCause
  END IF
  
  RETURN response
END FUNCTION
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate natural language questions through the explain endpoint and assert that:
1. The NLP layer is called for processing
2. Intent classification is performed correctly
3. Entity extraction identifies the correct entities
4. Out-of-scope questions are detected
5. Conversation history is maintained

Run these tests on the UNFIXED code to observe failures and understand the root cause.

**Test Cases**:

1. **Entity-Specific Query Test**: Simulate POST to /api/explain with question "List suppliers for CYS20_F01C01"
   - Assert that NLP layer is called (will fail on unfixed code)
   - Assert that location entity "CYS20_F01C01" is extracted
   - Assert that response contains specific supplier list for that location

2. **Entity Extraction Query Test**: Simulate POST to /api/explain with question "Which materials are affected?"
   - Assert that NLP layer processes the question
   - Assert that relevant entities are extracted
   - Assert that response contains specific list of affected materials

3. **Out-of-Scope Question Test**: Simulate POST to /api/explain with question "What is your name?"
   - Assert that out-of-scope detection is triggered
   - Assert that response is clarification message, not planning summary

4. **Analysis Question Test**: Simulate POST to /api/explain with question "Is this demand-driven or design-driven?"
   - Assert that intent is classified as "root_cause" or "analysis"
   - Assert that response contains meaningful analysis

5. **Duplicate Question Test**: Simulate two consecutive requests with same question
   - Assert that conversation history is maintained
   - Assert that duplicate is detected
   - Assert that cached response is returned for duplicate

**Expected Counterexamples**:
- NLP layer is not called, ReasoningEngine is used directly
- Intent classification is not performed, generic responses are returned
- Entity extraction fails or is incomplete
- Out-of-scope questions receive planning summaries instead of clarification
- Duplicate questions are not detected, responses are repeated

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed explain endpoint produces the expected behavior.

**Pseudocode:**
```
FOR ALL question WHERE isBugCondition(question) DO
  response := explain_fixed(question)
  ASSERT response.nlpProcessed == true
  ASSERT response.intent is correctly classified
  ASSERT response.entities are correctly extracted
  ASSERT response.answer is specific and relevant
  ASSERT response.confidence > 0.8
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed explain endpoint produces the same result as the original endpoint.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT explain_original(input) = explain_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for error cases and context-based queries, then write property-based tests capturing that behavior.

**Test Cases**:

1. **Error Handling Preservation**: Verify that missing question field returns 400 error on both original and fixed code
2. **Missing Data Preservation**: Verify that missing detail records returns 404 error on both original and fixed code
3. **Context Parameter Preservation**: Verify that location_id and material_group parameters are used correctly on both versions
4. **Response Structure Preservation**: Verify that response contains same fields (question, answer, intent, entities, timestamp) on both versions
5. **Timeout Handling Preservation**: Verify that API timeouts are handled the same way on both versions

### Unit Tests

- Test NLP layer integration: verify `NLPEndpointHandler.process_question()` is called
- Test intent classification: verify different question types are classified correctly
- Test entity extraction: verify entities are extracted from questions
- Test out-of-scope detection: verify non-planning questions are detected
- Test conversation history: verify duplicate questions are detected
- Test error handling: verify missing data and invalid input are handled correctly

### Property-Based Tests

- Generate random natural language questions and verify NLP layer processes them correctly
- Generate random entity combinations and verify scope determination works correctly
- Generate random conversation histories and verify duplicate detection works
- Generate random error conditions and verify preservation of error handling
- Test that all non-buggy inputs continue to work across many scenarios

### Integration Tests

- Test full flow: user asks question → NLP layer processes → ReasoningEngine generates answer → response returned
- Test conversation flow: user asks multiple questions → conversation history maintained → duplicates detected
- Test context switching: user switches between locations → context updated → new questions processed correctly
- Test error recovery: API fails → user retries → question preserved and reprocessed
