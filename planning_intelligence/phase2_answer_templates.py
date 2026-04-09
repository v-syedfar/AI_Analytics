"""
Phase 2: Answer Templates - Generate query-specific answers

This module implements answer templates for different query types:
1. Comparison template - side-by-side comparison
2. Root cause template - why something is risky
3. Why-not template - why something is stable
4. Traceability template - top contributing records
5. Summary template - general summary (backward compatible)
"""

from typing import Dict, List, Any, Optional


class ComparisonAnswerTemplate:
    """Generate comparison answers for side-by-side analysis."""
    
    @staticmethod
    def generate(
        entity1: str,
        entity2: str,
        metrics1: Dict[str, Any],
        metrics2: Dict[str, Any],
        scope_type: str
    ) -> str:
        """
        Generate comparison answer.
        
        Format: "Comparing [entity1] vs [entity2]:
        - [entity1]: [changed_count] changes ([change_rate]%), primary driver: [driver]
        - [entity2]: [changed_count] changes ([change_rate]%), primary driver: [driver]
        [entity1] has [more/fewer] changes than [entity2]."
        Improved to clarify metrics and provide actionable insights.
        """
        changed1 = metrics1.get("changedCount", 0)
        total1 = metrics1.get("filteredRecordsCount", 0)
        rate1 = metrics1.get("changeRate", 0)
        driver1 = metrics1.get("scopedDrivers", {}).get("primary", "unknown")
        
        changed2 = metrics2.get("changedCount", 0)
        total2 = metrics2.get("filteredRecordsCount", 0)
        rate2 = metrics2.get("changeRate", 0)
        driver2 = metrics2.get("scopedDrivers", {}).get("primary", "unknown")
        
        scope_label = scope_type.replace("_", " ").title()
        
        comparison = "more" if changed1 > changed2 else "fewer" if changed1 < changed2 else "the same number of"
        
        answer = f"""📊 Comparing {entity1} vs {entity2}:

**{entity1}:**
  • Total Records: {total1:,}
  • Changed Records: {changed1:,} ({rate1}% change rate)
  • Primary Driver: {driver1.title()}

**{entity2}:**
  • Total Records: {total2:,}
  • Changed Records: {changed2:,} ({rate2}% change rate)
  • Primary Driver: {driver2.title()}

**Summary:** {entity1} has {comparison} changes than {entity2}. """
        
        if changed1 > changed2:
            answer += f"\n{entity1} is riskier due to higher change frequency ({rate1}% vs {rate2}%)."
            answer += f"\n\n**Recommended Action:** Prioritize review of {entity1}, focusing on {driver1} changes."
        elif changed1 < changed2:
            answer += f"\n{entity2} is riskier due to higher change frequency ({rate2}% vs {rate1}%)."
            answer += f"\n\n**Recommended Action:** Prioritize review of {entity2}, focusing on {driver2} changes."
        else:
            answer += f"\nBoth have similar risk profiles ({rate1}% change rate)."
            answer += f"\n\n**Recommended Action:** Review both locations, focusing on {driver1} and {driver2} changes respectively."
        
        return answer


class RootCauseAnswerTemplate:
    """Generate root cause answers explaining why something is risky."""
    
    @staticmethod
    def generate(
        entity: str,
        metrics: Dict[str, Any],
        scope_type: str
    ) -> str:
        """
        Generate root cause answer.
        
        Format: "In [entity], [what changed]. This is risky because [why]. [Action]"
        Improved to clarify driver breakdown and multiple changes.
        """
        changed_count = metrics.get("changedCount", 0)
        total_count = metrics.get("filteredRecordsCount", 0)
        change_rate = metrics.get("changeRate", 0)
        
        # Get driver counts (not percentages)
        qty_changed = metrics.get("scopedDrivers", {}).get("quantity", 0)
        supplier_changed = metrics.get("scopedDrivers", {}).get("supplier", 0)
        design_changed = metrics.get("scopedDrivers", {}).get("design", 0)
        schedule_changed = metrics.get("scopedDrivers", {}).get("schedule", 0)
        
        primary_driver = metrics.get("scopedDrivers", {}).get("primary", "unknown")
        top_records = metrics.get("topContributingRecords", [])
        
        scope_label = scope_type.replace("_", " ").title()
        
        # Build what changed
        what_changed = f"{changed_count} of {total_count} records have changed ({change_rate}%)"
        
        # Build driver breakdown with counts
        driver_breakdown = f"""  • Quantity: {qty_changed} records
  • Schedule: {schedule_changed} records
  • Design: {design_changed} records
  • Supplier: {supplier_changed} records"""
        
        # Build action
        action = f"Review the {changed_count} changed records and prioritize {primary_driver} changes."
        
        answer = f"""⚠️ Risk Analysis for {entity}:

**What Changed:** {what_changed}

**Why It's Risky:** The primary driver is {primary_driver} changes

**Change Breakdown (by frequency):**
{driver_breakdown}

ℹ️ Note: Some records have multiple change types, so totals may exceed changed record count.

**Recommended Action:** {action}"""
        
        if top_records:
            answer += f"\n\n**Top Contributing Records:** {len(top_records)} records with largest deltas"
        
        return answer


class WhyNotAnswerTemplate:
    """Generate why-not answers explaining why something is stable."""
    
    @staticmethod
    def generate(
        entity: str,
        metrics: Dict[str, Any],
        scope_type: str,
        all_metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate why-not answer.
        
        Format: "[Entity] is stable because [reasons]. [Comparison if available]"
        """
        changed_count = metrics.get("changedCount", 0)
        total_count = metrics.get("filteredRecordsCount", 0)
        change_rate = metrics.get("changeRate", 0)
        
        scope_label = scope_type.replace("_", " ").title()
        
        # Build stability statement
        if changed_count == 0:
            stability = f"no records have changed"
        else:
            stability = f"only {changed_count} out of {total_count} records have changed ({change_rate}%)"
        
        answer = f"""✅ Stability Analysis for {entity}:

**Why It's Stable:** {stability}

This indicates a low-risk, stable planning environment for {entity}."""
        
        # Add comparison if all_metrics provided
        if all_metrics:
            global_changed = all_metrics.get("changedCount", 0)
            global_rate = all_metrics.get("changeRate", 0)
            
            if global_rate > change_rate:
                answer += f"\n\n**Comparison:** {entity} is more stable than the overall portfolio ({change_rate}% vs {global_rate}% change rate)."
            elif global_rate < change_rate:
                answer += f"\n\n**Comparison:** {entity} is less stable than the overall portfolio ({change_rate}% vs {global_rate}% change rate)."
        
        return answer


class TraceabilityAnswerTemplate:
    """Generate traceability answers showing top contributing records."""
    
    @staticmethod
    def generate(
        entity: str,
        metrics: Dict[str, Any],
        scope_type: str
    ) -> str:
        """
        Generate traceability answer.
        
        Format: "📊 Top [N] contributing records:
        1. [location] - [material] - [delta] - [change_type] - [risk]
        ..."
        """
        top_records = metrics.get("topContributingRecords", [])
        filtered_count = metrics.get("filteredRecordsCount", 0)
        
        scope_label = scope_type.replace("_", " ").title()
        
        answer = f"""📊 Top Contributing Records for {entity}:

**Total Records:** {filtered_count}
**Top Contributors:** {len(top_records)} records with largest deltas

"""
        
        if not top_records:
            answer += "No records found."
            return answer
        
        for i, record in enumerate(top_records, 1):
            location = record.get("LOCID", "Unknown")
            material = record.get("PRDID", "Unknown")
            delta = record.get("qtyDelta", 0)
            
            # Determine change type
            change_types = []
            if record.get("qtyChanged"):
                change_types.append("Qty")
            if record.get("supplierChanged"):
                change_types.append("Supplier")
            if record.get("designChanged"):
                change_types.append("Design")
            if record.get("scheduleChanged"):
                change_types.append("Schedule")
            
            change_type = ", ".join(change_types) if change_types else "Unknown"
            
            # Determine risk level
            risk = "High" if record.get("Risk_Flag") else "Normal"
            
            answer += f"{i}. **{location}** - {material}\n"
            answer += f"   - Delta: {delta}\n"
            answer += f"   - Changes: {change_type}\n"
            answer += f"   - Risk: {risk}\n\n"
        
        return answer


class SummaryAnswerTemplate:
    """Generate summary answers (backward compatible)."""
    
    @staticmethod
    def generate(
        question: str,
        metrics: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate summary answer (backward compatible).
        
        This is the default template for unscoped questions.
        Improved to clarify metrics and driver breakdown.
        """
        changed_count = metrics.get("changedCount", 0)
        total_count = metrics.get("filteredRecordsCount", 0)
        change_rate = metrics.get("changeRate", 0)
        
        # Get driver counts (not percentages)
        qty_changed = metrics.get("scopedDrivers", {}).get("quantity", 0)
        supplier_changed = metrics.get("scopedDrivers", {}).get("supplier", 0)
        design_changed = metrics.get("scopedDrivers", {}).get("design", 0)
        schedule_changed = metrics.get("scopedDrivers", {}).get("schedule", 0)
        
        primary_driver = metrics.get("scopedDrivers", {}).get("primary", "unknown")
        
        # Build driver breakdown with counts and clarification
        driver_breakdown = f"""**Change Drivers (by frequency):**
  • Quantity: {qty_changed} records
  • Schedule: {schedule_changed} records
  • Design: {design_changed} records
  • Supplier: {supplier_changed} records
  
  ℹ️ Note: Some records have multiple change types, so totals may exceed changed record count."""
        
        answer = f"""📊 Planning Intelligence Summary:

**Overall Metrics:**
  • Total Records: {total_count:,}
  • Changed Records: {changed_count:,} ({change_rate}% change rate)
  • Primary Driver: {primary_driver.title()}

{driver_breakdown}

**Status:** 🟡 HIGH
**Action:** Review planning adjustments needed.

**Recommended Actions:**
  1. Prioritize {primary_driver} changes for immediate review
  2. Validate {primary_driver} change impact on planning
  3. Coordinate with supply chain and engineering teams
  4. Establish baseline parameters for new records
  5. Monitor trend for next planning cycle"""
        
        return answer


class AnswerTemplateRouter:
    """Route to appropriate answer template based on query type and mode."""
    
    @staticmethod
    def generate_answer(
        query_type: str,
        answer_mode: str,
        entity: Optional[str],
        metrics: Dict[str, Any],
        scope_type: Optional[str],
        comparison_entities: Optional[List[str]] = None,
        all_metrics: Optional[Dict[str, Any]] = None,
        question: Optional[str] = None
    ) -> str:
        """
        Route to appropriate answer template.
        
        Args:
            query_type: "comparison", "root_cause", "why_not", "traceability", "summary"
            answer_mode: "summary" or "investigate"
            entity: The entity being analyzed (location, supplier, etc.)
            metrics: Computed metrics for the entity
            scope_type: Type of scope (location, supplier, etc.)
            comparison_entities: For comparison queries, list of entities to compare
            all_metrics: Global metrics for comparison
            question: Original question
        
        Returns:
            Generated answer string
        """
        if query_type == "comparison" and comparison_entities and len(comparison_entities) >= 2:
            # Get metrics for both entities (would need to be computed separately)
            # For now, use the provided metrics for entity1
            return ComparisonAnswerTemplate.generate(
                comparison_entities[0],
                comparison_entities[1],
                metrics,
                all_metrics or metrics,
                scope_type or "unknown"
            )
        
        elif query_type == "root_cause" and answer_mode == "investigate":
            return RootCauseAnswerTemplate.generate(
                entity or "this scope",
                metrics,
                scope_type or "unknown"
            )
        
        elif query_type == "why_not" and answer_mode == "investigate":
            return WhyNotAnswerTemplate.generate(
                entity or "this scope",
                metrics,
                scope_type or "unknown",
                all_metrics
            )
        
        elif query_type == "traceability":
            return TraceabilityAnswerTemplate.generate(
                entity or "this scope",
                metrics,
                scope_type or "unknown"
            )
        
        else:  # Default to summary
            return SummaryAnswerTemplate.generate(
                question or "Planning Intelligence Query",
                metrics,
                None
            )
