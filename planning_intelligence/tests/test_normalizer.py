import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from normalizer import normalize_row

RAW_CURRENT = {
    "LOCID": "LOC001",
    "GSCEQUIPCAT": "PUMP",
    "PRDID": "MAT-100",
    "LOCFR": "Supplier A",
    "GSCFSCTQTY": "50",
    "GSCCONROJDATE": "2026-06-01",
    "ZCOIBODVER": "v2",
    "ZCOIFORMFACT": "FF-A",
}

RAW_PREVIOUS = {
    **RAW_CURRENT,
    "GSCPREVFCSTQTY": "40",
    "GSCPREVROJNBD": "2026-05-01",
}


def test_normalize_current():
    rec = normalize_row(RAW_CURRENT, is_current=True)
    assert rec.location_id == "LOC001"
    assert rec.material_group == "PUMP"
    assert rec.material_id == "MAT-100"
    assert rec.supplier == "Supplier A"
    assert rec.forecast_qty == 50.0
    assert rec.roj == "2026-06-01"
    assert rec.bod == "v2"
    assert rec.ff == "FF-A"


def test_normalize_previous():
    rec = normalize_row(RAW_PREVIOUS, is_current=False)
    assert rec.forecast_qty == 40.0
    assert rec.roj == "2026-05-01"


def test_normalize_missing_locfr_falls_back_to_locfrdescr():
    raw = {**RAW_CURRENT, "LOCFR": None, "LOCFRDESCR": "Supplier B"}
    rec = normalize_row(raw, is_current=True)
    assert rec.supplier == "Supplier B"


def test_normalize_empty_strings_become_none():
    raw = {**RAW_CURRENT, "ZCOIBODVER": "", "ZCOIFORMFACT": "  "}
    rec = normalize_row(raw, is_current=True)
    assert rec.bod is None
    assert rec.ff is None
