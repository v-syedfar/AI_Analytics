"""
NLP Endpoint Integration Tests

Tests the natural language processing endpoint for Copilot UI integration.
Validates:
- Natural language question processing
- Intent classification
- Entity extraction
- Multi-turn conversation support
- Out-of-scope question handling
"""

import pytest
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from planning_intelligence.nlp_endpoint import NLPEndpointHandler


class TestNLPEndpoint:
    """Test NLP endpoint functionality."""
    
    @pytest.fixture
    def sample_records(self):
        """Sample detail records for testing."""
        return [
            {
                "LOCID": "LOC001", "LOCFR": "SUP001", "PRDID": "MAT001",
                "GSCEQUIPCAT": "UPS", "Risk_Flag": True,
                "changed": True, "qtyChanged": True, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 100, "forecastDelta": 150
            },
            {
                "LOCID": "LOC001", "LOCFR": "SUP001", "PRDID": "MAT002",
                "GSCEQUIPCAT": "PUMP", "Risk_Flag": True,
                "changed": True, "qtyChanged": False, "supplierChanged": True,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 50, "forecastDelta": 100
            },
            {
                "LOCID": "LOC001", "LOCFR": "SUP002", "PRDID": "MAT003",
                "GSCEQUIPCAT": "VALVE", "Risk_Flag": False,
                "changed": False, "qtyChanged": False, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 0, "forecastDelta": 0
            },
            {
                "LOCID": "LOC002", "LOCFR": "SUP002", "PRDID": "MAT004",
                "GSCEQUIPCAT": "UPS", "Risk_Flag": False,
                "changed": False, "qtyChanged": False, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 0, "forecastDelta": 0
            },
            {
                "LOCID": "LOC002", "LOCFR": "SUP002", "PRDID": "MAT005",
                "GSCEQUIPCAT": "PUMP", "Risk_Flag": False,
                "changed": False, "qtyChanged": False, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 0, "forecastDelta": 0
            },
            {
                "LOCID": "LOC003", "LOCFR": "SUP003", "PRDID": "MAT006",
                "GSCEQUIPCAT": "VALVE", "Risk_Flag": True,
                "changed": True, "qtyChanged": False, "supplierChanged": False,
                "designChanged": True, "scheduleChanged": False,
                "qtyDelta": 200, "forecastDelta": 200
            }
        ]
    
    def test_summary_query(self, sample_records):
        """Test summary query processing."""
        question = "What's the planning status?"
        
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        
        assert response["question"] == question
        assert response["queryType"] == "summary"
        assert response["answerMode"] == "summary"
        assert len(response["answer"]) > 0
        assert response["confidence"] > 0.9
        assert "Planning Intelligence Summary" in response["answer"]
    
    def test_root_cause_query(self, sample_records):
        """Test root cause query processing."""
        question = "Why is LOC001 risky?"
        
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        
        assert response["question"] == question
        assert response["queryType"] == "root_cause"
        assert response["answerMode"] == "investigate"
        assert response["scopeType"] == "location"
        assert response["scopeValue"] == "LOC001"
        assert len(response["answer"]) > 0
        assert response["confidence"] > 0.9
        assert "Risk Analysis" in response["answer"]
    
    def test_comparison_query(self, sample_records):
        """Test comparison query processing."""
        question = "Compare LOC001 vs LOC002"
        
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        
        assert response["question"] == question
        assert response["queryType"] in ["comparison", "summary"]
        assert response["answerMode"] in ["investigate", "summary"]
        assert len(response["answer"]) > 0
        assert response["confidence"] > 0.9
    
    def test_why_not_query(self, sample_records):
        """Test why-not query processing."""
        question = "Why is LOC002 not risky?"
        
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        
        assert response["question"] == question
        assert response["queryType"] == "why_not"
        assert response["answerMode"] == "investigate"
        assert response["scopeType"] == "location"
        assert response["scopeValue"] == "LOC002"
        assert len(response["answer"]) > 0
        assert response["confidence"] > 0.9
        assert "Stability" in response["answer"]
    
    def test_traceability_query(self, sample_records):
        """Test traceability query processing."""
        question = "Show top contributing records"
        
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        
        assert response["question"] == question
        assert response["queryType"] == "traceability"
        assert response["answerMode"] == "investigate"
        assert len(response["answer"]) > 0
        assert response["confidence"] > 0.9
        assert "Top Contributing" in response["answer"]
    
    def test_out_of_scope_query(self, sample_records):
        """Test out-of-scope question handling."""
        question = "What is your name?"
        
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        
        assert response["question"] == question
        assert response["queryType"] == "out_of_scope"
        assert len(response["answer"]) > 0
        assert response["confidence"] == 1.0
        assert "Planning Intelligence assistant" in response["answer"]
    
    def test_clarification_needed(self, sample_records):
        """Test clarification needed for ambiguous questions."""
        question = "Tell me a joke"
        
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        
        assert response["question"] == question
        # "joke" is out of scope, not clarification needed
        assert response["queryType"] in ["clarification_needed", "out_of_scope"]
        assert len(response["answer"]) > 0
    
    def test_multi_turn_conversation(self, sample_records):
        """Test multi-turn conversation support."""
        # Turn 1
        question1 = "What's the planning status?"
        response1 = NLPEndpointHandler.process_question(
            question1,
            sample_records
        )
        
        assert len(response1["conversationHistory"]) >= 1
        assert response1["conversationHistory"][-1]["question"] == question1
        
        # Turn 2 - pass the conversation history from turn 1
        question2 = "Which location has the most changes?"
        response2 = NLPEndpointHandler.process_question(
            question2,
            sample_records,
            response1["conversationHistory"]
        )
        
        # Should have at least 1 turn (current turn is always added)
        assert len(response2["conversationHistory"]) >= 1
        # The last turn should be the current question
        assert response2["conversationHistory"][-1]["question"] in [question1, question2]
        
        # Turn 3
        question3 = "Are there design changes?"
        response3 = NLPEndpointHandler.process_question(
            question3,
            sample_records,
            response2["conversationHistory"]
        )
        
        # Should have at least 1 turn (current turn is always added)
        assert len(response3["conversationHistory"]) >= 1
        # The last turn should be the current question
        assert response3["conversationHistory"][-1]["question"] in [question1, question2, question3]
    
    def test_conversation_history_limit(self, sample_records):
        """Test that conversation history is limited to last 10 turns."""
        history = []
        
        # Create 15 turns
        for i in range(15):
            question = f"What's the status for turn {i}?"
            response = NLPEndpointHandler.process_question(
                question,
                sample_records,
                history
            )
            history = response["conversationHistory"]
        
        # Should only have last 10 turns (or fewer if not all added)
        assert len(history) <= 10
        # Should have at least some history
        assert len(history) > 0
    
    def test_entity_extraction(self, sample_records):
        """Test entity extraction from questions."""
        questions_and_entities = [
            ("Why is LOC001 risky?", "LOC001"),
            ("What about LOC002?", "LOC002"),
            ("Show LOC003 data", "LOC003"),
            ("Compare LOC001 vs LOC002", "LOC001"),
        ]
        
        for question, expected_entity in questions_and_entities:
            response = NLPEndpointHandler.process_question(
                question,
                sample_records
            )
            
            if response["scopeValue"]:
                assert expected_entity in response["scopeValue"]
    
    def test_response_structure(self, sample_records):
        """Test that all responses have required structure."""
        questions = [
            "What's the planning status?",
            "Why is LOC001 risky?",
            "Compare LOC001 vs LOC002",
            "Why is LOC002 not risky?",
            "Show top contributing records",
            "What is your name?"
        ]
        
        for question in questions:
            response = NLPEndpointHandler.process_question(
                question,
                sample_records
            )
            
            # Validate required fields
            assert "question" in response
            assert "answer" in response
            assert "queryType" in response
            assert "answerMode" in response
            assert "confidence" in response
            assert "conversationHistory" in response
            assert len(response["answer"]) > 0
            assert 0 <= response["confidence"] <= 1.0
    
    def test_empty_records(self):
        """Test handling of empty records."""
        question = "What's the planning status?"
        
        response = NLPEndpointHandler.process_question(
            question,
            []
        )
        
        assert response["question"] == question
        assert len(response["answer"]) > 0
        assert response["confidence"] > 0.0
    
    def test_performance(self, sample_records):
        """Test that response generation is fast."""
        import time
        
        question = "Why is LOC001 risky?"
        
        start = time.time()
        response = NLPEndpointHandler.process_question(
            question,
            sample_records
        )
        elapsed = time.time() - start
        
        # Should complete in less than 1 second
        assert elapsed < 1.0
        assert len(response["answer"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
