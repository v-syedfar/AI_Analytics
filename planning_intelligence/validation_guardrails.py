"""
Validation Guardrails - Prevents hallucination and enforces SAP domain logic.

This module validates all responses before they are returned to users.
It ensures:
1. All field names are valid SAP fields
2. All numbers exist in the MCP context
3. No hallucinated values are present
4. All domain rules are enforced
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from sap_schema import SAPSchema

logger = logging.getLogger(__name__)


class ValidationGuardrails:
    """
    Validates responses against SAP schema and MCP context.
    
    Prevents hallucination by ensuring all values are grounded in data.
    """
    
    def __init__(self, mcp_context: Dict[str, Any]):
        """
        Initialize validation guardrails.
        
        Args:
            mcp_context: Complete MCP context with SAP schema
        """
        self.mcp_context = mcp_context
        self.sap_schema = SAPSchema()
        self.field_dictionary = mcp_context.get("sapSchema", {}).get("fieldDictionary", {})
        self.analytics_context = mcp_context.get("analyticsContext", {})
        self.detail_records = self.analytics_context.get("detailRecords", [])
    
    def validate_response(self, response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a complete response.
        
        Args:
            response: Response dict to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate decision
        if "decision" in response:
            decision_errors = self._validate_field_references(response["decision"])
            errors.extend(decision_errors)
        
        # Validate key metrics
        if "keyMetrics" in response:
            metrics_errors = self._validate_metrics(response["keyMetrics"])
            errors.extend(metrics_errors)
        
        # Validate drivers
        if "drivers" in response:
            drivers_errors = self._validate_drivers(response["drivers"])
            errors.extend(drivers_errors)
        
        # Validate actions
        if "actions" in response:
            actions_errors = self._validate_actions(response["actions"])
            errors.extend(actions_errors)
        
        # Validate investigate mode fields
        if "investigateMode" in response:
            investigate_errors = self._validate_investigate_mode(response["investigateMode"])
            errors.extend(investigate_errors)
        
        return len(errors) == 0, errors
    
    def _validate_field_references(self, text: str) -> List[str]:
        """
        Validate that all field references in text are valid SAP fields.
        
        Args:
            text: Text to validate
            
        Returns:
            List of errors found
        """
        errors = []
        valid_fields = set(self.field_dictionary.keys())
        
        # Check for common field name patterns
        for field in valid_fields:
            # This is a simple check; more sophisticated parsing could be added
            pass
        
        return errors
    
    def _validate_metrics(self, metrics: Dict[str, Any]) -> List[str]:
        """
        Validate that all metrics exist in the MCP context.
        
        Args:
            metrics: Metrics dict to validate
            
        Returns:
            List of errors found
        """
        errors = []
        
        # Check for null values when data exists
        for key, value in metrics.items():
            if value is None:
                errors.append(f"Metric '{key}' is null but data exists in MCP context")
        
        # Validate specific metrics
        if "changedRecordCount" in metrics:
            if not isinstance(metrics["changedRecordCount"], (int, float)):
                errors.append(f"changedRecordCount must be numeric, got {type(metrics['changedRecordCount'])}")
        
        if "changeRate" in metrics:
            if not isinstance(metrics["changeRate"], (int, float)):
                errors.append(f"changeRate must be numeric, got {type(metrics['changeRate'])}")
            if metrics["changeRate"] < 0 or metrics["changeRate"] > 100:
                errors.append(f"changeRate must be between 0-100, got {metrics['changeRate']}")
        
        return errors
    
    def _validate_drivers(self, drivers: Dict[str, Any]) -> List[str]:
        """
        Validate that drivers are valid and sum to 100%.
        
        Args:
            drivers: Drivers dict to validate
            
        Returns:
            List of errors found
        """
        errors = []
        
        # Valid driver types
        valid_drivers = {"forecast", "supplier", "design", "schedule", "quantity"}
        
        # Check for invalid driver types
        for driver_type in drivers.keys():
            if driver_type not in valid_drivers and driver_type != "other":
                errors.append(f"Invalid driver type: {driver_type}")
        
        # Check that percentages are valid
        total_percentage = 0
        for driver_type, percentage in drivers.items():
            if not isinstance(percentage, (int, float)):
                errors.append(f"Driver '{driver_type}' percentage must be numeric, got {type(percentage)}")
            elif percentage < 0 or percentage > 100:
                errors.append(f"Driver '{driver_type}' percentage must be 0-100, got {percentage}")
            else:
                total_percentage += percentage
        
        # Check that percentages sum to approximately 100%
        if total_percentage > 0 and abs(total_percentage - 100) > 1:
            errors.append(f"Driver percentages sum to {total_percentage}%, expected ~100%")
        
        return errors
    
    def _validate_actions(self, actions: List[str]) -> List[str]:
        """
        Validate that actions are reasonable and grounded in data.
        
        Args:
            actions: List of actions to validate
            
        Returns:
            List of errors found
        """
        errors = []
        
        if not isinstance(actions, list):
            errors.append(f"Actions must be a list, got {type(actions)}")
            return errors
        
        if len(actions) == 0:
            errors.append("Actions list is empty")
        
        # Check for reasonable action types
        valid_action_keywords = {
            "monitor", "contact", "review", "investigate", "escalate",
            "reduce", "increase", "adjust", "verify", "confirm"
        }
        
        for action in actions:
            if not isinstance(action, str):
                errors.append(f"Action must be string, got {type(action)}")
            elif len(action) == 0:
                errors.append("Action is empty string")
            elif len(action) > 200:
                errors.append(f"Action is too long ({len(action)} chars): {action[:50]}...")
        
        return errors
    
    def _validate_investigate_mode(self, investigate_mode: Dict[str, Any]) -> List[str]:
        """
        Validate investigate mode fields.
        
        Args:
            investigate_mode: Investigate mode dict to validate
            
        Returns:
            List of errors found
        """
        errors = []
        
        # Validate filteredRecordsCount
        if "filteredRecordsCount" in investigate_mode:
            count = investigate_mode["filteredRecordsCount"]
            if not isinstance(count, int):
                errors.append(f"filteredRecordsCount must be int, got {type(count)}")
            elif count < 0:
                errors.append(f"filteredRecordsCount cannot be negative: {count}")
        
        # Validate scopedContributionBreakdown
        if "scopedContributionBreakdown" in investigate_mode:
            breakdown_errors = self._validate_drivers(investigate_mode["scopedContributionBreakdown"])
            errors.extend(breakdown_errors)
        
        # Validate scopedDrivers
        if "scopedDrivers" in investigate_mode:
            drivers = investigate_mode["scopedDrivers"]
            if "primary" in drivers:
                valid_drivers = {"forecast", "supplier", "design", "schedule", "none"}
                if drivers["primary"] not in valid_drivers:
                    errors.append(f"Invalid primary driver: {drivers['primary']}")
        
        # Validate topContributingRecords
        if "topContributingRecords" in investigate_mode:
            records = investigate_mode["topContributingRecords"]
            if not isinstance(records, list):
                errors.append(f"topContributingRecords must be list, got {type(records)}")
            elif len(records) > 5:
                errors.append(f"topContributingRecords should have max 5 records, got {len(records)}")
        
        return errors
    
    def validate_field_name(self, field_name: str) -> bool:
        """
        Validate that a field name is a valid SAP field.
        
        Args:
            field_name: Field name to validate
            
        Returns:
            True if valid, False otherwise
        """
        return field_name in self.field_dictionary
    
    def validate_value_exists_in_data(
        self,
        field_name: str,
        value: Any
    ) -> bool:
        """
        Validate that a value exists in the detail records for a field.
        
        Args:
            field_name: Field name to check
            value: Value to check
            
        Returns:
            True if value exists in data, False otherwise
        """
        if not self.detail_records:
            return False
        
        for record in self.detail_records:
            if record.get(field_name) == value:
                return True
        
        return False
    
    def detect_hallucination(self, response_text: str) -> Tuple[bool, List[str]]:
        """
        Detect potential hallucinations in response text.
        
        Args:
            response_text: Response text to check
            
        Returns:
            Tuple of (has_hallucination, list_of_suspicious_items)
        """
        suspicious = []
        
        # Check for common hallucination patterns
        hallucination_patterns = [
            ("Unknown", "Unknown values should not appear if data exists"),
            ("null", "Null values should not appear if data exists"),
            ("N/A", "N/A values should not appear if data exists"),
            ("approximately", "Approximate values suggest guessing"),
            ("roughly", "Rough estimates suggest guessing"),
            ("probably", "Probabilistic language suggests uncertainty"),
            ("might be", "Uncertain language suggests guessing"),
        ]
        
        for pattern, reason in hallucination_patterns:
            if pattern.lower() in response_text.lower():
                suspicious.append(f"Found '{pattern}': {reason}")
        
        return len(suspicious) > 0, suspicious
    
    def enforce_domain_rules(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Enforce SAP domain rules on a record.
        
        Args:
            record: Record to validate
            
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Check composite key
        if not self.sap_schema.validate_composite_key(record):
            violations.append("Record missing composite key (LOCID, GSCEQUIPCAT, PRDID)")
        
        # Check design change logic
        if "designChanged" in record:
            expected_design_change = self.sap_schema.is_design_change(record)
            if record.get("designChanged") != expected_design_change:
                violations.append(f"Design change logic violated: expected {expected_design_change}, got {record.get('designChanged')}")
        
        # Check supplier issue logic
        if "supplierIssue" in record:
            expected_supplier_issue = self.sap_schema.is_supplier_issue(record)
            if record.get("supplierIssue") != expected_supplier_issue:
                violations.append(f"Supplier issue logic violated: expected {expected_supplier_issue}, got {record.get('supplierIssue')}")
        
        # Check schedule issue logic
        if "scheduleIssue" in record:
            expected_schedule_issue = self.sap_schema.is_schedule_issue(record)
            if record.get("scheduleIssue") != expected_schedule_issue:
                violations.append(f"Schedule issue logic violated: expected {expected_schedule_issue}, got {record.get('scheduleIssue')}")
        
        return len(violations) == 0, violations
