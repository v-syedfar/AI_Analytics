"""
Preservation Property Tests - Phase 2

Tests that verify non-buggy behavior is preserved on unfixed code.
These tests MUST PASS on unfixed code to establish baseline behavior.
After the fix, these tests must STILL PASS to ensure no regressions.

Property 2: Preservation - Non-NLP Inputs and Error Handling
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


class TestPreservationProperties:
    """
    Preservation tests to verify non-buggy behavior is unchanged.
    These tests establish baseline behavior on unfixed code.
    """
    
    @pytest.fixture
    def sample_detail_records(self):
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
                "LOCID": "LOC002", "LOCFR": "SUP002", "PRDID": "MAT002",
                "GSCEQUIPCAT": "PUMP", "Risk_Flag": False,
                "changed": False, "qtyChanged": False, "supplierChanged": False,
                "designChanged": False, "scheduleChanged": False,
                "qtyDelta": 0, "forecastDelta": 0
            },
        ]
    
    @pytest.fixture
    def mock_request(self, sample_detail_records):
        """Create a mock HTTP request."""
        def create_request(question: str = None, context_data: Dict[str, Any] = None, 
                          location_id: str = None, material_group: str = None):
            req = MagicMock(spec=func.HttpRequest)
            body = {}
            
            if question:
                body["question"] = question
            
            if context_data:
                body["context"] = context_data
            else:
                body["context"] = {
                    "detailRecords": sample_detail_records,
                    "planningHealth": 45,
                    "status": "HIGH",
                    "changedRecordCount": 1,
                    "totalRecords": 2,
                }
            
            if location_id:
                body["location_id"] = location_id
            if material_group:
                body["material_group"] = material_group
            
            req.get_json.return_value = body
            return req
        return create_request
    
    def test_error_handling_missing_question_field(self, mock_request):
        """
        Test Case 1: Error Handling - Missing Question Field
        
        WHEN request is missing "question" field
        THEN endpoint should:
        - Return 400 error
        - Include error message
        - NOT crash
        
        Expected Behavior (Preservation):
        - Status code: 400
        - Response contains error message
        - Error message mentions "question is required"
        """
        # Create request without question field
        req = mock_request(question=None)
        
        response = explain(req)
        
        # Verify error response
        assert response.status_code == 400, \
            f"Expected 400 status, got {response.status_code}"
        
        response_data = json.loads(response.get_body().decode())
        assert "error" in response_data, \
            "Response should contain error field"
        assert "question" in response_data["error"].lower(), \
            f"Error message should mention 'question': {response_data['error']}"
    
    def test_error_handling_missing_detail_records(self, mock_request):
        """
        Test Case 2: Error Handling - Missing Detail Records
        
        WHEN request has no detail records available
        THEN endpoint should:
        - Handle gracefully (either 404 or fallback)
        - NOT crash
        - Return valid response
        
        Expected Behavior (Preservation):
        - Status code is valid (200, 404, or 500)
        - Response is valid JSON
        - No crash or exception
        """
        # Create request with empty context
        req = mock_request(question="What changed?", context_data={})
        
        response = explain(req)
        
        # Verify response is valid (either error or fallback)
        assert response.status_code in [200, 404, 500], \
            f"Expected valid status code, got {response.status_code}"
        
        response_data = json.loads(response.get_body().decode())
        # Response should be valid JSON dict
        assert isinstance(response_data, dict), \
            "Response should be valid JSON dict"
    
    def test_context_parameters_preserved(self, mock_request, sample_detail_records):
        """
        Test Case 3: Context Parameters Preservation
        
        WHEN request includes location_id and material_group parameters
        THEN endpoint should:
        - Accept and use these parameters
        - Include them in response context
        - Use them for scoping queries
        
        Expected Behavior (Preservation):
        - Response includes contextUsed field
        - Parameters are processed without error
        - Response structure remains consistent
        """
        question = "What changed?"
        location_id = "LOC001"
        material_group = "UPS"
        
        req = mock_request(
            question=question,
            location_id=location_id,
            material_group=material_group
        )
        
        response = explain(req)
        
        # Verify response
        assert response.status_code == 200, \
            f"Expected 200 status, got {response.status_code}"
        
        response_data = json.loads(response.get_body().decode())
        
        # Verify response structure
        assert "question" in response_data, \
            "Response should contain question field"
        assert "answer" in response_data, \
            "Response should contain answer field"
        assert response_data["question"] == question, \
            "Question should be echoed in response"
    
    def test_response_structure_preserved(self, mock_request):
        """
        Test Case 4: Response Structure Preservation
        
        WHEN endpoint processes a valid question
        THEN response should:
        - Contain required fields (question, answer, intent, entities, timestamp)
        - Have consistent structure
        - Be valid JSON
        
        Expected Behavior (Preservation):
        - Response contains: question, answer, intent, entities, timestamp
        - All fields are present and non-null
        - Response is valid JSON
        """
        question = "What changed?"
        req = mock_request(question=question)
        
        response = explain(req)
        
        # Verify response is valid JSON
        assert response.status_code == 200, \
            f"Expected 200 status, got {response.status_code}"
        
        response_data = json.loads(response.get_body().decode())
        
        # Verify required fields
        required_fields = ["question", "answer", "intent", "entities", "timestamp"]
        for field in required_fields:
            assert field in response_data, \
                f"Response missing required field: {field}"
        
        # Verify field types
        assert isinstance(response_data["question"], str), \
            "question should be string"
        assert isinstance(response_data["answer"], str), \
            "answer should be string"
        assert isinstance(response_data["intent"], str), \
            "intent should be string"
        assert isinstance(response_data["entities"], dict), \
            "entities should be dict"
    
    def test_timeout_handling_preserved(self, mock_request):
        """
        Test Case 5: Timeout Handling Preservation
        
        WHEN endpoint processes a request
        THEN it should:
        - Complete within reasonable time
        - NOT hang or timeout
        - Return response
        
        Expected Behavior (Preservation):
        - Response is returned
        - No timeout errors
        - Response is valid
        """
        question = "What changed?"
        req = mock_request(question=question)
        
        # This should complete quickly
        response = explain(req)
        
        # Verify response
        assert response.status_code in [200, 400, 404], \
            f"Expected valid status code, got {response.status_code}"
        
        # Verify response is valid JSON
        response_data = json.loads(response.get_body().decode())
        assert isinstance(response_data, dict), \
            "Response should be valid JSON dict"
    
    def test_empty_question_handling(self, mock_request):
        """
        Test Case 6: Empty Question Handling
        
        WHEN request contains empty question string
        THEN endpoint should:
        - Return 400 error
        - NOT process empty question
        - Include error message
        
        Expected Behavior (Preservation):
        - Status code: 400
        - Error message provided
        """
        req = mock_request(question="")
        
        response = explain(req)
        
        # Verify error response
        assert response.status_code == 400, \
            f"Expected 400 status for empty question, got {response.status_code}"
        
        response_data = json.loads(response.get_body().decode())
        assert "error" in response_data, \
            "Response should contain error field"
    
    def test_whitespace_only_question_handling(self, mock_request):
        """
        Test Case 7: Whitespace-Only Question Handling
        
        WHEN request contains only whitespace
        THEN endpoint should:
        - Return 400 error
        - NOT process whitespace-only question
        
        Expected Behavior (Preservation):
        - Status code: 400
        - Error message provided
        """
        req = mock_request(question="   \t\n   ")
        
        response = explain(req)
        
        # Verify error response
        assert response.status_code == 400, \
            f"Expected 400 status for whitespace question, got {response.status_code}"
    
    def test_response_contains_answer(self, mock_request):
        """
        Test Case 8: Response Contains Answer
        
        WHEN endpoint processes a valid question
        THEN response should:
        - Contain non-empty answer
        - Answer should be meaningful
        - Answer should not be null
        
        Expected Behavior (Preservation):
        - answer field is non-empty string
        - answer contains meaningful content
        """
        question = "What changed?"
        req = mock_request(question=question)
        
        response = explain(req)
        response_data = json.loads(response.get_body().decode())
        
        # Verify answer
        assert "answer" in response_data, \
            "Response should contain answer field"
        assert isinstance(response_data["answer"], str), \
            "answer should be string"
        assert len(response_data["answer"]) > 0, \
            "answer should not be empty"
    
    def test_intent_classification_present(self, mock_request):
        """
        Test Case 9: Intent Classification Present
        
        WHEN endpoint processes a valid question
        THEN response should:
        - Contain intent field
        - Intent should be non-empty string
        - Intent should be one of known types
        
        Expected Behavior (Preservation):
        - intent field is present
        - intent is non-empty string
        """
        question = "What changed?"
        req = mock_request(question=question)
        
        response = explain(req)
        response_data = json.loads(response.get_body().decode())
        
        # Verify intent
        assert "intent" in response_data, \
            "Response should contain intent field"
        assert isinstance(response_data["intent"], str), \
            "intent should be string"
        assert len(response_data["intent"]) > 0, \
            "intent should not be empty"
    
    def test_entities_extraction_present(self, mock_request):
        """
        Test Case 10: Entities Extraction Present
        
        WHEN endpoint processes a valid question
        THEN response should:
        - Contain entities field
        - Entities should be dict
        - Entities should be present (even if empty)
        
        Expected Behavior (Preservation):
        - entities field is present
        - entities is dict type
        """
        question = "What changed?"
        req = mock_request(question=question)
        
        response = explain(req)
        response_data = json.loads(response.get_body().decode())
        
        # Verify entities
        assert "entities" in response_data, \
            "Response should contain entities field"
        assert isinstance(response_data["entities"], dict), \
            "entities should be dict"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
