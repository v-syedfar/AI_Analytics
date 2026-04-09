"""
NLP/LLM Integration Endpoint for Copilot UI

This module provides the natural language processing endpoint that integrates
with the Copilot UI. It processes natural language questions and routes them
through the NLP pipeline to generate appropriate responses.

Features:
- Natural language question processing
- Intent classification (with Azure OpenAI)
- Entity extraction (with Azure OpenAI)
- Multi-turn conversation support
- Out-of-scope question handling
- Hallucination prevention with validation
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import azure.functions as func

# Import NLP pipeline components
from phase1_core_functions import (
    QuestionClassifier,
    ScopeExtractor,
    AnswerModeDecider,
    ScopedMetricsComputer
)
from phase2_answer_templates import AnswerTemplateRouter
from phase3_integration import IntegratedQueryProcessor

# Import Azure OpenAI integration
try:
    from azure_openai_integration import AzureOpenAIIntegration
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False
    logging.warning("Azure OpenAI integration not available, using rule-based NLP")


class NLPEndpointHandler:
    """Handles natural language queries from Copilot UI."""
    
    # Out-of-scope keywords
    OUT_OF_SCOPE_KEYWORDS = [
        "what is your name", "who are you", "what are you",
        "tell me about yourself", "hello", "hi",
        "how are you", "what time is it", "what's the weather",
        "joke", "funny", "music", "movie", "sports"
    ]
    
    # Planning-related keywords
    PLANNING_KEYWORDS = [
        "planning", "forecast", "demand", "supply", "supplier",
        "location", "material", "change", "risk", "status",
        "quantity", "design", "schedule", "roj", "bod",
        "changed", "risky", "stable", "driver", "trend"
    ]
    
    def __init__(self):
        """Initialize NLP handler with optional Azure OpenAI."""
        self.use_azure_openai = AZURE_OPENAI_AVAILABLE
        if self.use_azure_openai:
            try:
                self.openai_client = AzureOpenAIIntegration()
                logging.info("Azure OpenAI integration initialized")
            except Exception as e:
                logging.warning(f"Failed to initialize Azure OpenAI: {e}, falling back to rule-based NLP")
                self.use_azure_openai = False
        else:
            self.openai_client = None
    
    @staticmethod
    def is_planning_question(question: str) -> bool:
        """Check if question is about planning."""
        q_lower = question.lower()
        
        # Check for planning keywords
        if any(keyword in q_lower for keyword in NLPEndpointHandler.PLANNING_KEYWORDS):
            return True
        
        # Check for entity patterns (location codes, supplier codes, etc.)
        if any(pattern in q_lower for pattern in ["loc", "sup", "mat", "cys", "avc", "clt"]):
            return True
        
        # Check for traceability keywords
        if any(word in q_lower for word in ["show", "top", "contributing", "records", "list", "which"]):
            return True
        
        # Check for change-related questions
        if any(word in q_lower for word in ["changed", "change", "most", "affected", "impact"]):
            return True
        
        return False
    
    @staticmethod
    def is_out_of_scope(question: str) -> bool:
        """Check if question is out of scope."""
        q_lower = question.lower()
        return any(keyword in q_lower for keyword in NLPEndpointHandler.OUT_OF_SCOPE_KEYWORDS)
    
    def process_question(
        self,
        question: str,
        detail_records: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language question and return structured response.
        
        Uses Azure OpenAI for intent classification and entity extraction if available,
        falls back to rule-based NLP if Azure OpenAI is not available.
        
        Args:
            question: Natural language question from user
            detail_records: List of detail records for analysis
            conversation_history: Previous conversation turns (optional)
        
        Returns:
            {
                "question": str,
                "answer": str,
                "queryType": str,
                "scopeType": Optional[str],
                "scopeValue": Optional[str],
                "answerMode": str,
                "confidence": float,
                "conversationHistory": List[Dict],
                "azureOpenAIUsed": bool
            }
        """
        
        # Initialize response
        response = {
            "question": question,
            "answer": "",
            "queryType": "unknown",
            "scopeType": None,
            "scopeValue": None,
            "answerMode": "summary",
            "confidence": 0.0,
            "conversationHistory": conversation_history or [],
            "azureOpenAIUsed": False
        }
        
        try:
            # Check if question is out of scope
            if self.is_out_of_scope(question):
                response["answer"] = self._generate_out_of_scope_response(question)
                response["queryType"] = "out_of_scope"
                response["confidence"] = 1.0
                return response
            
            # Check if question is about planning
            if not self.is_planning_question(question):
                response["answer"] = self._generate_clarification_response(question)
                response["queryType"] = "clarification_needed"
                response["confidence"] = 0.5
                return response
            
            # Try to use Azure OpenAI for intent classification and entity extraction
            if self.use_azure_openai:
                try:
                    logging.info(f"Using Azure OpenAI for question: {question}")
                    
                    # Use Azure OpenAI for intent classification and entity extraction
                    intent_result = self.openai_client.extract_intent_and_entities(
                        query=question,
                        sap_field_dictionary={}  # Can be enhanced with actual SAP fields
                    )
                    
                    query_type = intent_result.get("intent", "summary")
                    scope_type = None
                    scope_value = None
                    
                    # Extract scope from entities if available
                    entities = intent_result.get("entities", {})
                    if entities:
                        # Try to extract location, supplier, or material
                        if "LOCID" in entities and entities["LOCID"]:
                            scope_type = "location"
                            scope_value = entities["LOCID"][0]
                        elif "LOCFR" in entities and entities["LOCFR"]:
                            scope_type = "supplier"
                            scope_value = entities["LOCFR"][0]
                        elif "PRDID" in entities and entities["PRDID"]:
                            scope_type = "material"
                            scope_value = entities["PRDID"][0]
                    
                    confidence = intent_result.get("confidence", 0.8)
                    response["azureOpenAIUsed"] = True
                    
                    logging.info(f"Azure OpenAI result: intent={query_type}, confidence={confidence}")
                    
                except Exception as e:
                    logging.warning(f"Azure OpenAI failed, falling back to rule-based: {e}")
                    # Fall back to rule-based classification
                    query_type = QuestionClassifier.classify_question(question)
                    scope_type, scope_value = ScopeExtractor.extract_scope(question)
                    confidence = 0.75
            else:
                # Use rule-based classification
                query_type = QuestionClassifier.classify_question(question)
                scope_type, scope_value = ScopeExtractor.extract_scope(question)
                confidence = 0.75
            
            answer_mode = AnswerModeDecider.determine_answer_mode(query_type, scope_type)
            
            # Compute metrics
            if scope_type and scope_value:
                metrics = ScopedMetricsComputer.compute_scoped_metrics(
                    detail_records,
                    scope_type,
                    scope_value
                )
            else:
                # Global metrics
                metrics = self._compute_global_metrics(detail_records)
            
            # Generate response
            answer = AnswerTemplateRouter.generate_answer(
                query_type=query_type,
                answer_mode=answer_mode,
                entity=scope_value,
                metrics=metrics,
                scope_type=scope_type,
                question=question
            )
            
            # Update response
            response["answer"] = answer
            response["queryType"] = query_type
            response["scopeType"] = scope_type
            response["scopeValue"] = scope_value
            response["answerMode"] = answer_mode
            response["confidence"] = confidence
            
        except Exception as e:
            logging.error(f"Error processing question: {str(e)}")
            response["answer"] = f"I encountered an error processing your question: {str(e)}"
            response["queryType"] = "error"
            response["confidence"] = 0.0
        
        # Add to conversation history
        if response["answer"]:
            response["conversationHistory"].append({
                "question": question,
                "answer": response["answer"],
                "queryType": response["queryType"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 10 turns
            if len(response["conversationHistory"]) > 10:
                response["conversationHistory"] = response["conversationHistory"][-10:]
        
        return response
    
    @staticmethod
    def _compute_global_metrics(detail_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute global metrics for all records."""
        if not detail_records:
            return {
                "filteredRecordsCount": 0,
                "changedCount": 0,
                "changeRate": 0.0,
                "scopedDrivers": {"primary": "unknown"}
            }
        
        changed_count = sum(1 for r in detail_records if r.get("changed", False))
        total_count = len(detail_records)
        change_rate = round(changed_count / max(total_count, 1) * 100, 1)
        
        # Compute drivers
        qty_changed = sum(1 for r in detail_records if r.get("qtyChanged", False))
        supplier_changed = sum(1 for r in detail_records if r.get("supplierChanged", False))
        design_changed = sum(1 for r in detail_records if r.get("designChanged", False))
        schedule_changed = sum(1 for r in detail_records if r.get("scheduleChanged", False))
        
        # Identify primary driver
        drivers = [
            ("quantity", qty_changed),
            ("supplier", supplier_changed),
            ("design", design_changed),
            ("schedule", schedule_changed)
        ]
        primary_driver = max(drivers, key=lambda x: x[1])[0] if changed_count > 0 else "unknown"
        
        return {
            "filteredRecordsCount": total_count,
            "changedCount": changed_count,
            "changeRate": change_rate,
            "scopedDrivers": {
                "primary": primary_driver,
                "quantity": qty_changed,
                "supplier": supplier_changed,
                "design": design_changed,
                "schedule": schedule_changed
            }
        }
    
    @staticmethod
    def _generate_out_of_scope_response(question: str) -> str:
        """Generate response for out-of-scope questions."""
        return """I'm a Planning Intelligence assistant specialized in analyzing planning data.

I can help you with questions like:
- "What's the planning status?"
- "Why is LOC001 risky?"
- "Compare LOC001 vs LOC002"
- "Which suppliers have design changes?"
- "Show top contributing records"

How can I help with your planning analysis?"""
    
    @staticmethod
    def _generate_clarification_response(question: str) -> str:
        """Generate response when clarification is needed."""
        return f"""I'm not sure how to interpret your question: "{question}"

Could you rephrase it to be more specific about planning data? For example:
- Mention a location (e.g., "LOC001", "CYS20_F01C01")
- Mention a change type (e.g., "quantity", "supplier", "design")
- Ask about a specific metric (e.g., "risk", "change rate", "drivers")

Example questions I can answer:
- "Why is CYS20_F01C01 risky?"
- "Which suppliers have design changes?"
- "Show materials with quantity changes"
- "What changed most?"
- "Which materials are affected?"

What would you like to know about your planning data?"""


def handle_nlp_query(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP endpoint handler for NLP queries from Copilot UI.
    
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
    
    logging.info("NLP Query endpoint triggered.")
    
    try:
        # Parse request
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON body"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Extract parameters
    question = body.get("question", "").strip()
    detail_records = body.get("detail_records", [])
    conversation_history = body.get("conversation_history", [])
    
    # Validate
    if not question:
        return func.HttpResponse(
            json.dumps({"error": "Question is required"}),
            mimetype="application/json",
            status_code=400
        )
    
    if not detail_records:
        return func.HttpResponse(
            json.dumps({"error": "detail_records is required"}),
            mimetype="application/json",
            status_code=400
        )
    
    # Process question
    response = NLPEndpointHandler.process_question(
        question,
        detail_records,
        conversation_history
    )
    
    # Return response
    return func.HttpResponse(
        json.dumps(response, default=str),
        mimetype="application/json",
        status_code=200
    )
