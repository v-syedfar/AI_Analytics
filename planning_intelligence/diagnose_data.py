#!/usr/bin/env python3
"""
Diagnostic script to understand the actual data structure and content.
Run this to see what's in your detailRecords.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from snapshot_store import load_snapshot
from blob_loader import load_current_previous_from_blob

def diagnose_snapshot():
    """Check what's in the cached snapshot."""
    print("\n" + "="*80)
    print("DIAGNOSING CACHED SNAPSHOT")
    print("="*80)
    
    snap = load_snapshot()
    if not snap:
        print("✗ No cached snapshot found")
        return False
    
    print(f"✓ Snapshot loaded")
    print(f"  - Keys: {list(snap.keys())}")
    print(f"  - Planning Health: {snap.get('planningHealth')}")
    print(f"  - Total Records: {snap.get('totalRecords')}")
    print(f"  - Changed Records: {snap.get('changedRecordCount')}")
    
    detail_records = snap.get("detailRecords", [])
    print(f"\n  - Detail Records Count: {len(detail_records)}")
    
    if detail_records:
        first = detail_records[0]
        print(f"  - First Record Type: {type(first)}")
        
        if isinstance(first, dict):
            print(f"  - First Record Keys: {list(first.keys())}")
            print(f"  - First Record Sample:")
            for key in list(first.keys())[:10]:
                print(f"      {key}: {first[key]}")
        else:
            print(f"  - First Record Attributes: {[attr for attr in dir(first) if not attr.startswith('_')][:10]}")
        
        # Check for location IDs
        locations = set()
        for r in detail_records[:100]:  # Check first 100
            if isinstance(r, dict):
                loc = r.get("locationId") or r.get("LOCID") or r.get("location_id")
            else:
                loc = getattr(r, "location_id", None)
            if loc:
                locations.add(str(loc))
        
        print(f"\n  - Sample Locations (first 100 records): {sorted(list(locations))[:10]}")
        
        # Check if AVC11_F01C01 exists
        avc_count = 0
        for r in detail_records:
            if isinstance(r, dict):
                loc = r.get("locationId") or r.get("LOCID") or r.get("location_id")
            else:
                loc = getattr(r, "location_id", None)
            if loc and "AVC11_F01C01" in str(loc).upper():
                avc_count += 1
        
        print(f"  - Records with AVC11_F01C01: {avc_count}")
        
        return True
    else:
        print("  ✗ No detail records in snapshot")
        return False

def diagnose_blob():
    """Check what's in the blob storage."""
    print("\n" + "="*80)
    print("DIAGNOSING BLOB STORAGE")
    print("="*80)
    
    try:
        current_rows, previous_rows = load_current_previous_from_blob()
        print(f"✓ Blob data loaded")
        print(f"  - Current rows: {len(current_rows)}")
        print(f"  - Previous rows: {len(previous_rows)}")
        
        if current_rows:
            first = current_rows[0]
            print(f"\n  - First Current Row Type: {type(first)}")
            print(f"  - First Current Row Keys: {list(first.keys())}")
            print(f"  - First Current Row Sample:")
            for key in list(first.keys())[:10]:
                print(f"      {key}: {first[key]}")
            
            # Check for location IDs
            locations = set()
            for r in current_rows[:100]:
                loc = r.get("LOCID") or r.get("locationId") or r.get("location_id")
                if loc:
                    locations.add(str(loc))
            
            print(f"\n  - Sample Locations (first 100 rows): {sorted(list(locations))[:10]}")
            
            # Check if AVC11_F01C01 exists
            avc_count = 0
            for r in current_rows:
                loc = r.get("LOCID") or r.get("locationId") or r.get("location_id")
                if loc and "AVC11_F01C01" in str(loc).upper():
                    avc_count += 1
            
            print(f"  - Rows with AVC11_F01C01: {avc_count}")
            
            return True
        else:
            print("  ✗ No current rows in blob")
            return False
            
    except Exception as e:
        print(f"✗ Error loading blob: {e}")
        return False

def main():
    """Run diagnostics."""
    print("\n" + "="*80)
    print("DATA STRUCTURE DIAGNOSTIC")
    print("="*80)
    
    snap_ok = diagnose_snapshot()
    blob_ok = diagnose_blob()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if snap_ok:
        print("✓ Snapshot has data")
    else:
        print("✗ Snapshot is empty or missing")
    
    if blob_ok:
        print("✓ Blob has data")
    else:
        print("✗ Blob is empty or missing")
    
    if not snap_ok and not blob_ok:
        print("\n⚠ ISSUE: No data found in snapshot or blob!")
        print("  This explains why supplier queries return 'No supplier information found'")
        print("  Solution: Load data from blob storage first")
        return 1
    
    print("\n✓ Diagnostics complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
