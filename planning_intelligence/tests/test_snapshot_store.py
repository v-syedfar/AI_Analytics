import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tempfile
from snapshot_store import save_snapshot, load_snapshot, get_last_updated_time, snapshot_exists, clear_snapshot

TEST_DATA = {
    "planningHealth": 80,
    "status": "Healthy",
    "totalRecords": 100,
    "changedRecordCount": 10,
}


def test_save_and_load():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_snapshot(TEST_DATA, path=path)
        loaded = load_snapshot(path=path)
        assert loaded is not None
        assert loaded["planningHealth"] == 80
        assert loaded["dataMode"] == "cached"
        assert "lastRefreshedAt" in loaded
    finally:
        if os.path.exists(path): os.remove(path)


def test_snapshot_exists():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        assert not snapshot_exists(path=path)
        save_snapshot(TEST_DATA, path=path)
        assert snapshot_exists(path=path)
    finally:
        if os.path.exists(path): os.remove(path)


def test_get_last_updated_time():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_snapshot(TEST_DATA, path=path)
        ts = get_last_updated_time(path=path)
        assert ts is not None
        assert "T" in ts  # ISO format
    finally:
        if os.path.exists(path): os.remove(path)


def test_load_returns_none_when_missing():
    result = load_snapshot(path="/tmp/nonexistent_planning_snap_xyz.json")
    assert result is None


def test_clear_snapshot():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    try:
        save_snapshot(TEST_DATA, path=path)
        clear_snapshot(path=path)
        assert not snapshot_exists(path=path)
    finally:
        if os.path.exists(path): os.remove(path)


def test_memory_fallback():
    """When file path is invalid, falls back to memory store."""
    from snapshot_store import _memory_store
    import snapshot_store as ss
    ss._memory_store = None
    save_snapshot(TEST_DATA, path="/invalid/path/snap.json")
    loaded = load_snapshot(path="/invalid/path/snap.json")
    assert loaded is not None
    assert loaded["planningHealth"] == 80
    ss._memory_store = None  # cleanup
