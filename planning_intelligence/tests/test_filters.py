import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import PlanningRecord
from filters import filter_records, get_available_locations, get_available_material_groups


def _rec(loc, mg, mid="MAT-1") -> PlanningRecord:
    return PlanningRecord(
        location_id=loc, material_group=mg, material_id=mid,
        supplier=None, forecast_qty=None, roj=None, bod=None, ff=None,
        # context fields all optional/defaulted
    )


RECORDS = [
    _rec("LOC001", "PUMP"),
    _rec("LOC001", "VALVE"),
    _rec("LOC002", "PUMP"),
    _rec("LOC003", "MOTOR"),
]


def test_filter_by_location():
    result = filter_records(RECORDS, location_id="LOC001")
    assert len(result) == 2
    assert all(r.location_id == "LOC001" for r in result)


def test_filter_by_material_group():
    result = filter_records(RECORDS, material_group="PUMP")
    assert len(result) == 2
    assert all(r.material_group == "PUMP" for r in result)


def test_filter_both():
    result = filter_records(RECORDS, location_id="LOC001", material_group="PUMP")
    assert len(result) == 1


def test_filter_case_insensitive():
    result = filter_records(RECORDS, location_id="loc001", material_group="pump")
    assert len(result) == 1


def test_no_filter_returns_all():
    result = filter_records(RECORDS)
    assert len(result) == 4


def test_available_locations():
    locs = get_available_locations(RECORDS)
    assert locs == ["LOC001", "LOC002", "LOC003"]


def test_available_material_groups():
    mgs = get_available_material_groups(RECORDS)
    assert mgs == ["MOTOR", "PUMP", "VALVE"]
