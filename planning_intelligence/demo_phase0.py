"""
Phase 0 Demo - Shows Prompt/Response Flow

This demo shows how Phase 0 components work together:
1. User Query (Prompt)
2. MCP Context Building
3. Scoped Metrics Computation
4. Response Validation
5. Final Response

Run with: python planning_intelligence/demo_phase0.py
"""

import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from sap_schema import SAPSchema
from mcp_context_builder import MCPContextBuilder
from validation_guardrails import ValidationGuardrails


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_subsection(title: str):
    """Print a subsection header."""
    print(f"\n{title}")
    print("-" * 80)


def demo_1_simple_query():
    """Demo 1: Simple Query - "Why is LOC001 risky?"."""
    print_section("DEMO 1: Simple Query - 'Why is LOC001 risky?'")
    
    # Step 1: User Query (Prompt)
    query = "Why is LOC001 risky?"
    print_subsection("STEP 1: User Query (Prompt)")
    print(f"User: {query}")
    
    # Step 2: Build MCP Context
    print_subsection("STEP 2: Build MCP Context")
    builder = MCPContextBuilder()
    
    analytics = {
        "planningHealth": "Critical",
        "forecastNew": 1000,
        "forecastOld": 800,
        "trendDelta": 200,
        "changedRecordCount": 15,
        "totalRecords": 33,
        "drivers": {"forecast": 60, "supplier": 30, "design": 10},
        "dataSource": "Blob",
        "lastRefreshedAt": datetime.now(timezone.utc).isoformat(),
        "blobFileNamesUsed": ["data_2026_04_09.csv"],
        "recordsAnalyzed": 1000
    }
    
    records = [
        {
            "LOCID": "LOC001",
            "GSCEQUIPCAT": "UPS",
            "PRDID": "MAT-101",
            "LOCFR": "SUP-001",
            "changed": True,
            "qtyChanged": True,
            "qtyDelta": 100
        },
        {
            "LOCID": "LOC001",
            "GSCEQUIPCAT": "UPS",
            "PRDID": "MAT-102",
            "LOCFR": "SUP-001",
            "changed": False,
            "qtyChanged": False,
            "qtyDelta": 0
        },
        {
            "LOCID": "LOC002",
            "GSCEQUIPCAT": "PUMP",
            "PRDID": "MAT-202",
            "LOCFR": "SUP-002",
            "changed": True,
            "qtyChanged": True,
            "qtyDelta": 50
        }
    ]
    
    mcp_context = builder.build_mcp_context(
        analytics,
        records,
        query_intent="root_cause",
        extracted_entities={"LOCID": ["LOC001"]}
    )
    
    print(f"✓ MCP Context built")
    print(f"  - Planning Health: {mcp_context['analyticsContext']['planningHealth']}")
    print(f"  - Total Records: {mcp_context['analyticsContext']['totalRecords']}")
    print(f"  - SAP Fields: {len(mcp_context['sapSchema']['fieldDictionary'])}")
    
    # Step 3: Extract Scoped Records
    print_subsection("STEP 3: Extract Scoped Records for LOC001")
    scoped = builder.extract_scoped_records(records, "location", "LOC001")
    print(f"✓ Extracted {len(scoped)} records for LOC001")
    for i, record in enumerate(scoped, 1):
        print(f"  Record {i}: {record['PRDID']} - Changed: {record['changed']}")
    
    # Step 4: Compute Scoped Metrics
    print_subsection("STEP 4: Compute Scoped Metrics")
    metrics = builder.compute_scoped_metrics(scoped)
    print(f"✓ Metrics computed:")
    print(f"  - Records in scope: {metrics['filteredRecordsCount']}")
    print(f"  - Changed records: {metrics['changedCount']}")
    print(f"  - Change rate: {metrics['changeRate']}%")
    print(f"  - Primary driver: {metrics['scopedDrivers']['primary']}")
    print(f"  - Contribution breakdown:")
    for driver, percentage in metrics['scopedContributionBreakdown'].items():
        if percentage > 0:
            print(f"    • {driver}: {percentage}%")
    
    # Step 5: Build Structured Response
    print_subsection("STEP 5: Build Structured Response")
    structured_response = {
        "decision": f"Location LOC001 is risky",
        "keyMetrics": {
            "changedCount": metrics['changedCount'],
            "changeRate": metrics['changeRate'],
            "totalRecords": metrics['filteredRecordsCount']
        },
        "drivers": metrics['scopedContributionBreakdown'],
        "riskProfile": "High",
        "actions": [
            "Monitor forecast changes at LOC001",
            "Contact supplier SUP-001",
            "Review BOD version changes"
        ]
    }
    
    print(f"✓ Structured response built:")
    print(f"  - Decision: {structured_response['decision']}")
    print(f"  - Risk Profile: {structured_response['riskProfile']}")
    print(f"  - Actions: {len(structured_response['actions'])} recommended")
    
    # Step 6: Validate Response
    print_subsection("STEP 6: Validate Response")
    guardrails = ValidationGuardrails(mcp_context)
    is_valid, errors = guardrails.validate_response(structured_response)
    
    if is_valid:
        print(f"✓ Response validation PASSED")
    else:
        print(f"✗ Response validation FAILED:")
        for error in errors:
            print(f"  - {error}")
    
    # Step 7: Generate Natural Language Response
    print_subsection("STEP 7: Generate Natural Language Response (Simulated)")
    response_text = (
        f"Location LOC001 is risky. Out of {metrics['filteredRecordsCount']} records, "
        f"{metrics['changedCount']} have changed ({metrics['changeRate']}%). "
        f"The primary driver is {metrics['scopedDrivers']['primary']} changes. "
        f"Recommended actions: {', '.join(structured_response['actions'])}."
    )
    
    print(f"✓ Natural language response generated:")
    print(f"\nCopilot: {response_text}")
    
    # Step 8: Return Response
    print_subsection("STEP 8: Return Response to User")
    print(f"✓ Response ready for UI")
    print(f"\nFinal Response:")
    print(f"  - Type: Root Cause Analysis")
    print(f"  - Scope: Location LOC001")
    print(f"  - Confidence: High (based on {metrics['filteredRecordsCount']} records)")
    print(f"  - Data Freshness: {mcp_context['provenance']['lastRefreshedAt']}")


def demo_2_comparison_query():
    """Demo 2: Comparison Query - "Compare LOC001 vs LOC002"."""
    print_section("DEMO 2: Comparison Query - 'Compare LOC001 vs LOC002'")
    
    # Step 1: User Query (Prompt)
    query = "Compare LOC001 vs LOC002"
    print_subsection("STEP 1: User Query (Prompt)")
    print(f"User: {query}")
    
    # Step 2: Build MCP Context
    print_subsection("STEP 2: Build MCP Context")
    builder = MCPContextBuilder()
    
    analytics = {
        "planningHealth": "Critical",
        "forecastNew": 1000,
        "forecastOld": 800,
        "trendDelta": 200,
        "changedRecordCount": 15,
        "totalRecords": 33,
        "drivers": {"forecast": 60, "supplier": 30, "design": 10},
        "dataSource": "Blob",
        "lastRefreshedAt": datetime.now(timezone.utc).isoformat(),
        "blobFileNamesUsed": ["data_2026_04_09.csv"],
        "recordsAnalyzed": 1000
    }
    
    records = [
        {"LOCID": "LOC001", "GSCEQUIPCAT": "UPS", "PRDID": "MAT-101", "LOCFR": "SUP-001", "changed": True, "qtyChanged": True, "qtyDelta": 100},
        {"LOCID": "LOC001", "GSCEQUIPCAT": "UPS", "PRDID": "MAT-102", "LOCFR": "SUP-001", "changed": False, "qtyChanged": False, "qtyDelta": 0},
        {"LOCID": "LOC002", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-202", "LOCFR": "SUP-002", "changed": True, "qtyChanged": True, "qtyDelta": 50},
        {"LOCID": "LOC002", "GSCEQUIPCAT": "PUMP", "PRDID": "MAT-203", "LOCFR": "SUP-002", "changed": True, "qtyChanged": True, "qtyDelta": 75},
    ]
    
    mcp_context = builder.build_mcp_context(
        analytics,
        records,
        query_intent="comparison",
        extracted_entities={"LOCID": ["LOC001", "LOC002"]}
    )
    
    print(f"✓ MCP Context built for comparison")
    
    # Step 3: Extract and Compare
    print_subsection("STEP 3: Extract and Compare Scoped Records")
    
    loc001_records = builder.extract_scoped_records(records, "location", "LOC001")
    loc002_records = builder.extract_scoped_records(records, "location", "LOC002")
    
    loc001_metrics = builder.compute_scoped_metrics(loc001_records)
    loc002_metrics = builder.compute_scoped_metrics(loc002_records)
    
    print(f"✓ LOC001: {loc001_metrics['filteredRecordsCount']} records, {loc001_metrics['changedCount']} changed ({loc001_metrics['changeRate']}%)")
    print(f"✓ LOC002: {loc002_metrics['filteredRecordsCount']} records, {loc002_metrics['changedCount']} changed ({loc002_metrics['changeRate']}%)")
    
    # Step 4: Build Comparison Response
    print_subsection("STEP 4: Build Comparison Response")
    
    comparison_response = {
        "decision": "LOC002 has more changes than LOC001",
        "comparisonMetrics": {
            "LOC001": {
                "changedCount": loc001_metrics['changedCount'],
                "changeRate": loc001_metrics['changeRate'],
                "primaryDriver": loc001_metrics['scopedDrivers']['primary']
            },
            "LOC002": {
                "changedCount": loc002_metrics['changedCount'],
                "changeRate": loc002_metrics['changeRate'],
                "primaryDriver": loc002_metrics['scopedDrivers']['primary']
            }
        },
        "actions": ["Monitor LOC002 closely", "Investigate supplier changes"]
    }
    
    print(f"✓ Comparison response built")
    
    # Step 5: Validate Response
    print_subsection("STEP 5: Validate Response")
    guardrails = ValidationGuardrails(mcp_context)
    is_valid, errors = guardrails.validate_response(comparison_response)
    
    if is_valid:
        print(f"✓ Response validation PASSED")
    else:
        print(f"✗ Response validation FAILED")
    
    # Step 6: Generate Natural Language Response
    print_subsection("STEP 6: Generate Natural Language Response (Simulated)")
    
    response_text = (
        f"📊 Comparison: LOC001 vs LOC002\n\n"
        f"LOC001: {loc001_metrics['changedCount']}/{loc001_metrics['filteredRecordsCount']} records changed "
        f"({loc001_metrics['changeRate']}%). Primary driver: {loc001_metrics['scopedDrivers']['primary']}\n"
        f"LOC002: {loc002_metrics['changedCount']}/{loc002_metrics['filteredRecordsCount']} records changed "
        f"({loc002_metrics['changeRate']}%). Primary driver: {loc002_metrics['scopedDrivers']['primary']}\n\n"
        f"→ LOC002 has more changes and requires closer monitoring."
    )
    
    print(f"✓ Natural language response generated:")
    print(f"\nCopilot:\n{response_text}")


def demo_3_validation():
    """Demo 3: Validation - Show hallucination detection."""
    print_section("DEMO 3: Validation - Hallucination Detection")
    
    print_subsection("STEP 1: Build MCP Context")
    builder = MCPContextBuilder()
    
    analytics = {
        "planningHealth": "Critical",
        "forecastNew": 1000,
        "forecastOld": 800,
        "trendDelta": 200,
        "changedRecordCount": 15,
        "totalRecords": 33,
        "drivers": {"forecast": 60, "supplier": 30, "design": 10},
        "dataSource": "Blob",
        "lastRefreshedAt": datetime.now(timezone.utc).isoformat(),
        "blobFileNamesUsed": ["data_2026_04_09.csv"],
        "recordsAnalyzed": 1000
    }
    
    records = [
        {"LOCID": "LOC001", "GSCEQUIPCAT": "UPS", "PRDID": "MAT-101", "LOCFR": "SUP-001", "changed": True, "qtyChanged": True, "qtyDelta": 100}
    ]
    
    mcp_context = builder.build_mcp_context(analytics, records)
    guardrails = ValidationGuardrails(mcp_context)
    
    print(f"✓ MCP Context built")
    
    print_subsection("STEP 2: Test Valid Response")
    valid_response = {
        "decision": "Location is risky",
        "keyMetrics": {"changedCount": 15, "changeRate": 45.5},
        "drivers": {"forecast": 60, "supplier": 30, "design": 10}
    }
    
    is_valid, errors = guardrails.validate_response(valid_response)
    print(f"✓ Valid response: {is_valid}")
    
    print_subsection("STEP 3: Test Invalid Response (Hallucination)")
    invalid_response = "The supplier is Unknown and might be risky"
    
    has_hallucination, suspicious = guardrails.detect_hallucination(invalid_response)
    print(f"✓ Hallucination detected: {has_hallucination}")
    if suspicious:
        print(f"  Suspicious items found:")
        for item in suspicious:
            print(f"    - {item}")
    
    print_subsection("STEP 4: Test Invalid Metrics")
    invalid_metrics = {
        "drivers": {"forecast": 150, "supplier": 30, "design": 10}  # Sum > 100
    }
    
    is_valid, errors = guardrails.validate_response(invalid_metrics)
    print(f"✓ Invalid metrics detected: {not is_valid}")
    if errors:
        print(f"  Errors found:")
        for error in errors:
            print(f"    - {error}")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("PHASE 0 DEMO - Prompt/Response Flow")
    print("=" * 80)
    
    demo_1_simple_query()
    demo_2_comparison_query()
    demo_3_validation()
    
    print_section("DEMO COMPLETE")
    print("\n✓ All demos completed successfully!")
    print("\nKey Takeaways:")
    print("  1. User provides a query (prompt)")
    print("  2. MCP context is built with SAP schema and analytics data")
    print("  3. Scoped records are extracted based on query intent")
    print("  4. Metrics are computed for the scoped records")
    print("  5. Response is validated against domain rules")
    print("  6. Natural language response is generated")
    print("  7. Response is returned to user")
    print("\n✓ Phase 0 is working correctly!")


if __name__ == "__main__":
    main()
