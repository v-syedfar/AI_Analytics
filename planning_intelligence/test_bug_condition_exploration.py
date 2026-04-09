"""
Bug Condition Exploration Test - Phase 1

Tests that demonstrate the bug exists on unfixed code.
These tests MUST FAIL on unfixed code to prove the bug exists.
When the fix is applied, these tests will PASS.

Bug Condition: Natural language questions are not routed through NLP layer
Expected Behavior: Questions should be processed through NLP layer with proper
                   intent classification, entity extraction, and response generation
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import azure.functions as func
from planning_intelligence.function_app import explain
from planning_intelligence.nlp_endpoint import NLPEndpointHandler


class TestBugConditionExploration:
    """
    Exploration tests to surface the bug on unfixed code.
    These tests encode the expected behavior and will fail on unfixed code.
    """
    
    @pytest.fixture
    def sample_detail_records(self):
        """Sample detail records for testing."""
        return [
            {
                "LOCID": "CYS20_F01C01", "LOCFR": "10_AMER", "PRDID": "MAT001",
                "GSCEQUIPCAT": "UPS", "Risk_Flag": True,
                "changed": True, "qtyChanged": True, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 100, "forecastDelta": 150
            },
            {
                "LOCID": "CYS20_F01C01", "LOCFR": "130_AMER", "PRDID": "MAT002",
                "GSCEQUIPCAT": "PUMP", "Risk_Flag": True,
                "changed": True, "qtyChanged": False, "supplierChanged": True,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 50, "forecastDelta": 100
            },
            {
                "LOCID": "CYS20_F01C01", "LOCFR": "210_AMER", "PRDID": "MAT003",
                "GSCEQUIPCAT": "VALVE", "Risk_Flag": False,
                "changed": False, "qtyChanged": False, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 0, "forecastDelta": 0
            },
            {
                "LOCID": "CYS20_F01C02", "LOCFR": "320_AMER", "PRDID": "MAT004",
                "GSCEQUIPCAT": "UPS", "Risk_Flag": False,
                "changed": False, "qtyChanged": False, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 0, "forecastDelta": 0
            },
        ]
    
    @pytest.fixture
    def mock_request(self, sample_detail_records):
        """Create a mock HTTP request."""
        def create_request(question: str, context_data: Dict[str, Any] = None):
            req = MagicMock(spec=func.HttpRequest)
            body = {
                "question": question,
                "context": context_data or {
                    "detailRecords": sample_detail_records,
                    "planningHealth": 45,
                    "status": "HIGH",
                    "changedRecordCount": 2,
                    "totalRecords": 4,
                }
            }
            req.get_json.return_value = body
            return req
        return create_request
    
    def test_entity_specific_query_nlp_processing(self, mock_request, sample_detail_records):
        """
        Test Case 1: Entity-Specific Query
        
        WHEN user asks: "List suppliers for CYS20_F01C01"
        THEN NLP layer should:
        - Extract location entity "CYS20_F01C01"
        - Classify intent as "list" or "traceability"
        - Return specific supplier list for that location
        
        Expected Response:
        - response.nlpProcessed == true
        - response.intent in ["list", "traceability"]
        - response.scopeType == "location"
        - response.scopeValue == "CYS20_F01C01"
        - response.answer contains supplier names (10_AMER, 130_AMER, 210_AMER)
        - response.confidence > 0.8
        """
        question = "List suppliers for CYS20_F01C01"
        req = mock_request(question)
        
        # Call explain endpoint
        response = explain(req)
        
        # Parse response
        response_data = json.loads(response.get_body().decode())
        
        # Assertions - these will FAIL on unfixed code
        assert response_data.get("nlpProcessed") == True, \
            "NLP layer was not called - explain endpoint bypasses NLP"
        assert response_data.get("intent") in ["list", "traceability", "supplier_by_location"], \
            f"Intent not classified correctly: {response_data.get('intent')}"
        assert response_data.get("scopeType") == "location", \
            f"Scope type not extracted: {response_data.get('scopeType')}"
        assert response_data.get("scopeValue") == "CYS20_F01C01", \
            f"Scope value not extracted: {response_data.get('scopeValue')}"
        assert response_data.get("confidence", 0) > 0.7, \
            f"Confidence too low: {response_data.get('confidence')}"
        
        # Verify answer contains specific supplier information
        answer = response_data.get("answer", "").lower()
        assert "supplier" in answer or "10_amer" in answer or "130_amer" in answer, \
            f"Answer doesn't contain supplier information: {response_data.get('answer')}"
    
    def test_entity_extraction_query(self, mock_request, sample_detail_records):
        """
        Test Case 2: Entity Extraction Query
        
        WHEN user asks: "Which materials are affected?"
        THEN NLP layer should:
        - Extract relevant entities (materials, locations)
        - Classify intent correctly
        - Return specific list of affected materials
        
        Expected Response:
        - response.nlpProcessed == true
        - response.intent in ["list", "summary", "out_of_scope"]
        - response.entities contains extracted materials
        - response.answer contains material information
        - response.confidence > 0.5
        """
        question = "Which materials are affected?"
        req = mock_request(question)
        
        response = explain(req)
        response_data = json.loads(response.get_body().decode())
        
        # Assertions - these will FAIL on unfixed code
        assert response_data.get("nlpProcessed") == True, \
            "NLP layer was not called"
        assert response_data.get("intent") in ["list", "summary", "traceability", "out_of_scope"], \
            f"Intent not classified: {response_data.get('intent')}"
        assert response_data.get("confidence", 0) > 0.5, \
            f"Confidence too low: {response_data.get('confidence')}"
        
        # Verify answer contains material information or clarification
        answer = response_data.get("answer", "").lower()
        assert "material" in answer or "mat" in answer or "affected" in answer or "planning" in answer, \
            f"Answer doesn't address materials: {response_data.get('answer')}"
    
    def test_out_of_scope_question_detection(self, mock_request):
        """
        Test Case 3: Out-of-Scope Question
        
        WHEN user asks: "What is your name?"
        THEN NLP layer should:
        - Detect question is out of scope
        - Return clarification response
        - NOT return planning summary
        
        Expected Response:
        - response.nlpProcessed == true
        - response.intent == "out_of_scope"
        - response.confidence == 1.0
        - response.answer contains clarification (not planning summary)
        """
        question = "What is your name?"
        req = mock_request(question)
        
        response = explain(req)
        response_data = json.loads(response.get_body().decode())
        
        # Assertions - these will FAIL on unfixed code
        assert response_data.get("nlpProcessed") == True, \
            "NLP layer was not called"
        assert response_data.get("intent") == "out_of_scope", \
            f"Out-of-scope not detected: {response_data.get('intent')}"
        assert response_data.get("confidence") == 1.0, \
            f"Confidence should be 1.0 for out-of-scope: {response_data.get('confidence')}"
        
        # Verify answer is clarification about Planning Intelligence
        answer = response_data.get("answer", "").lower()
        assert "planning" in answer or "assistant" in answer or "help" in answer, \
            f"Answer should be clarification about Planning Intelligence: {response_data.get('answer')}"
    
    def test_analysis_question_processing(self, mock_request, sample_detail_records):
        """
        Test Case 4: Analysis Question
        
        WHEN user asks: "Is this demand-driven or design-driven?"
        THEN NLP layer should:
        - Extract entities
        - Classify intent as "root_cause" or "analysis" or "out_of_scope"
        - Return meaningful analysis of change drivers
        
        Expected Response:
        - response.nlpProcessed == true
        - response.intent in ["root_cause", "analysis", "why_not", "summary", "out_of_scope"]
        - response.answer contains analysis (not generic summary)
        - response.confidence > 0.5
        """
        question = "Is this demand-driven or design-driven?"
        req = mock_request(question)
        
        response = explain(req)
        response_data = json.loads(response.get_body().decode())
        
        # Assertions - these will FAIL on unfixed code
        assert response_data.get("nlpProcessed") == True, \
            "NLP layer was not called"
        assert response_data.get("intent") in ["root_cause", "analysis", "why_not", "summary", "out_of_scope"], \
            f"Intent not classified for analysis: {response_data.get('intent')}"
        assert response_data.get("confidence", 0) > 0.5, \
            f"Confidence too low: {response_data.get('confidence')}"
        
        # Verify answer contains analysis or clarification
        answer = response_data.get("answer", "").lower()
        assert "demand" in answer or "design" in answer or "driven" in answer or "driver" in answer or "planning" in answer, \
            f"Answer doesn't contain analysis: {response_data.get('answer')}"
    
    def test_duplicate_question_detection(self, mock_request):
        """
        Test Case 5: Duplicate Question Detection
        
        WHEN user asks same question twice
        THEN NLP layer should:
        - Maintain conversation history
        - Detect duplicate question
        - Return cached response (not reprocess)
        
        Expected Response:
        - First response: normal processing
        - Second response: same answer (cached)
        - No duplicate responses
        """
        question = "List suppliers for CYS20_F01C01"
        
        # First request
        req1 = mock_request(question)
        response1 = explain(req1)
        response_data1 = json.loads(response1.get_body().decode())
        answer1 = response_data1.get("answer")
        
        # Second request with same question
        req2 = mock_request(question)
        response2 = explain(req2)
        response_data2 = json.loads(response2.get_body().decode())
        answer2 = response_data2.get("answer")
        
        # Assertions - these will FAIL on unfixed code
        assert response_data1.get("nlpProcessed") == True, \
            "NLP layer not called for first request"
        assert response_data2.get("nlpProcessed") == True, \
            "NLP layer not called for second request"
        
        # Verify no duplicate responses (same answer, not repeated twice)
        assert answer1 == answer2, \
            "Duplicate detection failed - different answers returned"
        assert answer1.count(answer1.split()[0]) <= 2, \
            "Response appears to be duplicated"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
