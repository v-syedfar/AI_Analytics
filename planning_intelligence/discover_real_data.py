#!/usr/bin/env python3
"""
Discover the REAL location IDs, material IDs, and equipment categories in your data.
This will show you what actually exists so we can use correct values in tests.
"""

import sys
import os
import json
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))

from snapshot_store import load_snapshot

def discover_data():
    """Discover what's actually in the data."""
    print("\n" + "="*80)
    print("DISCOVERING REAL DATA IN YOUR SYSTEM")
    print("="*80)
    
    snap = load_snapshot()
    if not snap:
        print("✗ No cached snapshot found")
        return False
    
    detail_records = snap.get("detailRecords", [])
    if not detail_records:
        print("✗ No detail records found")
        return False
    
    print(f"\n✓ Found {len(detail_records)} detail records\n")
    
    # Discover location IDs
    print("="*80)
    print("LOCATION IDs (First 20)")
    print("="*80)
    locations = Counter()
    for r in detail_records:
        if isinstance(r, dict):
            loc = r.get("locationId") or r.get("LOCID") or r.get("location_id")
        else:
            loc = getattr(r, "location_id", None)
        if loc:
            locations[str(loc).upper()] += 1
    
    if locations:
        for loc, count in locations.most_common(20):
            print(f"  {loc:<20} ({count:>5} records)")
    else:
        print("  ✗ No location IDs found")
    
    # Discover material IDs
    print("\n" + "="*80)
    print("MATERIAL IDs (First 20)")
    print("="*80)
    materials = Counter()
    for r in detail_records:
        if isinstance(r, dict):
            mat = r.get("materialId") or r.get("PRDID") or r.get("material_id")
        else:
            mat = getattr(r, "material_id", None)
        if mat:
            materials[str(mat).upper()] += 1
    
    if materials:
        for mat, count in materials.most_common(20):
            print(f"  {mat:<20} ({count:>5} records)")
    else:
        print("  ✗ No material IDs found")
    
    # Discover equipment categories
    print("\n" + "="*80)
    print("EQUIPMENT CATEGORIES (First 20)")
    print("="*80)
    categories = Counter()
    for r in detail_records:
        if isinstance(r, dict):
            cat = r.get("materialGroup") or r.get("GSCEQUIPCAT") or r.get("material_group")
        else:
            cat = getattr(r, "material_group", None)
        if cat:
            categories[str(cat).upper()] += 1
    
    if categories:
        for cat, count in categories.most_common(20):
            print(f"  {cat:<20} ({count:>5} records)")
    else:
        print("  ✗ No equipment categories found")
    
    # Discover suppliers
    print("\n" + "="*80)
    print("SUPPLIERS (First 20)")
    print("="*80)
    suppliers = Counter()
    for r in detail_records:
        if isinstance(r, dict):
            sup = r.get("supplier") or r.get("LOCFR") or r.get("supplier_current")
        else:
            sup = getattr(r, "supplier_current", None) or getattr(r, "supplier", None)
        if sup:
            suppliers[str(sup).upper()] += 1
    
    if suppliers:
        for sup, count in suppliers.most_common(20):
            print(f"  {sup:<20} ({count:>5} records)")
    else:
        print("  ✗ No suppliers found")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total detail records: {len(detail_records)}")
    print(f"Unique locations: {len(locations)}")
    print(f"Unique materials: {len(materials)}")
    print(f"Unique equipment categories: {len(categories)}")
    print(f"Unique suppliers: {len(suppliers)}")
    
    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDED TEST VALUES")
    print("="*80)
    
    if locations:
        top_loc = locations.most_common(1)[0][0]
        print(f"\n✓ Use these LOCATION IDs in tests:")
        for loc, count in locations.most_common(5):
            print(f"  - {loc}")
    
    if materials:
        top_mat = materials.most_common(1)[0][0]
        print(f"\n✓ Use these MATERIAL IDs in tests:")
        for mat, count in materials.most_common(5):
            print(f"  - {mat}")
    
    if categories:
        print(f"\n✓ Use these EQUIPMENT CATEGORIES in tests:")
        for cat, count in categories.most_common(5):
            print(f"  - {cat}")
    
    if suppliers:
        print(f"\n✓ Use these SUPPLIERS in tests:")
        for sup, count in suppliers.most_common(5):
            print(f"  - {sup}")
    
    # Export to JSON
    export_data = {
        "locations": dict(locations.most_common(50)),
        "materials": dict(materials.most_common(50)),
        "categories": dict(categories.most_common(50)),
        "suppliers": dict(suppliers.most_common(50)),
    }
    
    with open("discovered_data.json", "w") as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✓ Exported to discovered_data.json")
    
    return True

if __name__ == "__main__":
    success = discover_data()
    sys.exit(0 if success else 1)
