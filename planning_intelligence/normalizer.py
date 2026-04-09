from typing import Any, Optional
from models import PlanningRecord

# ---------------------------------------------------------------------------
# Column reference (full dataset mapping)
# ---------------------------------------------------------------------------
# LOCID              -> location_id          (Location ID)
# PRDID              -> material_id          (Material ID)
# GSCEQUIPCAT        -> material_group       (Equipment Category)
# LOCFR              -> supplier             (Supplier From)
# LOCFRDESCR         -> supplier (fallback)  (Supplier Description)
# GSCFSCTQTY         -> forecast_qty         (Forecast Quantity - current)
# GSCPREVFCSTQTY     -> forecast_qty         (Previous Forecast Quantity)
# GSCCONROJDATE      -> roj                  (ROJ Need by Date - current)
# GSCPREVROJNBD      -> roj                  (Previous ROJ Need By Date)
# ZCOIBODVER         -> bod                  (BOD Version)
# ZCOIFORMFACT       -> ff                   (Form Factor)
# ROC                -> roc_region           (ROC Region)
# ZCOIDCID           -> dc_site              (Facility/DC/Site Name)
# ZCOIMETROID        -> metro                (Planning Metro)
# ZCOICOUNTRY        -> country              (Country)
# GSCSUPLDATE        -> supplier_date        (Supplier Date)
# GSCPREVSUPLDATE    -> prev_supplier_date   (Previous Supplier Date)
# ZGSCPLANNINGEXCEPTION -> planning_exception
# ZGSCROJDATEREASONCODE -> roj_reason_code   (ROJ Date Reason Code)
# LASTMODIFIEDBY    -> last_modified_by     (User who last modified)
# LASTMODIFIEDDATE  -> last_modified_date
# CREATEDBY         -> created_by
# CREATEDDATE       -> created_date
# ---------------------------------------------------------------------------


def _safe_str(val: Any) -> Optional[str]:
    if val is None or str(val).strip() in ("", "None", "nan"):
        return None
    return str(val).strip()


def _safe_float(val: Any) -> Optional[float]:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_bool(val: Any) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("true", "1", "yes", "y")


def normalize_row(raw: dict, is_current: bool = True) -> PlanningRecord:
    """
    Normalize a raw Excel row dict into a PlanningRecord.
    is_current=True  -> reads GSCFSCTQTY / GSCCONROJDATE
    is_current=False -> reads GSCPREVFCSTQTY / GSCPREVROJNBD
    """
    supplier = _safe_str(raw.get("LOCFR")) or _safe_str(raw.get("LOCFRDESCR"))

    if is_current:
        forecast_qty = _safe_float(raw.get("GSCFSCTQTY"))
        roj = _safe_str(raw.get("GSCCONROJDATE"))
    else:
        forecast_qty = _safe_float(raw.get("GSCPREVFCSTQTY"))
        roj = _safe_str(raw.get("GSCPREVROJNBD"))

    return PlanningRecord(
        # Matching keys
        location_id=_safe_str(raw.get("LOCID")) or "",
        material_group=_safe_str(raw.get("GSCEQUIPCAT")) or "",
        material_id=_safe_str(raw.get("PRDID")) or "",
        # Tracked change fields
        supplier=supplier,
        forecast_qty=forecast_qty,
        roj=roj,
        bod=_safe_str(raw.get("ZCOIBODVER")),
        ff=_safe_str(raw.get("ZCOIFORMFACT")),
        # Context / enrichment fields
        roc_region=_safe_str(raw.get("ROC")),
        dc_site=_safe_str(raw.get("ZCOIDCID")),
        metro=_safe_str(raw.get("ZCOIMETROID")),
        country=_safe_str(raw.get("ZCOICOUNTRY")),
        supplier_date=_safe_str(raw.get("GSCSUPLDATE")),
        prev_supplier_date=_safe_str(raw.get("GSCPREVSUPLDATE")),
        planning_exception=_safe_str(raw.get("ZGSCPLANNINGEXCEPTION")),
        roj_reason_code=_safe_str(raw.get("ZGSCROJDATEREASONCODE")),
        automation_reason=_safe_str(raw.get("ZGSCAUTOMATIONREASON")),
        # Audit fields
        last_modified_by=_safe_str(raw.get("LASTMODIFIEDBY")),
        last_modified_date=_safe_str(raw.get("LASTMODIFIEDDATE")),
        created_by=_safe_str(raw.get("CREATEDBY")),
        created_date=_safe_str(raw.get("CREATEDDATE")),
        # Pre-computed CSV flags
        is_new_demand=_safe_bool(raw.get("IS_NEW DEMAND") or raw.get("IS_NEW_DEMAND")),
        is_cancelled=_safe_bool(raw.get("IS_CANCELLED")),
        risk_flag=_safe_str(raw.get("RISK_FLAG")),
        fcst_delta_qty=_safe_float(raw.get("FCST_DELTA QTY") or raw.get("FCST_DELTA_QTY")),
        nbd_delta_days=_safe_float(raw.get("NBD_DELTADAYS")),
        is_supplier_date_missing=_safe_bool(raw.get("IS_SUPPLIERDATEMISSING")),
    )


def normalize_rows(rows: list[dict], is_current: bool = True) -> list[PlanningRecord]:
    return [normalize_row(r, is_current) for r in rows]
