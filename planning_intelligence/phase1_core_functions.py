"""
Phase 1: Core Functions - Scope Extraction, Classification, and Answer Mode

This module implements the core functions needed for query-specific computation:
1. Scope extraction from questions
2. Question classification with scope
3. Answer mode determination
4. Scoped metrics computation
"""

import re
from typing import Dict, List, Any, Tuple, Optional


class ScopeExtractor:
    """Extracts scope (location, supplier, material group, etc.) from questions."""
    
    @staticmethod
    def extract_scope(question: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract scope from question.
        
        Returns: (scope_type, scope_value)
        
        Examples:
        - "Why is LOC001 risky?" → ("location", "LOC001")
        - "Compare LOC001 vs LOC002" → ("location", ["LOC001", "LOC002"])
        - "Which supplier has design changes?" → ("supplier", None)
        - "Show top records" → (None, None)
        """
        q = question.lower()
        
        # Location patterns - check for LOC codes first
        loc_match = re.search(r'\b(LOC\d+|[A-Z]{3}\d{2}_[A-Z]\d{2}[A-Z]\d{2})\b', q, re.IGNORECASE)
        if loc_match:
            return ("location", loc_match.group(1).upper())
        
        # Location named patterns
        loc_named = re.search(r'\blocation\s+(\w+)\b', q, re.IGNORECASE)
        if loc_named:
            return ("location", f"location_{loc_named.group(1).upper()}")
        
        # Supplier patterns - check for SUP codes first
        sup_match = re.search(r'\b(SUP\d+)\b', q, re.IGNORECASE)
        if sup_match:
            return ("supplier", sup_match.group(1).upper())
        
        # Supplier named patterns
        sup_named = re.search(r'\bsupplier\s+(\w+)\b', q, re.IGNORECASE)
        if sup_named:
            return ("supplier", f"supplier_{sup_named.group(1).upper()}")
        
        # Material group patterns - check for known categories first
        if re.search(r'\b(UPS|PUMP|VALVE)\b', q, re.IGNORECASE):
            mg_match = re.search(r'\b(UPS|PUMP|VALVE)\b', q, re.IGNORECASE)
            return ("material_group", mg_match.group(1).upper())
        
        # Material group named patterns
        mg_named = re.search(r'\bmaterial\s+group\s+(\w+)\b', q, re.IGNORECASE)
        if mg_named:
            return ("material_group", f"group_{mg_named.group(1).upper()}")
        
        # Material ID patterns - check for MAT codes first
        mat_match = re.search(r'\b(MAT\d+)\b', q, re.IGNORECASE)
        if mat_match:
            return ("material_id", mat_match.group(1).upper())
        
        # Material ID named patterns
        mat_named = re.search(r'\bmaterial\s+(\w+)\b', q, re.IGNORECASE)
        if mat_named:
            return ("material_id", f"material_{mat_named.group(1).upper()}")
        
        # Risk type patterns
        if any(w in q for w in ["high risk", "low risk", "critical", "normal"]):
            return ("risk_type", None)
        
        return (None, None)
    
    @staticmethod
    def extract_comparison_entities(question: str) -> List[str]:
        """
        Extract entities for comparison questions.
        
        Examples:
        - "Compare LOC001 vs LOC002" → ["LOC001", "LOC002"]
        - "Compare UPS vs PUMP" → ["UPS", "PUMP"]
        """
        # Find all location patterns
        locations = re.findall(r'\b([A-Z]{3}\d{2}_[A-Z]\d{2}[A-Z]\d{2}|LOC\d+)\b', question, re.IGNORECASE)
        if len(locations) >= 2:
            return [loc.upper() for loc in locations[:2]]
        
        # Find all material groups
        material_groups = re.findall(r'\b(UPS|PUMP|VALVE)\b', question, re.IGNORECASE)
        if len(material_groups) >= 2:
            return [mg.upper() for mg in material_groups[:2]]
        
        # Find all suppliers
        suppliers = re.findall(r'\b(SUP\d+)\b', question, re.IGNORECASE)
        if len(suppliers) >= 2:
            return [sup.upper() for sup in suppliers[:2]]
        
        return []


class QuestionClassifier:
    """Classifies questions into intent types."""
    
    @staticmethod
    def classify_question(question: str) -> str:
        """
        Classify question into intent type.
        
        Returns: "comparison" | "root_cause" | "why_not" | "traceability" | "summary"
        """
        q = question.lower()
        
        # Comparison patterns
        if any(word in q for word in ["compare", "vs", "versus", "difference", "similar"]):
            return "comparison"
        
        # Why-not patterns (check before root_cause since "why" and "not" are more specific)
        if "why" in q and "not" in q:
            return "why_not"
        
        # Traceability patterns (check before root_cause since "show" is more specific)
        if any(word in q for word in ["show", "top", "contributing", "records", "impacted", "affected"]):
            return "traceability"
        
        # Root cause patterns
        if any(word in q for word in ["why", "reason", "cause", "risky", "risk", "problem", "issue"]):
            if "not" not in q:
                return "root_cause"
        
        # Default to summary
        return "summary"
    
    @staticmethod
    def classify_with_scope(question: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Classify question and extract scope.
        
        Returns: (query_type, scope_type, scope_value)
        """
        query_type = QuestionClassifier.classify_question(question)
        scope_type, scope_value = ScopeExtractor.extract_scope(question)
        
        return query_type, scope_type, scope_value


class AnswerModeDecider:
    """Determines if answer should be in summary or investigate mode."""
    
    @staticmethod
    def determine_answer_mode(query_type: str, scope_type: Optional[str]) -> str:
        """
        Determine answer mode.
        
        Returns: "summary" | "investigate"
        
        Investigate mode for:
        - comparison (always)
        - root_cause (if scoped)
        - why_not (if scoped)
        - traceability (always)
        - entity-specific questions (if scoped)
        """
        if query_type in ["comparison", "traceability"]:
            return "investigate"
        
        if query_type in ["root_cause", "why_not"] and scope_type:
            return "investigate"
        
        if scope_type and query_type not in ["summary"]:
            return "investigate"
        
        return "summary"


class ScopedMetricsComputer:
    """Computes metrics for scoped records."""
    
    @staticmethod
    def compute_scoped_metrics(
        detail_records: List[Dict[str, Any]],
        scope_type: str,
        scope_value: str
    ) -> Dict[str, Any]:
        """
        Filter detailRecords to scope and recompute metrics.
        
        Returns: {
            "filteredRecordsCount": int,
            "scopedContributionBreakdown": {...},
            "scopedDrivers": {...},
            "topContributingRecords": [...],
            "scopedMetrics": {
                "changedCount": int,
                "changeRate": float,
                ...
            }
        }
        """
        # Filter records to scope
        if scope_type == "location":
            filtered = [r for r in detail_records if r.get("LOCID") == scope_value]
        elif scope_type == "supplier":
            filtered = [r for r in detail_records if r.get("LOCFR") == scope_value]
        elif scope_type == "material_group":
            filtered = [r for r in detail_records if r.get("GSCEQUIPCAT") == scope_value]
        elif scope_type == "material_id":
            filtered = [r for r in detail_records if r.get("PRDID") == scope_value]
        elif scope_type == "risk_type":
            filtered = [r for r in detail_records if r.get("Risk_Flag") == (scope_value == "high")]
        else:
            filtered = detail_records
        
        if not filtered:
            return {
                "filteredRecordsCount": 0,
                "changedCount": 0,
                "changeRate": 0.0,
                "scopedContributionBreakdown": {},
                "scopedDrivers": {},
                "topContributingRecords": []
            }
        
        # Recompute metrics for filtered records
        changed_count = sum(1 for r in filtered if r.get("changed", False))
        total_count = len(filtered)
        change_rate = round(changed_count / max(total_count, 1) * 100, 1)
        
        # Compute contribution breakdown
        qty_changed = sum(1 for r in filtered if r.get("qtyChanged", False))
        supplier_changed = sum(1 for r in filtered if r.get("supplierChanged", False))
        design_changed = sum(1 for r in filtered if r.get("designChanged", False))
        schedule_changed = sum(1 for r in filtered if r.get("scheduleChanged", False))
        
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
        
        # Top contributing records (by absolute delta)
        top_records = sorted(
            filtered,
            key=lambda r: abs(r.get("qtyDelta", 0)),
            reverse=True
        )[:5]
        
        return {
            "filteredRecordsCount": total_count,
            "changedCount": changed_count,
            "changeRate": change_rate,
            "scopedContributionBreakdown": contribution,
            "scopedDrivers": {
                "primary": primary_driver,
                "changedCount": changed_count,
                "totalCount": total_count
            },
            "topContributingRecords": top_records
        }
