from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class PlanningRecord:
    # --- Matching keys ---
    location_id: str           # LOCID         - Location ID
    material_group: str        # GSCEQUIPCAT   - Equipment Category
    material_id: str           # PRDID         - Material ID

    # --- Tracked change fields ---
    supplier: Optional[str]            # LOCFR / LOCFRDESCR  - Supplier From / Supplier Description
    forecast_qty: Optional[float]      # GSCFSCTQTY (current) / GSCPREVFCSTQTY (previous)
    roj: Optional[str]                 # GSCCONROJDATE (current) / GSCPREVROJNBD (previous)
    bod: Optional[str]                 # ZCOIBODVER    - BOD Version
    ff: Optional[str]                  # ZCOIFORMFACT  - Form Factor

    # --- Context / enrichment fields ---
    roc_region: Optional[str] = None   # ROC           - ROC Region
    dc_site: Optional[str] = None      # ZCOIDCID      - Facility/DC/Site Name
    metro: Optional[str] = None        # ZCOIMETROID   - Planning Metro
    country: Optional[str] = None      # ZCOICOUNTRY   - Country
    supplier_date: Optional[str] = None        # GSCSUPLDATE   - Supplier Date
    prev_supplier_date: Optional[str] = None   # GSCPREVSUPLDATE - Previous Supplier Date
    planning_exception: Optional[str] = None   # ZGSCPLANNINGEXCEPTION - Planning Exception
    roj_reason_code: Optional[str] = None      # ZGSCROJDATEREASONCODE - ROJ Date Reason Code
    automation_reason: Optional[str] = None    # ZGSCAUTOMATIONREASON  - Automation Reason
    # --- Audit fields ---
    last_modified_by: Optional[str] = None     # LASTMODIFIEDBY  - User who last modified
    last_modified_date: Optional[str] = None   # LASTMODIFIEDDATE
    created_by: Optional[str] = None           # CREATEDBY
    created_date: Optional[str] = None         # CREATEDDATE

    # --- Pre-computed CSV flags (if present) ---
    is_new_demand: bool = False                # Is_New Demand
    is_cancelled: bool = False                 # Is_cancelled
    risk_flag: Optional[str] = None            # Risk_Flag
    fcst_delta_qty: Optional[float] = None     # FCST_Delta Qty
    nbd_delta_days: Optional[float] = None     # NBD_DeltaDays
    is_supplier_date_missing: bool = False     # Is_SupplierDateMissing

    @property
    def key(self) -> tuple:
        return (self.location_id, self.material_group, self.material_id)


@dataclass
class ComparedRecord:
    # --- Matching keys ---
    location_id: str
    material_group: str
    material_id: str

    # --- Tracked change fields (current vs previous) ---
    supplier_current: Optional[str]
    supplier_previous: Optional[str]
    forecast_qty_current: Optional[float]
    forecast_qty_previous: Optional[float]
    roj_current: Optional[str]
    roj_previous: Optional[str]
    bod_current: Optional[str]
    bod_previous: Optional[str]
    ff_current: Optional[str]
    ff_previous: Optional[str]

    # --- Context fields (from current row) ---
    roc_region: Optional[str] = None        # ROC           - ROC Region
    dc_site: Optional[str] = None           # ZCOIDCID      - Facility/DC/Site Name
    metro: Optional[str] = None             # ZCOIMETROID   - Planning Metro
    country: Optional[str] = None           # ZCOICOUNTRY   - Country
    supplier_date: Optional[str] = None     # GSCSUPLDATE   - Supplier Date
    planning_exception: Optional[str] = None  # ZGSCPLANNINGEXCEPTION
    roj_reason_code: Optional[str] = None   # ZGSCROJDATEREASONCODE
    automation_reason: Optional[str] = None # ZGSCAUTOMATIONREASON

    # --- Audit fields (from current row) ---
    last_modified_by: Optional[str] = None
    last_modified_date: Optional[str] = None

    # --- Derived analytics fields ---
    qty_changed: bool = False
    roj_changed: bool = False
    supplier_changed: bool = False
    design_changed: bool = False
    qty_delta: Optional[float] = None
    change_type: str = "Unchanged"
    risk_level: str = "Normal"

    # --- Enhanced flags ---
    is_new_demand: bool = False
    is_cancelled: bool = False
    risk_flag: Optional[str] = None
    fcst_delta_qty: Optional[float] = None
    nbd_delta_days: Optional[float] = None
    is_supplier_date_missing: bool = False
    bod_changed: bool = False
    ff_changed: bool = False


# ---------------------------------------------------------------------------
# Trend models
# ---------------------------------------------------------------------------

@dataclass
class SnapshotPoint:
    """One material record at a specific point in time."""
    snapshot_date: str              # supplied by Power Automate (sheet pull date)
    forecast_qty: Optional[float]
    roj: Optional[str]
    supplier: Optional[str]
    bod: Optional[str]
    ff: Optional[str]
    last_modified_by: Optional[str]
    last_modified_date: Optional[str]


@dataclass
class TrendRecord:
    """Multi-snapshot trend analysis for a single material key."""
    location_id: str
    material_group: str
    material_id: str

    # Ordered oldest -> newest
    snapshots: List[SnapshotPoint] = field(default_factory=list)

    # --- Derived trend fields ---
    qty_trend: str = "stable"           # increasing | decreasing | volatile | stable
    change_streak: int = 0              # consecutive snapshots with any change
    changed_snapshot_count: int = 0     # total snapshots where something changed
    is_recurring: bool = False          # changed in >= recurring_threshold snapshots
    is_one_off_spike: bool = False      # spiked exactly once, stable otherwise
    spike_dates: List[str] = field(default_factory=list)
    consistently_increasing: bool = False
    consistently_decreasing: bool = False
    qty_values: List[Optional[float]] = field(default_factory=list)
    snapshot_dates: List[str] = field(default_factory=list)
