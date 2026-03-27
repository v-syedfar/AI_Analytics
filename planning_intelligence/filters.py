from typing import Optional
from models import PlanningRecord


def filter_records(
    records: list,
    location_id: Optional[str] = None,
    material_group: Optional[str] = None,
) -> list:
    """Filter records by locationId and/or materialGroup (case-insensitive)."""
    result = records
    if location_id:
        loc = location_id.strip().lower()
        result = [r for r in result if r.location_id.lower() == loc]
    if material_group:
        mg = material_group.strip().lower()
        result = [r for r in result if r.material_group.lower() == mg]
    return result


def get_available_locations(records: list[PlanningRecord]) -> list[str]:
    return sorted({r.location_id for r in records if r.location_id})


def get_available_material_groups(records: list[PlanningRecord]) -> list[str]:
    return sorted({r.material_group for r in records if r.material_group})
