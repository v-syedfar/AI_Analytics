"""
MCP Context Builder - Builds complete MCP context for all queries.

MCP = Model Context Protocol = Single Source of Truth

This module constructs the complete context that will be used by:
1. Azure OpenAI (for intent/entity extraction and response generation)
2. ReasoningEngine (for deterministic computation)
3. Validation Guardrails (for hallucination prevention)
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from sap_schema import SAPSchema


class MCPContextBuilder:
    """
    Builds complete MCP context for all queries.
    
    MCP context includes:
    - Query Context: intent, entities, selectedContext
    - Analytics Context: metrics, drivers, risk summary
    - Provenance: data source, freshness, blob files
    - SAP Schema: field dictionary, semantic mapping, domain rules
    """
    
    def __init__(self):
        """Initialize MCP Context Builder."""
        self.sap_schema = SAPSchema()
    
    def build_mcp_context(
        self,
        analytics_data: Dict[str, Any],
        detail_records: List[Dict[str, Any]],
        query_intent: Optional[str] = None,
        extracted_entities: Optional[Dict[str, List[str]]] = None,
        selected_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build complete MCP context.
        
        Args:
            analytics_data: Global analytics data (planningHealth, drivers, etc.)
            detail_records: List of detail records from blob storage
            query_intent: Extracted query intent (comparison, root_cause, etc.)
            extracted_entities: Extracted entities (LOCID, GSCEQUIPCAT, etc.)
            selected_context: User-selected context from clarification
            
        Returns:
            Complete MCP context dict with all required sections
        """
        return {
            "queryContext": self._build_query_context(
                query_intent,
                extracted_entities,
                selected_context
            ),
            "analyticsContext": self._build_analytics_context(
                analytics_data,
                detail_records
            ),
            "provenance": self._build_provenance(analytics_data),
            "sapSchema": self._build_sap_schema(),
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0",
                "description": "Complete MCP context for query processing"
            }
        }
    
    def _build_query_context(
        self,
        query_intent: Optional[str],
        extracted_entities: Optional[Dict[str, List[str]]],
        selected_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build query context section.
        
        Returns:
            Query context with intent, entities, and selectedContext
        """
        return {
            "intent": query_intent or "summary",
            "entities": extracted_entities or {},
            "selectedContext": selected_context or {},
            "description": "User query intent and extracted entities"
        }
    
    def _build_analytics_context(
        self,
        analytics_data: Dict[str, Any],
        detail_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build analytics context section.
        
        Returns:
            Analytics context with metrics, drivers, risk summary
        """
        return {
            "planningHealth": analytics_data.get("planningHealth", "Unknown"),
            "forecastNew": analytics_data.get("forecastNew", 0),
            "forecastOld": analytics_data.get("forecastOld", 0),
            "trendDelta": analytics_data.get("trendDelta", 0),
            "changedRecordCount": analytics_data.get("changedRecordCount", 0),
            "totalRecords": analytics_data.get("totalRecords", len(detail_records)),
            "drivers": analytics_data.get("drivers", {}),
            "riskSummary": analytics_data.get("riskSummary", {}),
            "supplierSummary": analytics_data.get("supplierSummary", {}),
            "materialGroupSummary": analytics_data.get("materialGroupSummary", {}),
            "datacenterSummary": analytics_data.get("datacenterSummary", {}),
            "detailRecords": detail_records,
            "description": "Global analytics metrics and detail records"
        }
    
    def _build_provenance(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build provenance section.
        
        Returns:
            Provenance with data source, freshness, blob files
        """
        return {
            "dataSource": analytics_data.get("dataSource", "Blob"),
            "lastRefreshedAt": analytics_data.get("lastRefreshedAt", datetime.utcnow().isoformat()),
            "blobFileNamesUsed": analytics_data.get("blobFileNamesUsed", []),
            "recordsAnalyzed": analytics_data.get("recordsAnalyzed", 0),
            "description": "Data source and freshness information"
        }
    
    def _build_sap_schema(self) -> Dict[str, Any]:
        """
        Build SAP schema section.
        
        Returns:
            SAP schema with field dictionary, semantic mapping, domain rules
        """
        return {
            "fieldDictionary": self.sap_schema.get_field_dictionary(),
            "semanticMapping": self.sap_schema.get_semantic_mapping(),
            "domainRules": self.sap_schema.get_domain_rules(),
            "description": "SAP field definitions, semantic mappings, and domain rules"
        }
    
    def get_sap_field_dictionary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get SAP field dictionary.
        
        Returns:
            Dictionary of all valid SAP fields with their definitions
        """
        return self.sap_schema.get_field_dictionary()
    
    def get_semantic_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        Get semantic mapping for domain logic.
        
        Returns:
            Dictionary of semantic mappings (forecast_change, design_change, etc.)
        """
        return self.sap_schema.get_semantic_mapping()
    
    def get_domain_rules(self) -> Dict[str, Any]:
        """
        Get domain rules for SAP logic.
        
        Returns:
            Dictionary of domain rules (composite key, design change logic, etc.)
        """
        return self.sap_schema.get_domain_rules()
    
    def validate_field_in_schema(self, field_name: str) -> bool:
        """
        Validate if a field is in the SAP schema.
        
        Args:
            field_name: Field name to validate
            
        Returns:
            True if field is valid, False otherwise
        """
        return self.sap_schema.validate_field(field_name)
    
    def validate_composite_key(self, record: Dict[str, Any]) -> bool:
        """
        Validate that a record has a valid composite key.
        
        Args:
            record: Record to validate
            
        Returns:
            True if composite key is valid, False otherwise
        """
        return self.sap_schema.validate_composite_key(record)
    
    def extract_scoped_records(
        self,
        detail_records: List[Dict[str, Any]],
        scope_type: str,
        scope_value: str
    ) -> List[Dict[str, Any]]:
        """
        Extract records matching a specific scope.
        
        Args:
            detail_records: All detail records
            scope_type: Type of scope (location, supplier, material_group, etc.)
            scope_value: Value to filter by
            
        Returns:
            Filtered list of records matching the scope
        """
        if scope_type == "location":
            return [r for r in detail_records if r.get("LOCID") == scope_value]
        elif scope_type == "supplier":
            return [r for r in detail_records if r.get("LOCFR") == scope_value]
        elif scope_type == "material_group":
            return [r for r in detail_records if r.get("GSCEQUIPCAT") == scope_value]
        elif scope_type == "material_id":
            return [r for r in detail_records if r.get("PRDID") == scope_value]
        elif scope_type == "risk_type":
            return [r for r in detail_records if r.get("Risk_Flag") == (scope_value == "high")]
        else:
            return detail_records
    
    def compute_scoped_metrics(
        self,
        scoped_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute metrics for scoped records.
        
        Args:
            scoped_records: Records filtered to a specific scope
            
        Returns:
            Dictionary with computed metrics for the scope
        """
        if not scoped_records:
            return {
                "filteredRecordsCount": 0,
                "changedCount": 0,
                "changeRate": 0.0,
                "scopedContributionBreakdown": {},
                "scopedDrivers": {},
                "topContributingRecords": []
            }
        
        # Count changed records
        changed_count = sum(1 for r in scoped_records if r.get("changed", False))
        total_count = len(scoped_records)
        change_rate = round(changed_count / max(total_count, 1) * 100, 1)
        
        # Compute contribution breakdown
        qty_changed = sum(1 for r in scoped_records if r.get("qtyChanged", False))
        supplier_changed = sum(1 for r in scoped_records if r.get("supplierChanged", False))
        design_changed = sum(1 for r in scoped_records if r.get("designChanged", False))
        schedule_changed = sum(1 for r in scoped_records if r.get("scheduleChanged", False))
        
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
            scoped_records,
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
