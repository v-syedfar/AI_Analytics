"""
MCP Tool Schemas
Typed dataclasses representing structured inputs/outputs for each MCP tool.
These are the contracts between the analytics engine and the LLM layer.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class AnalyticsContext:
    """Output of analytics_context_tool — compressed facts for LLM consumption."""
    total_records: int
    matched_records: int
    new_records: int
    forecast_new: float
    forecast_old: float
    trend_delta: float
    trend_direction: str           # increasing | decreasing | stable | volatile
    quantity_changed_count: int
    supplier_changed_count: int
    design_changed_count: int
    roj_changed_count: int
    top_impacted_location: Optional[str]
    top_impacted_supplier: Optional[str]
    top_impacted_material: Optional[str]
    top_impacted_material_group: Optional[str]
    risk_level: str
    planning_health: int           # 0-100


@dataclass
class RiskSummary:
    """Output of risk_summary_tool."""
    highest_risk_level: str
    risk_breakdown: dict           # { "Design Change Risk": 3, ... }
    high_risk_count: int
    risk_drivers: List[str]        # ["design_changed", "supplier_changed"]
    affected_material_ids: List[str]


@dataclass
class RootCauseContext:
    """Output of root_cause_driver_tool."""
    primary_driver: str            # "quantity" | "supplier" | "design" | "schedule"
    primary_driver_count: int
    driver_location: Optional[str]
    driver_supplier: Optional[str]
    driver_material: Optional[str]
    driver_material_group: Optional[str]
    change_type_label: str         # human-readable e.g. "Quantity + Design"
    is_stable: bool


@dataclass
class RecommendationContext:
    """Output of recommendation_tool — deterministic candidate actions."""
    actions: List[str]


@dataclass
class NotificationPayload:
    """Future-ready notification tool schema."""
    severity: str                  # "high" | "medium" | "low"
    subject: str
    body: str
    target_location: Optional[str]
    target_supplier: Optional[str]
    recommended_actions: List[str] = field(default_factory=list)
