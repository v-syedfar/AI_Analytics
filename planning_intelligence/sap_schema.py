"""
SAP Schema Module - Defines SAP field dictionary, semantic mapping, and domain rules.

This module serves as the single source of truth for SAP domain logic.
All field names, semantic mappings, and domain rules are defined here.
"""


class SAPSchema:
    """
    Manages SAP field dictionary, semantic mapping, and domain rules.
    
    This is the foundation for validation guardrails and domain rule enforcement.
    """
    
    @staticmethod
    def get_field_dictionary() -> dict:
        """
        Return complete SAP field dictionary.
        
        All field names and their meanings are defined here.
        Used for validation and schema enforcement.
        
        Source: SAP IBP Planning Data Extract
        """
        return {
            # ===== LOCATION & FACILITY FIELDS =====
            "ZCOILLEPLANINDZCO": {
                "name": "Location ID",
                "type": "string",
                "description": "Unique identifier for location/facility",
                "example": "LOC001"
            },
            "LOCFR": {
                "name": "Supplier From",
                "type": "string",
                "description": "Source supplier identifier",
                "example": "SUP001"
            },
            "LOCFRDESCR": {
                "name": "Supplier Description",
                "type": "string",
                "description": "Description of supplier",
                "example": "Supplier A"
            },
            "ZCOIFORMFACTZ": {
                "name": "Form Factor",
                "type": "string",
                "description": "Facility form factor",
                "example": "DC"
            },
            "ZCOIBODVERZ": {
                "name": "BOD Version",
                "type": "string",
                "description": "Bill of Distribution version",
                "example": "1.0"
            },
            "ZCOIMETROIDZ": {
                "name": "Metro ID",
                "type": "string",
                "description": "Metropolitan area identifier",
                "example": "NYC"
            },
            "ZCOICOUNTRY": {
                "name": "Country",
                "type": "string",
                "description": "Country code",
                "example": "US"
            },
            
            # ===== MATERIAL & PRODUCT FIELDS =====
            "PRDID": {
                "name": "Material ID",
                "type": "string",
                "description": "Unique product/material identifier",
                "example": "MAT001"
            },
            "GSCEQUIPCAT": {
                "name": "Equipment Category",
                "type": "string",
                "description": "Material group (UPS, PUMP, VALVE)",
                "example": "UPS"
            },
            "ZCOICIDZ": {
                "name": "Component ID",
                "type": "string",
                "description": "Component identifier",
                "example": "COMP001"
            },
            
            # ===== FORECAST QUANTITY FIELDS =====
            "GSCPREVFCSTQTY": {
                "name": "Previous Forecast Quantity",
                "type": "number",
                "description": "Forecast from previous cycle",
                "example": 1000
            },
            "GSCFSCTQTY": {
                "name": "Current Forecast Quantity",
                "type": "number",
                "description": "Current forecast quantity",
                "example": 1200
            },
            "FCST_Delta Qty": {
                "name": "Forecast Delta Quantity",
                "type": "number",
                "description": "Change in forecast (current - previous)",
                "example": 200
            },
            "GSCFCSTTOSCPZ": {
                "name": "Send Forecast to SCP",
                "type": "boolean",
                "description": "Flag to send forecast to SCP",
                "example": True
            },
            "GSCFCSTAPPROVALSCP": {
                "name": "Forecast Approval",
                "type": "string",
                "description": "Approval status",
                "example": "APPROVED"
            },
            
            # ===== ROJ (REQUIRED ON-HAND BY DATE) FIELDS =====
            "GSCPREVROJNBD": {
                "name": "Previous ROJ Need-By Date",
                "type": "date",
                "description": "Previous ROJ date",
                "example": "2026-04-15"
            },
            "GSCCONROJDATE": {
                "name": "Current ROJ Need-By Date",
                "type": "date",
                "description": "Current ROJ date",
                "example": "2026-04-20"
            },
            "GSCROJDATEZ": {
                "name": "ROJ Date",
                "type": "date",
                "description": "ROJ date",
                "example": "2026-04-20"
            },
            "GSCROJDATEREASONCODEZ": {
                "name": "ROJ Date Reason Code",
                "type": "string",
                "description": "Reason for ROJ change",
                "example": "DEMAND_CHANGE"
            },
            "GSCROJNBDLASTCHANGEDDATE": {
                "name": "ROJ Last Changed Date",
                "type": "date",
                "description": "Last modification date",
                "example": "2026-04-09"
            },
            "GSCROJNBDCREATIONDATE": {
                "name": "ROJ Creation Date",
                "type": "date",
                "description": "Creation date",
                "example": "2026-04-01"
            },
            "NBD_Change Type": {
                "name": "ROJ Change Type",
                "type": "string",
                "description": "Type of change",
                "example": "SHIFT"
            },
            "NBD_DeltaDays": {
                "name": "ROJ Shift (Days)",
                "type": "number",
                "description": "Change in days",
                "example": 5
            },
            
            # ===== SUPPLIER FIELDS =====
            "GSCPREVSUPLDATEZ": {
                "name": "Previous Supplier Date",
                "type": "date",
                "description": "Previous supplier date",
                "example": "2026-04-10"
            },
            "GSCSUPLDATEZ": {
                "name": "Current Supplier Date",
                "type": "date",
                "description": "Current supplier date",
                "example": "2026-04-12"
            },
            "GSCSCPROJDATEZ": {
                "name": "SCP ROJ Date",
                "type": "date",
                "description": "SCP ROJ date",
                "example": "2026-04-20"
            },
            "GSCSCPROJINDZ": {
                "name": "SCP ROJ Indicator",
                "type": "string",
                "description": "SCP ROJ indicator",
                "example": "Y"
            },
            "GSCSCPSUPCMT": {
                "name": "SCP Supplier Comment",
                "type": "string",
                "description": "Supplier comment",
                "example": "On track"
            },
            "GSCSENDFCSTSCPFIRSTPUBLISHDATE": {
                "name": "Send Forecast First Publish Date",
                "type": "date",
                "description": "First publish date",
                "example": "2026-04-01"
            },
            "GSCTRACKLASTPUBLISHDATEZ": {
                "name": "Track Last Publish Date",
                "type": "date",
                "description": "Last publish date",
                "example": "2026-04-09"
            },
            "GSCSENDFCSTSCPLASTREMOVEDATE": {
                "name": "Send Forecast Last Removed Date",
                "type": "date",
                "description": "Last removed date",
                "example": "2026-04-08"
            },
            "GSCSENDFCSTSCPLASTCHANGEDDATE": {
                "name": "Send Forecast Last Changed Date",
                "type": "date",
                "description": "Last changed date",
                "example": "2026-04-09"
            },
            
            # ===== PLANNING & EXCEPTION FIELDS =====
            "GSCCONSUMEINVFLG": {
                "name": "Consume Inventory Flag",
                "type": "boolean",
                "description": "Flag to consume inventory",
                "example": True
            },
            "GSCLLEPLANNING": {
                "name": "LLE Planning Needed",
                "type": "boolean",
                "description": "Low-level engineering planning needed",
                "example": False
            },
            "GSCPLANNINGEXCEPTIONZ": {
                "name": "Planning Exception",
                "type": "string",
                "description": "Planning exception code",
                "example": "NONE"
            },
            "GSCPLANNINGMETRO": {
                "name": "Planning Metro",
                "type": "string",
                "description": "Planning metro area",
                "example": "NYC"
            },
            "GSCPLNRVWNOTES": {
                "name": "Planner Review Notes",
                "type": "string",
                "description": "Planner notes",
                "example": "Reviewed and approved"
            },
            
            # ===== APPROVAL & WORKFLOW FIELDS =====
            "GSCCMAPPROVALFIRSTDATE": {
                "name": "CM Approval First Date",
                "type": "date",
                "description": "First approval date",
                "example": "2026-04-01"
            },
            "GSCCMAPPROVALLASTCHANGEDDATE": {
                "name": "CM Approval Last Changed Date",
                "type": "date",
                "description": "Last approval change",
                "example": "2026-04-09"
            },
            "GSCCMAPPROVALLASTCHANGEDVALUE": {
                "name": "CM Approval Last Changed Value",
                "type": "string",
                "description": "Last approval value",
                "example": "APPROVED"
            },
            "TINVALID": {
                "name": "Invalid Flag",
                "type": "boolean",
                "description": "Record invalid flag",
                "example": False
            },
            
            # ===== CHANGE TRACKING FIELDS =====
            "LASTMODIFIEDBY": {
                "name": "Last Modified By",
                "type": "string",
                "description": "User who last modified",
                "example": "USER001"
            },
            "LASTMODIFIEDDATE": {
                "name": "Last Modified Date",
                "type": "date",
                "description": "Last modification date",
                "example": "2026-04-09"
            },
            "CREATEDBY": {
                "name": "Created By",
                "type": "string",
                "description": "User who created record",
                "example": "USER001"
            },
            "CREATEDDATE": {
                "name": "Created Date",
                "type": "date",
                "description": "Creation date",
                "example": "2026-04-01"
            },
            "#Version": {
                "name": "Version",
                "type": "number",
                "description": "Record version",
                "example": 1
            },
            
            # ===== DATA QUALITY & VALIDATION FIELDS =====
            "GSCAUTOMATIONREASONZ": {
                "name": "Automation Reason",
                "type": "string",
                "description": "Reason for automation",
                "example": "AUTO_PROCESS"
            },
            "GSCMSFTCMTZ": {
                "name": "Microsoft Comment",
                "type": "string",
                "description": "Microsoft comment",
                "example": "Processed"
            },
            "GSCDATASTEWARDNOTES": {
                "name": "Data Steward Notes",
                "type": "string",
                "description": "Data steward notes",
                "example": "Verified"
            },
            
            # ===== COMPUTED/DERIVED FIELDS =====
            "qtyChanged": {
                "name": "Quantity Changed",
                "type": "boolean",
                "description": "Quantity changed flag",
                "example": True
            },
            "supplierChanged": {
                "name": "Supplier Changed",
                "type": "boolean",
                "description": "Supplier changed flag",
                "example": False
            },
            "designChanged": {
                "name": "Design Changed",
                "type": "boolean",
                "description": "Design changed flag",
                "example": False
            },
            "scheduleChanged": {
                "name": "Schedule Changed",
                "type": "boolean",
                "description": "Schedule changed flag",
                "example": True
            },
            "changed": {
                "name": "Any Change",
                "type": "boolean",
                "description": "Any change occurred",
                "example": True
            },
            "qtyDelta": {
                "name": "Quantity Delta",
                "type": "number",
                "description": "Quantity change amount",
                "example": 200
            },
            "forecastDelta": {
                "name": "Forecast Delta",
                "type": "number",
                "description": "Total forecast change",
                "example": 450
            },
            "Risk_Flag": {
                "name": "Risk Flag",
                "type": "boolean",
                "description": "Risk indicator",
                "example": True
            },
            "Is_New Demand": {
                "name": "New Demand Flag",
                "type": "boolean",
                "description": "New demand flag",
                "example": False
            },
            "Is_cancelled": {
                "name": "Cancelled Flag",
                "type": "boolean",
                "description": "Cancelled flag",
                "example": False
            },
            "Is_SupplierDateMissing": {
                "name": "Supplier Date Missing",
                "type": "boolean",
                "description": "Supplier date missing flag",
                "example": False
            }
        }
    
    @staticmethod
    def get_semantic_mapping() -> dict:
        """
        Return semantic mapping for domain logic.
        
        Defines how to compute derived fields from base SAP fields.
        """
        return {
            "forecast_change": {
                "formula": "GSCFSCTQTY - GSCPREVFCSTQTY",
                "description": "Change in forecast quantity",
                "type": "number"
            },
            "design_change": {
                "formula": "ZCOIBODVER changed OR ZCOIFORMFACT changed",
                "description": "True if BOD version or form factor changed",
                "type": "boolean",
                "exclude": ["Is_New Demand", "Is_cancelled"]
            },
            "supplier_issue": {
                "formula": "GSCSUPLDATE changed OR Is_SupplierDateMissing",
                "description": "True if supplier date changed or is missing",
                "type": "boolean"
            },
            "schedule_issue": {
                "formula": "NBD_DeltaDays > 0",
                "description": "True if ROJ need-by date shifted later",
                "type": "boolean"
            }
        }
    
    @staticmethod
    def get_domain_rules() -> dict:
        """
        Return domain rules for SAP logic.
        
        Defines strict rules for data validation and computation.
        """
        return {
            "composite_key": {
                "fields": ["LOCID", "GSCEQUIPCAT", "PRDID"],
                "description": "Unique identifier for a record is (LOCID, GSCEQUIPCAT, PRDID)"
            },
            "design_change_logic": {
                "TRUE_IF": [
                    "ZCOIBODVER changed",
                    "ZCOIFORMFACT changed"
                ],
                "EXCLUDE": [
                    "Is_New Demand == True",
                    "Is_cancelled == True"
                ],
                "description": "Design change is TRUE only if BOD or form factor changed, excluding new demand and cancelled"
            },
            "supplier_grouping": {
                "field": "LOCFR",
                "description": "Supplier grouping is by LOCFR field"
            },
            "risk_determination": {
                "factors": [
                    "forecast_change > threshold",
                    "design_change == True",
                    "supplier_issue == True",
                    "schedule_issue == True"
                ],
                "description": "Risk is determined by multiple factors"
            }
        }
    
    @staticmethod
    def validate_field(field_name: str) -> bool:
        """
        Validate if a field name is a valid SAP field.
        
        Args:
            field_name: Field name to validate
            
        Returns:
            True if field is valid, False otherwise
        """
        field_dict = SAPSchema.get_field_dictionary()
        return field_name in field_dict
    
    @staticmethod
    def get_field_info(field_name: str) -> dict:
        """
        Get information about a specific field.
        
        Args:
            field_name: Field name to get info for
            
        Returns:
            Field information dict, or empty dict if field not found
        """
        field_dict = SAPSchema.get_field_dictionary()
        return field_dict.get(field_name, {})
    
    @staticmethod
    def validate_composite_key(record: dict) -> bool:
        """
        Validate that a record has a valid composite key.
        
        Args:
            record: Record to validate
            
        Returns:
            True if composite key is valid, False otherwise
        """
        required_fields = ["LOCID", "GSCEQUIPCAT", "PRDID"]
        return all(field in record and record[field] is not None for field in required_fields)
    
    @staticmethod
    def is_design_change(record: dict) -> bool:
        """
        Determine if a record represents a design change.
        
        Follows strict domain rules:
        - TRUE only if BOD version OR form factor changed
        - EXCLUDE new demand and cancelled records
        
        Args:
            record: Record to check
            
        Returns:
            True if design change, False otherwise
        """
        # Exclude new demand and cancelled
        if record.get("Is_New Demand") or record.get("Is_cancelled"):
            return False
        
        # Check if BOD or form factor changed
        bod_changed = record.get("ZCOIBODVER_changed", False)
        form_factor_changed = record.get("ZCOIFORMFACT_changed", False)
        
        return bod_changed or form_factor_changed
    
    @staticmethod
    def is_supplier_issue(record: dict) -> bool:
        """
        Determine if a record represents a supplier issue.
        
        Args:
            record: Record to check
            
        Returns:
            True if supplier issue, False otherwise
        """
        supplier_date_changed = record.get("GSCSUPLDATE_changed", False)
        supplier_date_missing = record.get("Is_SupplierDateMissing", False)
        
        return supplier_date_changed or supplier_date_missing
    
    @staticmethod
    def is_schedule_issue(record: dict) -> bool:
        """
        Determine if a record represents a schedule issue.
        
        Args:
            record: Record to check
            
        Returns:
            True if schedule issue, False otherwise
        """
        nbd_delta = record.get("NBD_DeltaDays", 0)
        return nbd_delta > 0
