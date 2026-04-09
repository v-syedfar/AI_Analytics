#!/usr/bin/env python3
"""
Check what's actually in the snapshot file.
Run this to diagnose why detailRecords is empty.
"""
import json
import os
from snapshot_store import load_snapshot

# Try to load the snapshot
snap = load_snapshot()

if not snap:
    print("❌ No snapshot found!")
    print("   Checked paths:")
    print("   - /home/data/planning_snapshot.json")
    print("   - /tmp/planning_snapshot.json")
    print("   - Memory store")
    exit(1)

print("✅ Snapshot loaded successfully!")
print()

# Check what fields are in the snapshot
print("📋 Snapshot fields:")
for key in sorted(snap.keys()):
    value = snap[key]
    if isinstance(value, list):
        print(f"  - {key}: list with {len(value)} items")
    elif isinstance(value, dict):
        print(f"  - {key}: dict with {len(value)} keys")
    elif isinstance(value, str):
        print(f"  - {key}: string ({len(value)} chars)")
    else:
        print(f"  - {key}: {type(value).__name__}")

print()

# Check detailRecords specifically
if "detailRecords" not in snap:
    print("❌ detailRecords field is MISSING from snapshot!")
    exit(1)

detail_records = snap["detailRecords"]
print(f"📊 detailRecords: {len(detail_records)} records")

if len(detail_records) == 0:
    print("❌ detailRecords is EMPTY!")
    exit(1)

# Check first record
first = detail_records[0]
print()
print("First record:")
print(f"  Type: {type(first)}")
if isinstance(first, dict):
    print(f"  Keys: {list(first.keys())}")
    print(f"  locationId: {first.get('locationId')}")
    print(f"  supplier: {first.get('supplier')}")
    print(f"  materialId: {first.get('materialId')}")
else:
    print(f"  Not a dict! Type: {type(first)}")

# Check how many records have CYS20_F01C01
cys_records = [r for r in detail_records if isinstance(r, dict) and r.get("locationId") == "CYS20_F01C01"]
print()
print(f"Records for CYS20_F01C01: {len(cys_records)}")

if len(cys_records) > 0:
    print("✅ Found records for CYS20_F01C01!")
    # Check suppliers
    suppliers = set(r.get("supplier") for r in cys_records if r.get("supplier"))
    print(f"   Suppliers: {suppliers}")
else:
    print("❌ No records found for CYS20_F01C01!")
    # Show what locations are in the data
    locations = set(r.get("locationId") for r in detail_records if isinstance(r, dict) and r.get("locationId"))
    print(f"   Available locations: {sorted(list(locations))[:10]}")  # Show first 10

print()
print("✅ Snapshot check complete!")
