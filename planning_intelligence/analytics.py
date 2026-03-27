from dataclasses import asdict
from collections import Counter
from models import ComparedRecord


def is_changed(rec: ComparedRecord) -> bool:
    return rec.change_type != "Unchanged"


def build_summary(records: list[ComparedRecord]) -> dict:
    """Full summary — answers all six analytical questions in one response."""
    changed = [r for r in records if is_changed(r)]
    unchanged = [r for r in records if not is_changed(r)]

    return {
        # Q1: How many records changed?
        "total_available_records": len(records),
        "changed_record_count": len(changed),
        "unchanged_record_count": len(unchanged),

        # Q2: Which material IDs changed?
        "changed_material_ids": sorted({r.material_id for r in changed}),

        # Q3: Which locations have the most changes?
        "changes_by_location": _count_by(changed, "location_id"),

        # Q4: Which material groups have changes?
        "changes_by_material_group": _count_by(changed, "material_group"),

        # Q5: Are changes quantity-, supplier-, or design-driven?
        "change_driver_summary": _change_driver_summary(changed),

        # Q6: Which records are high risk?
        "high_risk_records": [_serialize(r) for r in changed if r.risk_level != "Normal"],

        # Full detail
        "change_type_summary": dict(Counter(r.change_type for r in changed)),
        "changed_records": [_serialize(r) for r in changed],
    }


def build_location_material_list(records: list[ComparedRecord]) -> dict:
    return {
        "available_locations": sorted({r.location_id for r in records}),
        "available_material_groups": sorted({r.material_group for r in records}),
    }


def changes_by_location(records: list[ComparedRecord]) -> dict:
    """Q3: Ranked list of locations by number of changed records."""
    changed = [r for r in records if is_changed(r)]
    return {
        "changes_by_location": _count_by(changed, "location_id"),
        "changed_record_count": len(changed),
    }


def changes_by_material_group(records: list[ComparedRecord]) -> dict:
    """Q4: Which material groups have changes and how many."""
    changed = [r for r in records if is_changed(r)]
    return {
        "changes_by_material_group": _count_by(changed, "material_group"),
        "changed_record_count": len(changed),
    }


def change_driver_analysis(records: list[ComparedRecord]) -> dict:
    """Q5: Break down whether changes are qty-, supplier-, or design-driven."""
    changed = [r for r in records if is_changed(r)]
    return {
        "change_driver_summary": _change_driver_summary(changed),
        "change_type_summary": dict(Counter(r.change_type for r in changed)),
        "changed_record_count": len(changed),
    }


def high_risk_records(records: list[ComparedRecord]) -> dict:
    """Q6: All records with a non-Normal risk level."""
    risky = [r for r in records if is_changed(r) and r.risk_level != "Normal"]
    return {
        "high_risk_count": len(risky),
        "risk_level_summary": dict(Counter(r.risk_level for r in risky)),
        "high_risk_records": [_serialize(r) for r in risky],
    }


def filter_by_supplier_design_change(records: list[ComparedRecord]) -> list[dict]:
    """Records where both supplier AND design changed."""
    return [_serialize(r) for r in records if r.supplier_changed and r.design_changed]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_by(records: list[ComparedRecord], field: str) -> list[dict]:
    """Return [{field, count}] sorted descending by count."""
    counts = Counter(getattr(r, field) for r in records)
    return [
        {field: k, "change_count": v}
        for k, v in sorted(counts.items(), key=lambda x: -x[1])
    ]


def _change_driver_summary(changed: list[ComparedRecord]) -> dict:
    return {
        "quantity_driven": sum(1 for r in changed if r.qty_changed),
        "supplier_driven": sum(1 for r in changed if r.supplier_changed),
        "design_driven": sum(1 for r in changed if r.design_changed),
        "roj_driven": sum(1 for r in changed if r.roj_changed),
    }


def _serialize(rec: ComparedRecord) -> dict:
    return asdict(rec)
