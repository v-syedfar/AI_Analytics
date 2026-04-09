# Copilot UI Repeated/Generic Responses Bugfix

## Introduction

The Copilot UI is receiving repeated or generic responses instead of properly processed, context-aware answers to natural language questions. This occurs when the frontend sends questions through the `/api/explain` endpoint. The NLP/LLM integration has been fully implemented with proper intent classification, entity extraction, and response generation, but the explain endpoint is not correctly routing questions through the NLP layer, resulting in duplicate responses, ignored queries, and incorrect response types being returned.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user asks a specific entity query like "List suppliers for CYS20_F01C01" THEN the system returns the same generic response twice instead of a specific supplier list for that location

1.2 WHEN a user asks a question that requires entity extraction like "Which materials are affected?" THEN the system ignores the question and returns no processing result

1.3 WHEN a user asks an out-of-scope question like "What is your name?" THEN the system returns a planning summary response instead of a clarification that the question is out of scope

1.4 WHEN a user asks a question requiring analysis like "Is this demand-driven or design-driven?" THEN the system ignores the question and returns no meaningful response

1.5 WHEN a user sends multiple questions in sequence THEN the system may return duplicate responses or fail to maintain conversation context properly

### Expected Behavior (Correct)

2.1 WHEN a user asks a specific entity query like "List suppliers for CYS20_F01C01" THEN the system SHALL extract the location entity, classify the intent as "list", compute location-specific metrics, and return a specific supplier list for that location

2.2 WHEN a user asks a question that requires entity extraction like "Which materials are affected?" THEN the system SHALL extract relevant entities, classify the intent correctly, compute appropriate metrics, and return a specific list of affected materials

2.3 WHEN a user asks an out-of-scope question like "What is your name?" THEN the system SHALL detect the question is out of scope and return a clarification response explaining that the Copilot is designed for planning intelligence questions

2.4 WHEN a user asks a question requiring analysis like "Is this demand-driven or design-driven?" THEN the system SHALL extract entities, classify the intent as "root_cause" or "analysis", compute relevant metrics, and return a meaningful analysis of change drivers

2.5 WHEN a user sends multiple questions in sequence THEN the system SHALL maintain conversation context, avoid duplicate responses, and process each question independently through the NLP layer

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user clicks on a suggested prompt or starter question THEN the system SHALL CONTINUE TO process the question and return a response without changes to the prompt suggestion mechanism

3.2 WHEN the dashboard context is available (location_id, material_group, context data) THEN the system SHALL CONTINUE TO use this context to scope queries appropriately

3.3 WHEN the data snapshot is unavailable THEN the system SHALL CONTINUE TO return an appropriate error message without crashing

3.4 WHEN a user receives a response with follow-up suggestions THEN the system SHALL CONTINUE TO display follow-up suggestions and allow the user to click them to send new questions

3.5 WHEN the API request times out THEN the system SHALL CONTINUE TO preserve the user's question and allow them to retry without losing their input
