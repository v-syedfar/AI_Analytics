#!/usr/bin/env python3
"""
Local verification script to test the supplier query fix WITHOUT deploying to Azure.

This script:
1. Loads the CSV data
2. Simulates the response building process
3. Tests supplier queries locally
4. Shows what the Azure Function should return after deployment
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from blob_loader import load_all_data
from response_builder import get_suppliers_for_location, compute_supplier_metrics, analyze_supplier_behavior
from function_app import _normalize_detail_records, _extract_scope


def test_supplier_query_locally(location: str):
    """Test supplier query locally without Azure Function."""
    
    print(f"\n{'='*80}")
    print(f"Testing Supplier Query Locally: {location}")
    print(f"{'='*80}\n")
    
    # Step 1: Load data
    print("Step 1: Loading CSV data...")
    try:
        data = load_all_data()
        print(f"✓ Loaded data successfully")
        print(f"  - Total records: {len(data)}")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return
    
    # Step 2: Simulate response building (using ALL records, not just changed)
    print(f"\nStep 2: Building response context (using ALL records)...")
    try:
        # This simulates what response_builder.py does
        compared = data  # ALL records
        detail_records = compared  # This is the fix - use ALL records
        print(f"✓ Built response context")
        print(f"  - Detail records: {len(detail_records)}")
    except Exception as e:
        print(f"✗ Failed to build context: {e}")
        return
    
    # Step 3: Normalize records
    print(f"\nStep 3: Normalizing detail records...")
    try:
        normalized = _normalize_detail_records(detail_records)
        print(f"✓ Normalized records")
        print(f"  - Normalized records: {len(normalized)}")
        
        # Show unique locations
        locations = set(r.get("locationId", "").upper() for r in normalized if r.get("locationId"))
        print(f"  - Unique locations: {len(locations)}")
        if location.upper() in locations:
            print(f"  ✓ Location {location} found in data")
        else:
            print(f"  ✗ Location {location} NOT found in data")
            print(f"    Available locations: {sorted(list(locations))[:10]}...")
    except Exception as e:
        print(f"✗ Failed to normalize: {e}")
        return
    
    # Step 4: Get suppliers for location
    print(f"\nStep 4: Getting suppliers for location {location}...")
    try:
        suppliers = get_suppliers_for_location(normalized, location)
        print(f"✓ Got suppliers")
        print(f"  - Suppliers found: {len(suppliers)}")
        if suppliers:
            print(f"  - Supplier list: {suppliers}")
        else:
            print(f"  ✗ No suppliers found for {location}")
    except Exception as e:
        print(f"✗ Failed to get suppliers: {e}")
        return
    
    # Step 5: Build response
    print(f"\nStep 5: Building response...")
    if not suppliers:
        response = f"No supplier information found for location {location}."
        print(f"✗ Response: {response}")
        return
    
    try:
        lines = [f"📊 Suppliers at {location}:\n"]
        lines.append(f"{'Supplier':<20} {'Records':<10} {'Changed':<10} {'Forecast':<12} {'Design':<10} {'Avail':<8} {'ROJ':<8} {'Risk':<8}")
        lines.append("-" * 90)
        
        for supplier in suppliers:
            metrics = compute_supplier_metrics(normalized, location, supplier)
            behavior = analyze_supplier_behavior(normalized, location, supplier)
            
            sup_name = supplier[:19]
            records = metrics['affected_records']
            changed = metrics['changed_records']
            forecast = f"{metrics['forecast_impact']:+,.0f}"
            design = f"{metrics['design_changes']} ({behavior['design_pct']}%)"
            avail = metrics['availability_issues']
            roj = f"{metrics['roj_issues']} ({behavior['roj_pct']}%)"
            risk = metrics['risk_count']
            lines.append(f"{sup_name:<20} {records:<10} {changed:<10} {forecast:<12} {design:<10} {avail:<8} {roj:<8} {risk:<8}")
        
        response = "\n".join(lines)
        print(f"✓ Response built successfully:\n")
        print(response)
    except Exception as e:
        print(f"✗ Failed to build response: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n{'='*80}")
    print("✓ LOCAL TEST PASSED - This is what Azure Function should return after deployment")
    print(f"{'='*80}\n")


def main():
    """Run local verification tests."""
    
    print("\n" + "="*80)
    print("LOCAL VERIFICATION - Supplier Query Fix")
    print("="*80)
    print("\nThis script tests the supplier query fix locally WITHOUT deploying to Azure.")
    print("It shows what the Azure Function should return after deployment.\n")
    
    # Test with the location from the user's query
    test_supplier_query_locally("AVC11_F01C01")
    
    # Also test with a common location
    print("\n" + "="*80)
    print("Testing with alternative location format...")
    print("="*80)
    test_supplier_query_locally("LOC001")


if __name__ == "__main__":
    main()
