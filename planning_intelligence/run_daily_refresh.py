"""
Daily Refresh Job
Reads SharePoint files, runs the full analytics pipeline,
builds the dashboard response, and saves a snapshot.

Can be triggered:
  1. Manually: python run_daily_refresh.py
  2. Azure Function Timer Trigger (add to function_app.py)
  3. Azure Logic App / Scheduler
"""
import logging
import os
import sys

# Allow running standalone
sys.path.insert(0, os.path.dirname(__file__))

from sharepoint_loader import load_current_previous_from_sharepoint, SharePointError
from normalizer import normalize_rows
from filters import filter_records
from comparator import compare_records
from trend_analyzer import analyze_trends
from response_builder import build_response
from snapshot_store import save_snapshot

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def run_daily_refresh(
    location_id: str = None,
    material_group: str = None,
) -> dict:
    """
    Full pipeline:
    1. Load current + previous from SharePoint
    2. Normalize
    3. Filter (optional)
    4. Compare
    5. Build dashboard response
    6. Save snapshot
    Returns the dashboard response dict.
    """
    logger.info("Starting daily planning refresh...")

    # Step 1: Load from SharePoint
    try:
        current_rows, previous_rows = load_current_previous_from_sharepoint()
        logger.info(f"Loaded {len(current_rows)} current rows, {len(previous_rows)} previous rows.")
    except SharePointError as e:
        logger.error(f"SharePoint load failed: {e}")
        raise

    # Step 2: Normalize
    current_records = normalize_rows(current_rows, is_current=True)
    previous_records = normalize_rows(previous_rows, is_current=False)

    # Step 3: Filter (if specified)
    current_filtered = filter_records(current_records, location_id, material_group)
    previous_filtered = filter_records(previous_records, location_id, material_group)

    # Step 4: Compare
    compared = compare_records(current_filtered, previous_filtered)
    logger.info(f"Compared {len(compared)} records.")

    # Step 5: Build dashboard response
    result = build_response(compared, [], location_id, material_group, data_mode="cached")

    # Step 6: Save snapshot
    save_snapshot(result)
    logger.info("Daily refresh complete. Snapshot saved.")

    return result


# ---------------------------------------------------------------------------
# Timer trigger (add to function_app.py if needed)
# ---------------------------------------------------------------------------

def get_timer_trigger_function():
    """
    Returns an Azure Function timer trigger handler.
    Register in function_app.py:
        app.schedule(schedule="0 0 6 * * *")(daily_refresh_trigger)
    """
    import azure.functions as func

    def daily_refresh_trigger(timer: func.TimerRequest) -> None:
        logger.info("Timer trigger fired — running daily refresh.")
        try:
            run_daily_refresh()
        except Exception as e:
            logger.error(f"Daily refresh failed: {e}")

    return daily_refresh_trigger


# ---------------------------------------------------------------------------
# Manual run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = run_daily_refresh()
    print(f"Refresh complete. Health: {result.get('planningHealth')}, "
          f"Changed: {result.get('changedRecordCount')}/{result.get('totalRecords')}")
