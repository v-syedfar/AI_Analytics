"""
Blob Loader Tests
Tests blob_loader.py without requiring real Azure Blob Storage.
Uses in-memory Excel bytes to simulate blob content.
"""
import sys, os, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

pytestmark = pytest.mark.skipif(not HAS_PANDAS, reason="pandas not installed in local env")
from blob_loader import (
    load_excel_from_bytes,
    standardize_columns,
    validate_required_columns,
    BlobLoaderError,
)


def _make_excel_bytes(data: dict) -> bytes:
    """Creates an in-memory Excel file from a dict of {col: [values]}."""
    import pandas as pd
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


VALID_DATA = {
    "LOCID": ["LOC001", "LOC002"],
    "PRDID": ["MAT-100", "MAT-101"],
    "GSCEQUIPCAT": ["PUMP", "VALVE"],
    "GSCFSCTQTY": ["100", "50"],
}


def test_load_excel_from_bytes_valid():
    content = _make_excel_bytes(VALID_DATA)
    df = load_excel_from_bytes(content, label="test")
    assert len(df) == 2
    assert "LOCID" in df.columns


def test_load_excel_from_bytes_empty_raises():
    with pytest.raises(BlobLoaderError, match="Empty file content"):
        load_excel_from_bytes(b"", label="test")


def test_load_excel_from_bytes_invalid_raises():
    with pytest.raises(BlobLoaderError, match="Failed to parse Excel"):
        load_excel_from_bytes(b"not an excel file", label="test")


def test_standardize_columns_uppercases():
    content = _make_excel_bytes({"locid": ["LOC001"], "prdid": ["MAT-1"], "gscequipcat": ["PUMP"]})
    df = load_excel_from_bytes(content)
    df = standardize_columns(df)
    assert "LOCID" in df.columns
    assert "PRDID" in df.columns


def test_standardize_columns_applies_aliases():
    content = _make_excel_bytes({"LOC ID": ["LOC001"], "PRD ID": ["MAT-1"], "GSCEQUIPCAT": ["PUMP"]})
    df = load_excel_from_bytes(content)
    df = standardize_columns(df)
    assert "LOCID" in df.columns
    assert "PRDID" in df.columns


def test_validate_required_columns_passes():
    content = _make_excel_bytes(VALID_DATA)
    df = load_excel_from_bytes(content)
    df = standardize_columns(df)
    validate_required_columns(df, label="test")  # should not raise


def test_validate_required_columns_missing_raises():
    content = _make_excel_bytes({"LOCID": ["LOC001"], "PRDID": ["MAT-1"]})  # missing GSCEQUIPCAT
    df = load_excel_from_bytes(content)
    df = standardize_columns(df)
    with pytest.raises(BlobLoaderError, match="Missing required columns"):
        validate_required_columns(df, label="test")


def test_require_env_raises_when_missing(monkeypatch):
    from blob_loader import _require_env
    monkeypatch.delenv("BLOB_CONNECTION_STRING", raising=False)
    with pytest.raises(BlobLoaderError, match="Missing required environment variable"):
        _require_env("BLOB_CONNECTION_STRING")
