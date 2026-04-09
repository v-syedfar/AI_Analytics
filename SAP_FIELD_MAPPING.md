# SAP Field Mapping & Integration Guide

## Complete SAP Field Dictionary

This document provides the complete mapping of all SAP fields used in the Planning Intelligence System for data extraction and analysis from Blob Storage files.

### Field Categories

---

## 1. Location & Facility Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| ZCOILLEPLANINDZCO | Location ID | String | Unique identifier for location/facility | LOC001 |
| LOCFR | Supplier From | String | Source supplier identifier | SUP001 |
| LOCFRDESCR | Supplier Description | String | Description of supplier | "Supplier A" |
| ZCOIFORMFACTZ | Form Factor | String | Facility form factor | "DC" |
| ZCOIBODVERZ | BOD Version | String | Bill of Distribution version | "1.0" |
| ZCOIMETROIDZ | Metro ID | String | Metropolitan area identifier | "NYC" |
| ZCOICOUNTRY | Country | String | Country code | "US" |

---

## 2. Material & Product Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| PRDID | Material ID | String | Unique product/material identifier | MAT001 |
| GSCEQUIPCAT | Equipment Category | String | Material group (UPS, PUMP, VALVE) | "UPS" |
| ZCOICIDZ | Component ID | String | Component identifier | "COMP001" |
| ZCOIBODVERZ | BOD Version | String | Bill of Distribution version | "1.0" |

---

## 3. Forecast Quantity Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| GSCPREVFCSTQTY | Previous Forecast Quantity | Number | Forecast from previous cycle | 1000 |
| GSCFSCTQTY | Current Forecast Quantity | Number | Current forecast quantity | 1200 |
| FCST_Delta Qty | Forecast Delta Quantity | Number | Change in forecast (current - previous) | 200 |
| GSCFCSTTOSCPZ | Send Forecast to SCP | Boolean | Flag to send forecast to SCP | true |
| GSCFCSTAPPROVALSCP | Forecast Approval | String | Approval status | "APPROVED" |

---

## 4. ROJ (Required On-hand by Date) Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| GSCPREVROJNBD | Previous ROJ Need-By Date | Date | Previous ROJ date | 2026-04-15 |
| GSCCONROJDATE | Current ROJ Need-By Date | Date | Current ROJ date | 2026-04-20 |
| GSCROJDATEZ | ROJ Date | Date | ROJ date | 2026-04-20 |
| GSCROJDATEREASONCODEZ | ROJ Date Reason Code | String | Reason for ROJ change | "DEMAND_CHANGE" |
| GSCROJNBDLASTCHANGEDDATE | ROJ Last Changed Date | Date | Last modification date | 2026-04-09 |
| GSCROJNBDCREATIONDATE | ROJ Creation Date | Date | Creation date | 2026-04-01 |
| NBD_Change Type | ROJ Change Type | String | Type of change | "SHIFT" |
| NBD_DeltaDays | ROJ Shift (Days) | Number | Change in days | 5 |

---

## 5. Supplier Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| LOCFR | Supplier From | String | Source supplier | SUP001 |
| GSCPREVSUPLDATEZ | Previous Supplier Date | Date | Previous supplier date | 2026-04-10 |
| GSCSUPLDATEZ | Current Supplier Date | Date | Current supplier date | 2026-04-12 |
| GSCSCPROJDATEZ | SCP ROJ Date | Date | SCP ROJ date | 2026-04-20 |
| GSCSCPROJINDZ | SCP ROJ Indicator | String | SCP ROJ indicator | "Y" |
| GSCSCPSUPCMT | SCP Supplier Comment | String | Supplier comment | "On track" |
| GSCSENDFCSTSCPFIRSTPUBLISHDATE | Send Forecast First Publish Date | Date | First publish date | 2026-04-01 |
| GSCTRACKLASTPUBLISHDATEZ | Track Last Publish Date | Date | Last publish date | 2026-04-09 |
| GSCSENDFCSTSCPLASTREMOVEDATE | Send Forecast Last Removed Date | Date | Last removed date | 2026-04-08 |
| GSCSENDFCSTSCPLASTCHANGEDDATE | Send Forecast Last Changed Date | Date | Last changed date | 2026-04-09 |

---

## 6. Planning & Exception Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| GSCCONSUMEINVFLG | Consume Inventory Flag | Boolean | Flag to consume inventory | true |
| GSCLLEPLANNING | LLE Planning Needed | Boolean | Low-level engineering planning needed | false |
| GSCPLANNINGEXCEPTIONZ | Planning Exception | String | Planning exception code | "NONE" |
| GSCPLANNINGMETRO | Planning Metro | String | Planning metro area | "NYC" |
| GSCPLNRVWNOTES | Planner Review Notes | String | Planner notes | "Reviewed and approved" |

---

## 7. Approval & Workflow Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| GSCFCSTAPPROVALSCP | Forecast Approval | String | Approval status | "APPROVED" |
| GSCCMAPPROVALFIRSTDATE | CM Approval First Date | Date | First approval date | 2026-04-01 |
| GSCCMAPPROVALLASTCHANGEDDATE | CM Approval Last Changed Date | Date | Last approval change | 2026-04-09 |
| GSCCMAPPROVALLASTCHANGEDVALUE | CM Approval Last Changed Value | String | Last approval value | "APPROVED" |
| TINVALID | Invalid Flag | Boolean | Record invalid flag | false |

---

## 8. Change Tracking Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| LASTMODIFIEDBY | Last Modified By | String | User who last modified | "USER001" |
| LASTMODIFIEDDATE | Last Modified Date | Date | Last modification date | 2026-04-09 |
| CREATEDBY | Created By | String | User who created record | "USER001" |
| CREATEDDATE | Created Date | Date | Creation date | 2026-04-01 |
| #Version | Version | Number | Record version | 1 |

---

## 9. Data Quality & Validation Fields

| SAP Code | Field Name | Type | Description | Example |
|----------|-----------|------|-------------|---------|
| GSCAUTOMATIONREASONZ | Automation Reason | String | Reason for automation | "AUTO_PROCESS" |
| GSCMSFTCMTZ | Microsoft Comment | String | Microsoft comment | "Processed" |
| GSCDATASTEWARDNOTES | Data Steward Notes | String | Data steward notes | "Verified" |
| GSCROJDATEREASONCODEZ | ROJ Date Reason Code | String | Reason for ROJ change | "DEMAND_CHANGE" |
| ZCOIFORMFACTORZ | Form Factor | String | Form factor | "DC" |

---

## 10. Computed/Derived Fields

| Field Name | Type | Description | Calculation |
|-----------|------|-------------|-------------|
| qtyChanged | Boolean | Quantity changed | GSCFSCTQTY != GSCPREVFCSTQTY |
| supplierChanged | Boolean | Supplier changed | LOCFR != LOCFR_previous |
| designChanged | Boolean | Design changed | ZCOIBODVERZ != ZCOIBODVERZ_previous |
| scheduleChanged | Boolean | Schedule changed | GSCCONROJDATE != GSCPREVROJNBD |
| changed | Boolean | Any change occurred | qtyChanged OR supplierChanged OR designChanged OR scheduleChanged |
| qtyDelta | Number | Quantity change amount | GSCFSCTQTY - GSCPREVFCSTQTY |
| forecastDelta | Number | Total forecast change | SUM(qtyDelta) |
| Risk_Flag | Boolean | Risk indicator | changed AND (qtyDelta > threshold OR scheduleChanged) |

---

## Data Extraction from Blob Storage

### File Format
- **Format:** CSV or Excel
- **Encoding:** UTF-8
- **Delimiter:** Comma (,) or Tab
- **Headers:** First row contains field names

### Extraction Process

```python
# 1. Read file from Blob Storage
blob_data = read_blob_file(blob_path)

# 2. Parse CSV/Excel
records = parse_data(blob_data)

# 3. Map SAP fields
for record in records:
    mapped_record = {
        'LOCID': record['ZCOILLEPLANINDZCO'],
        'PRDID': record['PRDID'],
        'GSCEQUIPCAT': record['GSCEQUIPCAT'],
        'LOCFR': record['LOCFR'],
        'GSCPREVFCSTQTY': float(record['GSCPREVFCSTQTY']),
        'GSCFSCTQTY': float(record['GSCFSCTQTY']),
        'GSCPREVROJNBD': parse_date(record['GSCPREVROJNBD']),
        'GSCCONROJDATE': parse_date(record['GSCCONROJDATE']),
        'GSCPREVSUPLDATEZ': parse_date(record['GSCPREVSUPLDATEZ']),
        'GSCSUPLDATEZ': parse_date(record['GSCSUPLDATEZ']),
        # ... other fields
    }
    
    # 4. Compute derived fields
    mapped_record['qtyChanged'] = (
        mapped_record['GSCFSCTQTY'] != mapped_record['GSCPREVFCSTQTY']
    )
    mapped_record['qtyDelta'] = (
        mapped_record['GSCFSCTQTY'] - mapped_record['GSCPREVFCSTQTY']
    )
    mapped_record['changed'] = (
        mapped_record['qtyChanged'] or 
        mapped_record['supplierChanged'] or
        mapped_record['designChanged'] or
        mapped_record['scheduleChanged']
    )
    
    # 5. Validate record
    if validate_record(mapped_record):
        processed_records.append(mapped_record)
```

---

## Validation Rules

### Composite Key Validation
- **Primary Key:** LOCID + PRDID + GSCEQUIPCAT + LOCFR
- **Requirement:** Must be unique per record
- **Action:** Reject duplicate keys

### Field Type Validation
- **Numeric Fields:** Must be valid numbers
- **Date Fields:** Must be valid dates (YYYY-MM-DD)
- **String Fields:** Must not be null
- **Boolean Fields:** Must be true/false or Y/N

### Business Logic Validation
- **Forecast Change:** GSCFSCTQTY must be >= 0
- **ROJ Date:** GSCCONROJDATE must be >= today
- **Supplier Date:** GSCSUPLDATEZ must be valid
- **Version:** #Version must be numeric

---

## Risk Calculation Logic

### Risk Flag Determination
```python
def calculate_risk_flag(record):
    """
    Determine if record is risky based on changes and thresholds.
    """
    # Quantity change threshold (e.g., 10% or 100 units)
    qty_threshold = max(
        record['GSCPREVFCSTQTY'] * 0.10,  # 10% of previous
        100  # or 100 units minimum
    )
    
    # Schedule change threshold (e.g., 5 days)
    schedule_threshold = 5
    
    # Risk factors
    qty_risk = abs(record['qtyDelta']) > qty_threshold
    schedule_risk = abs(record['NBD_DeltaDays']) > schedule_threshold
    supplier_risk = record['supplierChanged']
    design_risk = record['designChanged']
    
    # Overall risk
    risk_flag = qty_risk or schedule_risk or supplier_risk or design_risk
    
    return {
        'Risk_Flag': risk_flag,
        'qty_risk': qty_risk,
        'schedule_risk': schedule_risk,
        'supplier_risk': supplier_risk,
        'design_risk': design_risk,
        'primary_driver': determine_primary_driver({
            'quantity': qty_risk,
            'schedule': schedule_risk,
            'supplier': supplier_risk,
            'design': design_risk
        })
    }
```

---

## Integration with Planning Intelligence System

### Data Flow
```
Blob Storage File
    ↓
Extract & Parse
    ↓
Map SAP Fields
    ↓
Compute Derived Fields
    ↓
Validate Records
    ↓
Calculate Risk Flags
    ↓
Store in Memory/Database
    ↓
Query Processing
    ↓
Analysis & Response
```

### Query Processing with SAP Data
```
User Query: "Why is LOC001 risky?"
    ↓
Phase 1: Extract scope (LOCID = LOC001)
    ↓
Phase 2: Filter records by LOCID
    ↓
Phase 3: Compute metrics
    - Count changed records
    - Calculate change rate
    - Identify primary driver
    - Compute contribution breakdown
    ↓
Phase 4: Generate response
    - "Risk Analysis for LOC001"
    - "2 out of 3 records changed (66.7%)"
    - "Primary driver: quantity changes"
```

---

## Performance Considerations

### Indexing Strategy
- **Primary Index:** LOCID + PRDID (for fast filtering)
- **Secondary Index:** LOCFR (for supplier queries)
- **Tertiary Index:** GSCEQUIPCAT (for material group queries)

### Caching Strategy
- **Cache Level 1:** Frequently accessed locations (LOC001, LOC002, etc.)
- **Cache Level 2:** Computed metrics (change rates, drivers)
- **Cache TTL:** 1 hour (configurable)

### Batch Processing
- **Batch Size:** 1,000 records
- **Processing Time:** < 1 second per batch
- **Total Time:** < 5 minutes for 1M records

---

## Error Handling

### Invalid Records
- **Missing Fields:** Log and skip
- **Invalid Types:** Log and skip
- **Duplicate Keys:** Log and use latest version
- **Validation Failures:** Log and skip

### Data Quality Issues
- **Null Values:** Replace with default or skip
- **Out-of-Range Values:** Log and flag
- **Inconsistent Dates:** Log and flag
- **Missing Relationships:** Log and flag

---

## Audit & Compliance

### Data Lineage
- Track source file and extraction date
- Track all transformations applied
- Track validation results
- Track risk calculations

### Audit Trail
- Log all data access
- Log all calculations
- Log all errors
- Log all changes

---

## Future Enhancements

1. **Real-time Data Sync:** Stream updates from SAP
2. **Advanced Analytics:** ML-based risk prediction
3. **Custom Metrics:** User-defined KPIs
4. **Data Governance:** Automated compliance checks
5. **Performance Optimization:** Distributed processing

---

**Document Version:** 1.0.0  
**Last Updated:** April 9, 2026  
**Status:** Production Ready ✅
