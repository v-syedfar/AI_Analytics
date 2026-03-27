"""
Snapshot Store
Lightweight persistence layer for daily planning snapshots.
Stores the full dashboard JSON to a local file (Azure Function persistent storage)
or in-memory for testing.

Storage path is controlled by:
  SNAPSHOT_FILE_PATH  (default: /tmp/planning_snapshot.json)

For production, mount an Azure Files share and point SNAPSHOT_FILE_PATH there.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_PATH = os.environ.get("SNAPSHOT_FILE_PATH", "/tmp/planning_snapshot.json")

# In-memory fallback (used when file system is unavailable)
_memory_store: Optional[dict] = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_snapshot(data: dict, path: str = DEFAULT_PATH) -> None:
    """
    Saves dashboard response dict as a JSON snapshot.
    Adds metadata: savedAt timestamp, dataMode = "cached".
    """
    global _memory_store

    payload = {
        **data,
        "dataMode": "cached",
        "lastRefreshedAt": datetime.now(timezone.utc).isoformat(),
    }

    # Try file system first
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, default=str)
        logger.info(f"Snapshot saved to {path}")
    except OSError as e:
        logger.warning(f"Could not write snapshot to {path}: {e}. Using memory store.")
        _memory_store = payload


def load_snapshot(path: str = DEFAULT_PATH) -> Optional[dict]:
    """
    Loads the latest snapshot. Returns None if no snapshot exists.
    """
    global _memory_store

    # Try file first
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Snapshot loaded from {path}")
            return data
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Could not read snapshot from {path}: {e}")

    # Fall back to memory
    if _memory_store:
        logger.info("Snapshot loaded from memory store.")
        return _memory_store

    return None


def get_last_updated_time(path: str = DEFAULT_PATH) -> Optional[str]:
    """Returns the ISO timestamp of the last snapshot, or None."""
    snap = load_snapshot(path)
    if snap:
        return snap.get("lastRefreshedAt")
    return None


def snapshot_exists(path: str = DEFAULT_PATH) -> bool:
    """Returns True if a valid snapshot is available."""
    return load_snapshot(path) is not None


def clear_snapshot(path: str = DEFAULT_PATH) -> None:
    """Clears the snapshot (useful for testing)."""
    global _memory_store
    _memory_store = None
    if os.path.exists(path):
        os.remove(path)
        logger.info(f"Snapshot cleared: {path}")
