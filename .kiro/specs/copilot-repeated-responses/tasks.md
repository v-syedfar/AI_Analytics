# Implementation Plan

## Phase 1: Exploration - Surface the Bug

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - NLP Layer Integration for Natural Language Questions
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: For deterministic bugs, scope the property to concrete failing cases to ensure reproducibility
  
  **Test Implementation Details from Bug Condition in design:**
  - Test that natural language questions are routed through NLP layer
  - Verify NLPEndpointHandler.process_question() is called before ReasoningEngine
  - Test cases:
    1. Entity-Specific Query: "List suppliers for CYS20_F01C01" → NLP extracts location entity, classifies intent as "list", returns specific supplier list
    2. Entity Extraction Query: "Which materials are affected?" → NLP extracts entities, returns specific list of affected materials
    3. Out-of-Scope Question: "What is your name?" → NLP detects out-of-scope, returns clarification response
    4. Analysis Question: "Is this demand-driven or design-driven?" → NLP classifies as "root_cause", returns meaningful analysis
    5. Duplicate Question: Same question asked twice → NLP maintains conversation history, detects duplicate, returns cached response
  
  - The test assertions should match the Expected Behavior Properties from design:
    - response.nlpProcessed == true
    - response.intent is correctly classified
    - response.entities are correctly extracted
    - response.answer is specific and relevant
    - response.confidence > 0.8
  
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause:
    - NLP layer is not called, ReasoningEngine is used directly
    - Intent classification is not performed, generic responses are returned
    - Entity extraction fails or is incomplete
    - Out-of-scope questions receive planning summaries instead of clarification
    - Duplicate questions are not detected, responses are repeated
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

## Phase 2: Preservation - Verify Non-Buggy Behavior

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-NLP Inputs and Error Handling
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (inputs where isBugCondition returns false)
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Property-based testing generates many test cases for stronger guarantees
  
  **Test Implementation Details from Preservation Requirements in design:**
  - Test cases for non-buggy inputs:
    1. Error Handling: Missing question field → returns 400 error
    2. Missing Data: No detail records available → returns 404 error
    3. Context Parameters: location_id and material_group parameters are used correctly
    4. Response Structure: Response contains fields (question, answer, intent, entities, timestamp)
    5. Timeout Handling: API timeouts are handled gracefully
  
  - Observe and record actual outputs on UNFIXED code:
    - Missing question field returns 400 error with message "question is required"
    - Missing detail records returns 404 error with message "No detail records available"
    - Context parameters are preserved in response
    - Response structure remains consistent
    - Timeout errors are caught and returned appropriately
  
  - Write property-based tests that assert those observed outputs across the input domain:
    - For all requests with missing question field, response status is 400
    - For all requests with missing detail records, response status is 404
    - For all requests with context parameters, those parameters are used in scoping
    - For all requests, response contains required fields
    - For all timeout scenarios, error is handled gracefully
  
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

## Phase 3: Implementation - Apply the Fix

- [x] 3. Fix for NLP Layer Integration in explain endpoint

  - [x] 3.1 Implement the fix
    - Import NLPEndpointHandler from nlp_endpoint.py
    - Add NLP layer call after validating question and loading detail records
    - Call `nlp_handler.process_question(question, detail_records, conversation_history)` before ReasoningEngine
    - Extract queryType, scopeType, scopeValue, confidence from NLP response
    - Handle out-of-scope detection: if queryType == "out_of_scope", return NLP response directly
    - Handle clarification needed: if queryType == "clarification_needed", return clarification response
    - Check for duplicate questions using conversation history
    - Pass NLP classification results to ReasoningEngine (queryType, scopeType, scopeValue)
    - Maintain conversation history to detect duplicates
    - Update response structure to include NLP metadata (nlpProcessed, queryType, scopeType, scopeValue, confidence)
    - Preserve backward compatibility with existing context parameters
    - _Bug_Condition: isBugCondition(input) where input is natural language question not routed through NLP layer_
    - _Expected_Behavior: explain endpoint routes question through NLP layer, performs intent classification, entity extraction, scope determination, returns properly processed response_
    - _Preservation: Error handling, response structure, context parameter usage remain unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - NLP Layer Integration for Natural Language Questions
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - Verify all test cases pass:
      - Entity-Specific Query returns specific supplier list
      - Entity Extraction Query returns specific list of affected materials
      - Out-of-Scope Question returns clarification response
      - Analysis Question returns meaningful analysis
      - Duplicate Question detection works correctly
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-NLP Inputs and Error Handling
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - Verify all test cases still pass:
      - Error handling for missing question field
      - Error handling for missing detail records
      - Context parameters are used correctly
      - Response structure is preserved
      - Timeout handling is preserved
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

## Phase 4: Checkpoint

- [x] 4. Checkpoint - Ensure all tests pass
  - Verify all 25 existing tests still pass (no breaking changes)
  - Verify bug condition exploration test passes (bug is fixed)
  - Verify preservation tests pass (no regressions)
  - Verify new integration tests pass
  - Ensure no duplicate responses are returned
  - Ensure out-of-scope questions are handled correctly
  - Ensure conversation history is maintained
  - Ensure all success criteria are met:
    - "List suppliers for CYS20_F01C01" returns specific supplier list
    - "Which materials are affected?" returns list of affected materials
    - "What is your name?" returns out-of-scope clarification
    - "Is this demand-driven or design-driven?" returns analysis
    - No duplicate responses
    - All existing tests still pass (25/25)
    - New integration tests pass
    - No breaking changes to existing API
  - Ask the user if questions arise
