"""
Phase 3: Integration - Integrate Phase 1 and Phase 2 with the explain endpoint

This module provides the integration layer that:
1. Uses Phase 1 core functions for scope extraction and classification
2. Uses Phase 2 answer templates for answer generation
3. Integrates with the existing explain endpoint
4. Maintains backward compatibility
"""

from typing import Dict, List, Any, Optional, Tuple
from phase1_core_functions import (
    ScopeExtractor,
    QuestionClassifier,
    AnswerModeDecider,
    ScopedMetricsComputer
)
from phase2_answer_templates import AnswerTemplateRouter


class IntegratedQueryProcessor:
    """Process queries using Phase 1 and Phase 2 components."""
    
    @staticmethod
    def process_query(
        question: str,
        detail_records: List[Dict[str, Any]],
        global_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query end-to-end using Phase 1 and Phase 2.
        
        Returns: {
            "question": str,
            "answer": str,
            "queryType": str,
            "answerMode": str,
            "scopeType": Optional[str],
            "scopeValue": Optional[str],
            "investigateMode": Optional[Dict],
            "timestamp": str
        }
        """
        # Step 1: Classify question and extract scope (Phase 1)
        query_type, scope_type, scope_value = QuestionClassifier.classify_with_scope(question)
        
        # Step 2: Determine answer mode (Phase 1)
        answer_mode = AnswerModeDecider.determine_answer_mode(query_type, scope_type)
        
        # Step 3: Compute metrics
        scoped_metrics = None
        investigate_mode_data = None
        comparison_metrics = None
        
        if answer_mode == "investigate" and scope_type and scope_value:
            # Compute scoped metrics (Phase 1)
            scoped_metrics = ScopedMetricsComputer.compute_scoped_metrics(
                detail_records, scope_type, scope_value
            )
            
            # Build investigate mode data
            investigate_mode_data = {
                "scopeType": scope_type,
                "scopeValue": scope_value,
                "filteredRecordsCount": scoped_metrics.get("filteredRecordsCount", 0),
                "changedCount": scoped_metrics.get("changedCount", 0),
                "changeRate": scoped_metrics.get("changeRate", 0),
                "scopedContributionBreakdown": scoped_metrics.get("scopedContributionBreakdown", {}),
                "scopedDrivers": scoped_metrics.get("scopedDrivers", {}),
                "topContributingRecords": scoped_metrics.get("topContributingRecords", [])
            }
        else:
            # Use global metrics for summary mode
            scoped_metrics = global_metrics or IntegratedQueryProcessor._compute_global_metrics(detail_records)
        
        # Step 4: Extract entities for comparison queries
        comparison_entities = None
        if query_type == "comparison":
            comparison_entities = ScopeExtractor.extract_comparison_entities(question)
            
            # Compute comparison metrics for each entity
            if comparison_entities and len(comparison_entities) >= 2:
                comparison_metrics = {}
                for entity in comparison_entities[:2]:  # Compare first two entities
                    entity_metrics = ScopedMetricsComputer.compute_scoped_metrics(
                        detail_records, scope_type, entity
                    )
                    comparison_metrics[entity] = {
                        "filteredRecordsCount": entity_metrics.get("filteredRecordsCount", 0),
                        "changedCount": entity_metrics.get("changedCount", 0),
                        "changeRate": entity_metrics.get("changeRate", 0),
                        "scopedContributionBreakdown": entity_metrics.get("scopedContributionBreakdown", {}),
                        "scopedDrivers": entity_metrics.get("scopedDrivers", {})
                    }
        
        # Step 5: Generate answer using Phase 2
        answer = AnswerTemplateRouter.generate_answer(
            query_type=query_type,
            answer_mode=answer_mode,
            entity=scope_value,
            metrics=scoped_metrics,
            scope_type=scope_type,
            comparison_entities=comparison_entities,
            all_metrics=global_metrics,
            question=question
        )
        
        # Step 6: Build response
        response = {
            "question": question,
            "answer": answer,
            "queryType": query_type,
            "answerMode": answer_mode,
            "scopeType": scope_type,
            "scopeValue": scope_value,
        }
        
        if investigate_mode_data:
            response["investigateMode"] = investigate_mode_data
            
            # Add comparison metrics if this is a comparison query
            if query_type == "comparison" and comparison_metrics:
                response["investigateMode"]["comparisonMetrics"] = comparison_metrics
        
        return response
    
    @staticmethod
    def _compute_global_metrics(detail_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute global metrics for all records."""
        if not detail_records:
            return {
                "changedCount": 0,
                "changeRate": 0.0,
                "filteredRecordsCount": 0,
                "scopedContributionBreakdown": {},
                "scopedDrivers": {"primary": "none"}
            }
        
        changed_count = sum(1 for r in detail_records if r.get("changed", False))
        total_count = len(detail_records)
        change_rate = round(changed_count / max(total_count, 1) * 100, 1)
        
        # Compute contribution breakdown
        qty_changed = sum(1 for r in detail_records if r.get("qtyChanged", False))
        supplier_changed = sum(1 for r in detail_records if r.get("supplierChanged", False))
        design_changed = sum(1 for r in detail_records if r.get("designChanged", False))
        schedule_changed = sum(1 for r in detail_records if r.get("scheduleChanged", False))
        
        contribution = {
            "quantity": round(qty_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
            "supplier": round(supplier_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
            "design": round(design_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
            "schedule": round(schedule_changed / max(changed_count, 1) * 100, 1) if changed_count > 0 else 0,
        }
        
        # Identify primary driver
        drivers_list = [
            ("quantity", qty_changed),
            ("supplier", supplier_changed),
            ("design", design_changed),
            ("schedule", schedule_changed)
        ]
        primary_driver = max(drivers_list, key=lambda x: x[1])[0] if changed_count > 0 else "none"
        
        return {
            "changedCount": changed_count,
            "changeRate": change_rate,
            "filteredRecordsCount": total_count,
            "scopedContributionBreakdown": contribution,
            "scopedDrivers": {
                "primary": primary_driver,
                "changedCount": changed_count,
                "totalCount": total_count
            }
        }


class ExplainEndpointIntegration:
    """Integration with the explain endpoint."""
    
    @staticmethod
    def build_explain_response(
        question: str,
        detail_records: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build explain endpoint response using Phase 1-3 integration.
        
        This replaces the existing answer generation logic in function_app.py
        """
        # Process query using integrated processor
        processor_result = IntegratedQueryProcessor.process_query(
            question, detail_records
        )
        
        # Build response
        response = {
            "question": question,
            "answer": processor_result["answer"],
            "intent": processor_result["queryType"],
            "answerMode": processor_result["answerMode"],
            "dataMode": "reasoning",
            "requiresClarification": False,
            "timestamp": timestamp,
        }
        
        # Add scope information if present
        if processor_result.get("scopeType"):
            response["scope"] = {
                "type": processor_result["scopeType"],
                "value": processor_result["scopeValue"]
            }
        
        # Add investigate mode data if present
        if processor_result.get("investigateMode"):
            response["investigateMode"] = processor_result["investigateMode"]
        
        # Add context if available
        if context:
            response["contextUsed"] = [k for k, v in context.items() if v is not None]
            response["aiInsight"] = context.get("aiInsight")
            response["rootCause"] = context.get("rootCause")
            response["recommendedActions"] = context.get("recommendedActions", [])
            response["planningHealth"] = context.get("planningHealth")
        
        return response
    
    @staticmethod
    def build_explainability_metadata(
        question: str,
        processor_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build explainability metadata for the response.
        
        Includes: confidence score, data coverage, data freshness, etc.
        """
        from datetime import datetime, timezone
        
        # Get data freshness
        last_refreshed = context.get("lastRefreshedAt") if context else None
        freshness_minutes = None
        is_stale = False
        
        if last_refreshed:
            try:
                refreshed_dt = datetime.fromisoformat(last_refreshed.replace("Z", "+00:00"))
                freshness_minutes = round((datetime.now(timezone.utc) - refreshed_dt).total_seconds() / 60, 1)
                is_stale = freshness_minutes > 1440  # stale if > 24 hours
            except (ValueError, TypeError):
                pass
        
        # Compute confidence based on answer mode and scope
        confidence = 100
        if processor_result.get("answerMode") == "summary":
            confidence = 75  # Summary mode is less specific
        
        if processor_result.get("scopeType"):
            confidence = 90  # Scoped answers are more specific
        
        return {
            "confidenceScore": confidence,
            "answerMode": processor_result.get("answerMode"),
            "queryType": processor_result.get("queryType"),
            "scopeType": processor_result.get("scopeType"),
            "scopeValue": processor_result.get("scopeValue"),
            "dataFreshnessMinutes": freshness_minutes,
            "isStale": is_stale,
            "lastRefreshedAt": last_refreshed,
        }
