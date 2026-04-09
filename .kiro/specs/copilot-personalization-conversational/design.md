# Copilot Personalization & Conversational AI - Design Document

## Overview

The Copilot Personalization & Conversational AI feature adds a conversational layer on top of the existing real-time answers backend. This layer provides:

1. **Personalization** - Context-aware greetings and user-specific responses
2. **Intent Classification** - Understanding what users are asking for
3. **Conversation State Management** - Tracking multi-turn conversations
4. **Response Filtering** - Focusing answers on the current question
5. **Follow-Up Suggestions** - Guiding users toward deeper analysis

The design maintains 100% backward compatibility with existing clients while adding optional personalization fields to responses.

## Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Application                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Conversational Layer (NEW)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Personalization Manager                            │   │
│  │ • Intent Classifier                                  │   │
│  │ • Conversation State Manager                         │   │
│  │ • Response Formatter                                 │   │
│  │ • Follow-Up Suggestion Manager                       │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Real-Time Answers Backend (EXISTING)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • explain() endpoint                                 │   │
│  │ • Analytics engine                                   │   │
│  │ • Dashboard context                                  │   │
│  │ • Blob storage integration                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Diagram

```
User Question
     │
     ▼
┌─────────────────────────────────────────┐
│  Intent Classifier                      │
│  • Classify question type               │
│  • Extract scope entities               │
│  • Compute confidence                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Conversation State Manager             │
│  • Load conversation history            │
│  • Resolve pronouns/references          │
│  • Update conversation context          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Real-Time Answers Backend              │
│  • Call explain() endpoint              │
│  • Get scoped metrics                   │
│  • Get follow-up context                │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Response Formatter                     │
│  • Filter to current question           │
│  • Add personalization                  │
│  • Format for readability               │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Follow-Up Suggestion Manager           │
│  • Generate contextual suggestions      │
│  • Rank by relevance                    │
│  • Avoid repetition                     │
└────────────┬────────────────────────────┘
             │
             ▼
Personalized Response with Follow-Ups
```

## Components and Interfaces

### 1. Intent Classifier

**Purpose**: Understand what the user is asking for and extract relevant scope.

**Key Functions**:

```python
def classify_intent(question: str) -> IntentClassification:
    """
    Classify question intent and extract scope.
    
    Returns:
        IntentClassification with:
        - intent_type: "summary" | "comparison" | "root_cause" | "why_not" | "traceability"
        - scope_type: "location" | "supplier" | "material_group" | "material_id" | "risk_type" | None
        - scope_values: List of extracted entities (e.g., ["LOC001", "LOC002"])
        - confidence: 0.0-1.0 confidence score
        - reasoning: Explanation of classification
    """
    pass

def extract_entities(question: str) -> List[str]:
    """Extract location, supplier, material IDs from question."""
    pass

def classify_question_type(question: str) -> str:
    """Classify as comparison, root_cause, why_not, traceability, or summary."""
    pass
```

**Implementation Notes**:
- Use regex patterns for entity extraction (LOC\d+, SUP\d+, MAT\d+)
- Use keyword matching for intent classification
- Confidence based on pattern match strength and question clarity
- Deterministic (no LLM calls)

### 2. Conversation State Manager

**Purpose**: Track conversation history and resolve references across turns.

**Key Functions**:

```python
def load_conversation(conversation_id: str) -> ConversationState:
    """Load conversation history from storage or request."""
    pass

def resolve_references(question: str, conversation: ConversationState) -> str:
    """
    Resolve pronouns and references to previous context.
    
    Examples:
    - "Tell me more" → "Tell me more about [previous_entity]"
    - "Compare this to LOC002" → "Compare [previous_entity] to LOC002"
    """
    pass

def update_conversation(
    conversation_id: str,
    question: str,
    answer: str,
    intent: IntentClassification,
    context: dict
) -> ConversationState:
    """Add new turn to conversation history."""
    pass

def get_conversation_summary(conversation: ConversationState) -> str:
    """Generate summary of conversation so far."""
    pass
```

**Data Structure**:

```python
class ConversationState:
    conversation_id: str
    user_id: str
    turns: List[ConversationTurn]
    current_focus: Dict[str, str]  # {"location": "LOC001", "material_group": "Electronics"}
    last_answer: str
    last_entities: List[str]
    created_at: datetime
    updated_at: datetime
    
class ConversationTurn:
    turn_number: int
    question: str
    answer: str
    intent: IntentClassification
    entities: List[str]
    timestamp: datetime
```

**Implementation Notes**:
- Store conversation in request (stateless) or optional server-side storage
- Maintain last 5-10 turns for context
- Resolve pronouns using previous entities
- Track "current focus" for implicit references

### 3. Personalization Manager

**Purpose**: Generate context-aware greetings and personalized responses.

**Key Functions**:

```python
def generate_greeting(
    user_context: dict,
    dashboard_context: dict,
    conversation: ConversationState
) -> str:
    """
    Generate personalized greeting.
    
    Args:
        user_context: {"role": "planner", "name": "John", "location_focus": "LOC001"}
        dashboard_context: {"planning_health": 45, "changed_record_count": 12, ...}
        conversation: ConversationState (None for first message)
    
    Returns:
        Personalized greeting string
    """
    pass

def personalize_response(
    answer: str,
    user_context: dict,
    intent: IntentClassification
) -> str:
    """Add personalization touches to answer."""
    pass
```

**Greeting Templates**:

```
# First message - Critical health
"Hi [name], I see you're focused on [location]. Planning health is critical (45/100) 
with 12 records changed. Let's dig into what's happening."

# First message - Healthy
"Hi [name], planning health looks good (85/100). 2 records changed this cycle. 
What would you like to explore?"

# Follow-up - Continuing conversation
"Continuing our analysis of [location]..."

# Follow-up - New topic
"Switching focus to [new_location]..."
```

**Implementation Notes**:
- Extract user context from request headers or session
- Use dashboard health score to vary greeting tone
- Include 1-2 key metrics in greeting
- Keep greeting concise (1-2 sentences)

### 4. Response Formatter

**Purpose**: Filter responses to focus on current question and format for readability.

**Key Functions**:

```python
def filter_response(
    full_response: dict,
    intent: IntentClassification,
    question: str
) -> dict:
    """
    Filter response to address only current question.
    
    Removes:
    - Unrelated metrics
    - Tangential information
    - Suggestions outside scope
    
    Keeps:
    - Answer to current question
    - Supporting metrics for that answer
    - Relevant context
    """
    pass

def format_answer(
    answer: str,
    intent: IntentClassification,
    scope: List[str]
) -> str:
    """Format answer for readability and clarity."""
    pass
```

**Response Structure**:

```python
{
    # Personalization
    "personalization": {
        "greeting": "Hi John, I see you're focused on LOC001...",
        "user_context": {"role": "planner", "location_focus": "LOC001"},
        "conversation_id": "conv_123",
        "turn_number": 1
    },
    
    # Core answer
    "question": "Why is LOC001 risky?",
    "answer": "In LOC001, quantity changed significantly...",
    "intent": {
        "type": "root_cause",
        "scope_type": "location",
        "scope_values": ["LOC001"],
        "confidence": 0.95
    },
    
    # Supporting context
    "supporting_metrics": {
        "changed_record_count": 5,
        "change_rate": 25.0,
        "primary_driver": "quantity"
    },
    
    # Follow-ups
    "follow_up_questions": [
        "Which materials are most impacted in LOC001?",
        "How does LOC001 compare to LOC002?",
        "What's the recommended action?"
    ],
    
    # Conversation context
    "conversation_context": {
        "previous_questions": ["What's the planning health?"],
        "current_focus": {"location": "LOC001"},
        "conversation_summary": "Analyzing LOC001 risk factors"
    },
    
    # Backward compatibility
    "dataMode": "blob",
    "lastRefreshedAt": "2024-01-15T10:30:00Z",
    ...existing fields...
}
```

### 5. Follow-Up Suggestion Manager

**Purpose**: Generate contextual follow-up questions that guide deeper analysis.

**Key Functions**:

```python
def generate_follow_ups(
    answer: str,
    intent: IntentClassification,
    entities: List[str],
    conversation: ConversationState
) -> List[str]:
    """
    Generate 2-3 contextual follow-up questions.
    
    Strategy:
    - After root_cause: suggest drill-down (materials, suppliers)
    - After comparison: suggest related comparisons
    - After summary: suggest investigation
    - After traceability: suggest root cause analysis
    """
    pass

def rank_suggestions(
    suggestions: List[str],
    conversation: ConversationState
) -> List[str]:
    """Rank suggestions by relevance and avoid repetition."""
    pass
```

**Follow-Up Patterns**:

```
# After root_cause answer about LOC001
- "Which materials are most impacted in LOC001?"
- "How does LOC001 compare to other locations?"
- "What's the recommended action for LOC001?"

# After comparison answer (LOC001 vs LOC002)
- "Why is LOC001 riskier than LOC002?"
- "Which suppliers are causing LOC001's issues?"
- "Show me the top records in LOC001"

# After summary answer
- "Tell me more about the high-risk records"
- "Which location needs the most attention?"
- "What's driving the design changes?"

# After traceability answer
- "Why did these records change?"
- "What's the risk level for these materials?"
- "Which supplier is responsible?"
```

## Data Models

### IntentClassification

```python
class IntentClassification:
    intent_type: str  # "summary" | "comparison" | "root_cause" | "why_not" | "traceability"
    scope_type: Optional[str]  # "location" | "supplier" | "material_group" | "material_id" | "risk_type"
    scope_values: List[str]  # ["LOC001", "LOC002"]
    confidence: float  # 0.0-1.0
    reasoning: str  # Explanation of classification
    keywords_matched: List[str]  # Keywords that triggered classification
```

### ConversationState

```python
class ConversationState:
    conversation_id: str
    user_id: str
    session_id: str
    turns: List[ConversationTurn]
    current_focus: Dict[str, str]
    last_answer: str
    last_entities: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

class ConversationTurn:
    turn_number: int
    question: str
    answer: str
    intent: IntentClassification
    entities: List[str]
    timestamp: datetime
    context_used: List[str]
```

### PersonalizationContext

```python
class PersonalizationContext:
    user_id: str
    user_role: str
    user_name: str
    location_focus: Optional[str]
    material_group_focus: Optional[str]
    preferences: Dict[str, Any]
    last_activity: datetime
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Intent Classification Accuracy

*For any* question and scope combination, the intent classifier should correctly identify the question type and extract all mentioned entities with confidence score reflecting classification clarity.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Personalized Greeting Includes Context

*For any* user context and dashboard state, the greeting should include user role/name, location focus, and at least one relevant metric (health score, change count, or risk level).

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 3: Response Focuses on Current Question

*For any* question and answer, the response should only include information relevant to that specific question and should not include metrics or suggestions unrelated to the question scope.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 4: Follow-Up Suggestions Are Contextual

*For any* answer and intent type, the generated follow-up questions should be contextual to the current answer and should guide toward deeper analysis (drill-down, comparison, or root cause).

**Validates: Requirements 4.1, 4.2, 4.3**

### Property 5: Conversation Context Persistence

*For any* multi-turn conversation, the system should maintain context across all turns and correctly resolve pronouns and references to previous entities.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 6: Backward Compatibility

*For any* existing client request, the response should include all existing fields unchanged and new personalization fields should be optional and not break existing clients.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

### Property 7: Performance Within Bounds

*For any* request, the personalization layer should add less than 50ms latency, intent classification should complete in less than 30ms, and follow-up generation should complete in less than 50ms, with total response time under 500ms.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 8: Deterministic Response Generation

*For any* identical question and context, the system should generate the same answer, intent classification, and follow-up suggestions (no randomness or variation).

**Validates: Requirements AC7**

### Property 9: Conversation Summary Completeness

*For any* multi-turn conversation, the conversation summary should include key points from all turns and accurately represent the conversation focus and entities discussed.

**Validates: Requirements 5.4**

### Property 10: Scope Entity Extraction Round-Trip

*For any* question containing scope entities, extracting entities and then formatting them back into a question should preserve the original entities and their relationships.

**Validates: Requirements 2.1, 2.2**

## Error Handling

### Intent Classification Errors

```python
# Ambiguous question
if confidence < 0.5:
    return {
        "intent": "summary",  # Default to summary
        "confidence": confidence,
        "warning": "Question is ambiguous. Treating as general summary.",
        "suggestions": ["Try asking 'Why is LOC001 risky?' for specific analysis"]
    }

# No entities found
if not scope_values:
    return {
        "intent": intent_type,
        "scope_type": None,
        "scope_values": [],
        "confidence": confidence,
        "note": "No specific entities mentioned. Analyzing globally."
    }
```

### Conversation State Errors

```python
# Conversation not found
if not conversation:
    return {
        "conversation_id": generate_new_id(),
        "turns": [],
        "note": "Starting new conversation"
    }

# Reference resolution failed
if cannot_resolve_reference:
    return {
        "resolved_question": original_question,
        "warning": "Could not resolve reference. Using original question.",
        "suggestion": "Please rephrase with specific entity names"
    }
```

### Response Filtering Errors

```python
# No relevant information for scope
if filtered_response_empty:
    return {
        "answer": "No data available for the specified scope.",
        "suggestion": "Try asking about a different location or time period",
        "fallback": "Here's the global summary instead..."
    }
```

## Testing Strategy

### Unit Testing

**Intent Classification Tests**:
- Test entity extraction (LOC\d+, SUP\d+, MAT\d+)
- Test intent classification for each type
- Test confidence score computation
- Test edge cases (ambiguous questions, no entities)

**Conversation State Tests**:
- Test conversation creation and loading
- Test turn addition and history maintenance
- Test reference resolution (pronouns, implicit references)
- Test conversation summary generation

**Personalization Tests**:
- Test greeting generation with different contexts
- Test greeting variation based on health status
- Test metric inclusion in greeting
- Test personalization of responses

**Response Filtering Tests**:
- Test that unrelated metrics are removed
- Test that scope is maintained
- Test that answer length is proportional to specificity
- Test that scope is explicitly stated

**Follow-Up Generation Tests**:
- Test contextual suggestion generation
- Test suggestion ranking
- Test repetition avoidance
- Test suggestion relevance

### Property-Based Testing

**Property 1: Intent Classification**
- Generate random questions with various intents
- Verify correct intent classification
- Verify entity extraction
- Verify confidence scores in valid range

**Property 2: Personalization**
- Generate random user contexts and dashboard states
- Verify greeting includes required fields
- Verify greeting varies with health status
- Verify metrics are included

**Property 3: Response Filtering**
- Generate random answers and scopes
- Verify response only includes relevant information
- Verify unrelated metrics are removed
- Verify scope is stated

**Property 4: Follow-Up Suggestions**
- Generate random answers and intents
- Verify suggestions are contextual
- Verify suggestions guide deeper analysis
- Verify no repetition

**Property 5: Conversation Context**
- Generate multi-turn conversations
- Verify context maintained across turns
- Verify references resolved correctly
- Verify conversation summary accurate

**Property 6: Backward Compatibility**
- Generate requests with and without personalization
- Verify existing fields unchanged
- Verify new fields optional
- Verify fallback mode works

**Property 7: Performance**
- Measure personalization latency
- Measure intent classification latency
- Measure follow-up generation latency
- Verify total response < 500ms

**Property 8: Determinism**
- Generate identical requests multiple times
- Verify identical responses
- Verify no randomness

### Integration Testing

- Test full conversation flow (greeting → question → answer → follow-ups)
- Test conversation persistence across multiple turns
- Test integration with real-time answers backend
- Test performance with realistic data volumes
- Test backward compatibility with existing clients

## Integration Points

### 1. Explain Endpoint Integration

**Current Flow**:
```
Client → explain() → Backend → Response
```

**New Flow**:
```
Client → Conversational Layer → explain() → Backend → Response Formatter → Client
```

**Implementation**:
```python
@app.route(route="explain-conversational", methods=["POST"])
def explain_conversational(req: func.HttpRequest) -> func.HttpResponse:
    """
    Conversational wrapper around explain() endpoint.
    """
    body = req.get_json()
    
    # Extract personalization context
    user_context = extract_user_context(req)
    conversation_id = body.get("conversation_id")
    
    # Load conversation state
    conversation = load_conversation(conversation_id)
    
    # Classify intent
    question = body.get("question")
    intent = classify_intent(question)
    
    # Resolve references
    resolved_question = resolve_references(question, conversation)
    
    # Call existing explain() endpoint
    backend_response = call_explain_endpoint(resolved_question, body)
    
    # Format response
    formatted_response = format_response(
        backend_response,
        intent,
        user_context,
        conversation
    )
    
    # Generate follow-ups
    follow_ups = generate_follow_ups(
        formatted_response["answer"],
        intent,
        intent.scope_values,
        conversation
    )
    formatted_response["follow_up_questions"] = follow_ups
    
    # Update conversation
    update_conversation(conversation_id, question, formatted_response, intent)
    
    return func.HttpResponse(
        json.dumps(formatted_response, default=str),
        mimetype="application/json",
        status_code=200,
    )
```

### 2. Backward Compatibility

**Existing Clients**:
- Continue using existing `explain()` endpoint
- No changes required
- No new fields in response

**New Clients**:
- Use new `explain-conversational()` endpoint
- Get personalization fields
- Get follow-up suggestions
- Get conversation context

**Optional Personalization**:
```python
# Request parameter to disable personalization
{
    "question": "Why is LOC001 risky?",
    "personalization_enabled": false  # Optional, defaults to true
}

# Response includes personalization only if enabled
{
    "answer": "...",
    "personalization": {...},  # Only if enabled
    "follow_up_questions": [...]  # Only if enabled
}
```

### 3. Data Flow for Typical Conversation Turn

```
1. Client sends question with conversation_id
   {
       "question": "Why is LOC001 risky?",
       "conversation_id": "conv_123",
       "context": {...}
   }

2. Conversational Layer:
   - Load conversation history
   - Classify intent → root_cause, LOC001
   - Resolve references (if any)
   - Call explain() with resolved question

3. Backend returns:
   {
       "answer": "In LOC001, quantity changed...",
       "supporting_metrics": {...},
       ...
   }

4. Response Formatter:
   - Filter to LOC001-specific information
   - Add personalization greeting (if first turn)
   - Format answer for readability

5. Follow-Up Generator:
   - Generate drill-down suggestions
   - Rank by relevance
   - Return top 3

6. Return to client:
   {
       "personalization": {...},
       "question": "Why is LOC001 risky?",
       "answer": "In LOC001, quantity changed...",
       "intent": {...},
       "follow_up_questions": [...],
       "conversation_context": {...}
   }
```

## Implementation Roadmap

### Phase 1: Core Components (Week 1)
- Intent Classifier
- Conversation State Manager
- Basic Personalization Manager

### Phase 2: Response Formatting (Week 2)
- Response Formatter
- Follow-Up Suggestion Manager
- Integration with explain() endpoint

### Phase 3: Testing & Optimization (Week 3)
- Unit tests for all components
- Property-based tests
- Performance optimization
- Integration testing

### Phase 4: Deployment (Week 4)
- Backward compatibility verification
- Gradual rollout
- Monitoring and metrics
- User feedback collection

## Performance Considerations

### Latency Budget (500ms total)

- Intent Classification: 30ms
- Conversation State: 20ms
- Backend explain(): 350ms
- Response Formatting: 30ms
- Follow-Up Generation: 50ms
- Overhead: 20ms

### Optimization Strategies

1. **Caching**:
   - Cache intent classifications for common questions
   - Cache conversation summaries
   - Cache follow-up suggestions

2. **Async Processing**:
   - Generate follow-ups asynchronously if needed
   - Return answer immediately, follow-ups in background

3. **Lazy Loading**:
   - Load conversation history on demand
   - Don't load full history for every request

4. **Efficient Data Structures**:
   - Use efficient regex for entity extraction
   - Use trie for keyword matching
   - Use hash maps for conversation lookup

## Monitoring & Metrics

### Key Metrics

1. **Intent Classification Accuracy**: % of correctly classified questions
2. **Conversation Completion Rate**: % of conversations with 3+ turns
3. **Follow-Up Click Rate**: % of users clicking suggested follow-ups
4. **Response Time**: P50, P95, P99 latency
5. **Error Rate**: % of failed requests
6. **User Satisfaction**: NPS or CSAT score

### Logging

```python
# Log intent classification
logging.info(f"Intent: {intent.intent_type}, Confidence: {intent.confidence}")

# Log conversation turns
logging.info(f"Conversation {conv_id}: Turn {turn_num}, Intent: {intent.intent_type}")

# Log performance
logging.info(f"Response time: {elapsed_ms}ms (intent: {intent_ms}ms, backend: {backend_ms}ms)")

# Log errors
logging.error(f"Intent classification failed: {error}")
```

## Future Enhancements

1. **LLM-Based Personalization** (Optional)
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
