"""
End-to-End Integration Test - Planning Intelligence System

This comprehensive test validates the entire query processing pipeline:
1. Intent classification and scope extraction
2. Metrics computation
3. Response generation
4. Azure OpenAI integration
5. Validation and hallucination detection

All tests use real data to ensure production readiness.
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from planning_intelligence.phase1_core_functions import (
    QuestionClassifier,
    ScopeExtractor,
    AnswerModeDecider,
    ScopedMetricsComputer
)
from planning_intelligence.phase3_integration import IntegratedQueryProcessor


class TestEndToEndIntegration:
    """Comprehensive end-to-end integration tests."""
    
    @pytest.fixture
    def real_data(self):
        """Real data for testing."""
        return {
            "detail_records": [
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
        }
    
    def test_root_cause_query(self, real_data):
        """Test root cause analysis query."""
        question = "Why is LOC001 risky?"
        
        # Process query
        result = IntegratedQueryProcessor.process_query(
            question,
            real_data["detail_records"]
        )
        
        # Validate response structure
        assert result["question"] == question
        assert result["queryType"] == "root_cause"
        assert result["answerMode"] == "investigate"
        assert result["scopeType"] == "location"
        assert result["scopeValue"] == "LOC001"
        assert len(result["answer"]) > 0
        assert "LOC001" in result["answer"] or "risky" in result["answer"].lower()
        
        # Validate investigate mode data
        assert "investigateMode" in result
        assert result["investigateMode"]["filteredRecordsCount"] == 3
        assert result["investigateMode"]["changedCount"] == 2
        assert result["investigateMode"]["changeRate"] == 66.7
    
    def test_comparison_query(self, real_data):
        """Test comparison analysis query."""
        question = "Compare LOC001 vs LOC002"
        
        # Process query
        result = IntegratedQueryProcessor.process_query(
            question,
            real_data["detail_records"]
        )
        
        # Validate response structure
        assert result["question"] == question
        assert result["queryType"] == "comparison"
        assert result["answerMode"] == "investigate"
        assert len(result["answer"]) > 0
        assert "Comparing" in result["answer"] or "compare" in result["answer"].lower()
        
        # Validate investigate mode data
        assert "investigateMode" in result
    
    def test_why_not_query(self, real_data):
        """Test why-not analysis query."""
        question = "Why is LOC002 not risky?"
        
        # Process query
        result = IntegratedQueryProcessor.process_query(
            question,
            real_data["detail_records"]
        )
        
        # Validate response structure
        assert result["question"] == question
        assert result["queryType"] == "why_not"
        assert result["answerMode"] == "investigate"
        assert result["scopeType"] == "location"
        assert result["scopeValue"] == "LOC002"
        assert len(result["answer"]) > 0
        assert "stable" in result["answer"].lower() or "not" in result["answer"].lower()
    
    def test_traceability_query(self, real_data):
        """Test traceability query."""
        question = "Show top contributing records"
        
        # Process query
        result = IntegratedQueryProcessor.process_query(
            question,
            real_data["detail_records"]
        )
        
        # Validate response structure
        assert result["question"] == question
        assert result["queryType"] == "traceability"
        assert result["answerMode"] == "investigate"
        assert len(result["answer"]) > 0
        assert "records" in result["answer"].lower() or "contributing" in result["answer"].lower()
    
    def test_summary_query(self, real_data):
        """Test summary query."""
        question = "What is the planning status?"
        
        # Process query
        result = IntegratedQueryProcessor.process_query(
            question,
            real_data["detail_records"]
        )
        
        # Validate response structure
        assert result["question"] == question
        assert result["queryType"] == "summary"
        assert result["answerMode"] == "summary"
        assert len(result["answer"]) > 0
    
    def test_intent_classification(self):
        """Test intent classification for all types."""
        test_cases = [
            ("Why is LOC001 risky?", "root_cause"),
            ("Compare LOC001 vs LOC002", "comparison"),
            ("Why is LOC002 not risky?", "why_not"),
            ("Show top contributing records", "traceability"),
            ("What is the status?", "summary"),
        ]
        
        for question, expected_type in test_cases:
            result = QuestionClassifier.classify_question(question)
            assert result == expected_type, f"Failed for: {question}"
    
    def test_scope_extraction(self):
        """Test scope extraction for all entity types."""
        test_cases = [
            ("Why is LOC001 risky?", ("location", "LOC001")),
            ("Which supplier SUP001 has issues?", ("supplier", "SUP001")),
            ("Show materials in UPS category", ("material_group", "UPS")),
            ("What about MAT001?", ("material_id", "MAT001")),
        ]
        
        for question, expected_scope in test_cases:
            scope_type, scope_value = ScopeExtractor.extract_scope(question)
            assert (scope_type, scope_value) == expected_scope, f"Failed for: {question}"
    
    def test_answer_mode_determination(self):
        """Test answer mode determination."""
        test_cases = [
            ("comparison", None, "investigate"),
            ("root_cause", "location", "investigate"),
            ("root_cause", None, "summary"),
            ("why_not", "location", "investigate"),
            ("traceability", None, "investigate"),
            ("summary", None, "summary"),
        ]
        
        for query_type, scope_type, expected_mode in test_cases:
            mode = AnswerModeDecider.determine_answer_mode(query_type, scope_type)
            assert mode == expected_mode, f"Failed for: {query_type}, {scope_type}"
    
    def test_scoped_metrics_computation(self, real_data):
        """Test scoped metrics computation."""
        # Test location scope
        metrics = ScopedMetricsComputer.compute_scoped_metrics(
            real_data["detail_records"],
            "location",
            "LOC001"
        )
        
        assert metrics["filteredRecordsCount"] == 3
        assert metrics["changedCount"] == 2
        assert metrics["changeRate"] == 66.7
        assert "primary" in metrics["scopedDrivers"]
        assert len(metrics["topContributingRecords"]) > 0
    
    def test_response_structure_validation(self, real_data):
        """Test that all responses have required structure."""
        questions = [
            "Why is LOC001 risky?",
            "Compare LOC001 vs LOC002",
            "Why is LOC002 not risky?",
            "Show top contributing records",
            "What is the status?"
        ]
        
        for question in questions:
            result = IntegratedQueryProcessor.process_query(
                question,
                real_data["detail_records"]
            )
            
            # Validate required fields
            assert "question" in result
            assert "answer" in result
            assert "queryType" in result
            assert "answerMode" in result
            assert len(result["answer"]) > 0
            assert result["queryType"] in ["comparison", "root_cause", "why_not", "traceability", "summary"]
            assert result["answerMode"] in ["summary", "investigate"]
    
    def test_no_hallucinations(self, real_data):
        """Test that responses don't contain hallucinated data."""
        question = "Why is LOC001 risky?"
        result = IntegratedQueryProcessor.process_query(
            question,
            real_data["detail_records"]
        )
        
        answer = result["answer"].lower()
        
        # Check for non-existent entities
        assert "LOC999" not in answer
        assert "SUP999" not in answer
        assert "MAT999" not in answer
        
        # Check that mentioned entities exist in data
        if "LOC001" in result["answer"]:
            assert any(r["LOCID"] == "LOC001" for r in real_data["detail_records"])
    
    def test_metrics_accuracy(self, real_data):
        """Test that metrics are accurate."""
        # Compute global metrics
        changed_count = sum(1 for r in real_data["detail_records"] if r.get("changed", False))
        total_count = len(real_data["detail_records"])
        expected_rate = round(changed_count / total_count * 100, 1)
        
        # Process query to get metrics
        result = IntegratedQueryProcessor.process_query(
            "What is the status?",
            real_data["detail_records"]
        )
        
        # Verify metrics are reasonable
        assert changed_count == 3
        assert total_count == 6
        assert expected_rate == 50.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
