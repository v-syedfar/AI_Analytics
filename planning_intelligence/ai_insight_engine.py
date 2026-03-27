"""
AI Insight Engine
Orchestrates MCP tools → builds LLM prompt → calls Azure OpenAI → returns insights.
Falls back to deterministic logic if LLM is unavailable or fails.
"""
import json
import logging
import os
from dataclasses import asdict
from typing import Optional

from mcp.schemas import AnalyticsContext, RiskSummary, RootCauseContext, RecommendationContext

logger = logging.getLogger(__name__)

# Azure OpenAI config — set these in Azure Function App Settings
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
LLM_TIMEOUT = int(os.environ.get("LLM_TIMEOUT_SECONDS", "10"))

SYSTEM_PROMPT = """You are a supply chain planning intelligence expert.
Analyze the structured planning analytics context below and generate:
1. AI Insight
2. Root Cause
3. Recommended Actions

Rules:
- Only use provided context. Do not hallucinate.
- Be concise, executive-friendly, and business-focused.
- Identify the primary driver of change.
- State whether the change is demand-driven, supplier-driven, design-driven, or schedule-driven.
- Mention location, material group, or supplier only when supported by context.
- Mention stability explicitly if changes are insignificant.
- Mention risk only if supported by structured analytics.
- Recommendations must be actionable and aligned with observed signals.

Return ONLY valid JSON in this exact format:
{
  "aiInsight": "...",
  "rootCause": "...",
  "recommendedActions": ["...", "...", "..."]
}"""


def generate_insights(
    ctx: AnalyticsContext,
    risk: RiskSummary,
    root_cause: RootCauseContext,
    recommendations: RecommendationContext,
) -> dict:
    """
    Main entry point. Applies guardrails first, then attempts LLM.
    Falls back to deterministic if LLM fails or is not configured.
    """
    # Phase 4: Guardrails — skip LLM for stable/trivial cases
    guardrail_result = _apply_guardrails(ctx, risk, root_cause)
    if guardrail_result:
        logger.info("Guardrail triggered — skipping LLM call.")
        return guardrail_result

    # Attempt LLM
    if AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY:
        try:
            return _call_llm(ctx, risk, root_cause, recommendations)
        except Exception as e:
            logger.warning(f"LLM call failed: {e}. Falling back to deterministic.")

    # Fallback
    return _deterministic_fallback(ctx, risk, root_cause, recommendations)


# ---------------------------------------------------------------------------
# Phase 4: Guardrails
# ---------------------------------------------------------------------------

def _apply_guardrails(
    ctx: AnalyticsContext,
    risk: RiskSummary,
    root_cause: RootCauseContext,
) -> Optional[dict]:
    """Returns deterministic insight if the situation is simple enough."""

    # Fully stable
    if root_cause.is_stable:
        return {
            "aiInsight": "Demand remains stable across planning versions with no significant changes detected.",
            "rootCause": "No changes were identified in quantity, supplier, design, or schedule fields.",
            "recommendedActions": ["No immediate actions required. Continue monitoring planning cycle."],
        }

    # Only quantity changed
    if (ctx.quantity_changed_count > 0 and
            ctx.supplier_changed_count == 0 and
            ctx.design_changed_count == 0 and
            ctx.roj_changed_count == 0):
        direction = "increased" if ctx.trend_delta > 0 else "decreased"
        loc = f" at {ctx.top_impacted_location}" if ctx.top_impacted_location else ""
        return {
            "aiInsight": f"Forecast quantities have {direction} by {abs(ctx.trend_delta):,.0f} units{loc}. No supplier, design, or schedule changes detected.",
            "rootCause": f"Change is purely quantity-driven. {ctx.quantity_changed_count} record(s) show forecast adjustments.",
            "recommendedActions": [
                f"Review quantity adjustments{loc} to confirm alignment with demand plan.",
                "No supplier or design actions required at this time.",
            ],
        }

    # Only supplier changed
    if (ctx.supplier_changed_count > 0 and
            ctx.quantity_changed_count == 0 and
            ctx.design_changed_count == 0 and
            ctx.roj_changed_count == 0):
        supplier = f" involving {ctx.top_impacted_supplier}" if ctx.top_impacted_supplier else ""
        return {
            "aiInsight": f"Supplier changes detected{supplier} with no quantity or design impact.",
            "rootCause": f"Change is supplier-driven. {ctx.supplier_changed_count} record(s) show supplier transitions.",
            "recommendedActions": [
                f"Validate supplier transition plan{supplier} to avoid supply disruption.",
                "Confirm new supplier lead times and pricing.",
            ],
        }

    # Only schedule changed
    if (ctx.roj_changed_count > 0 and
            ctx.quantity_changed_count == 0 and
            ctx.supplier_changed_count == 0 and
            ctx.design_changed_count == 0):
        return {
            "aiInsight": f"Schedule (ROJ) changes detected across {ctx.roj_changed_count} record(s). No quantity, supplier, or design changes.",
            "rootCause": "Change is schedule-driven. ROJ need-by dates have shifted.",
            "recommendedActions": [
                "Review ROJ date shifts with supply chain team to assess delivery risk.",
                "Confirm updated delivery commitments with affected suppliers.",
            ],
        }

    return None  # proceed to LLM


# ---------------------------------------------------------------------------
# LLM Call
# ---------------------------------------------------------------------------

def _call_llm(
    ctx: AnalyticsContext,
    risk: RiskSummary,
    root_cause: RootCauseContext,
    recommendations: RecommendationContext,
) -> dict:
    """Calls Azure OpenAI with structured context. Returns parsed JSON."""
    try:
        from openai import AzureOpenAI
    except ImportError:
        raise RuntimeError("openai package not installed. Add openai to requirements.txt.")

    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        timeout=LLM_TIMEOUT,
    )

    user_message = _build_prompt(ctx, risk, root_cause, recommendations)

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    # Validate expected keys
    for key in ("aiInsight", "rootCause", "recommendedActions"):
        if key not in parsed:
            raise ValueError(f"LLM response missing key: {key}")

    return parsed


def _build_prompt(ctx, risk, root_cause, recommendations) -> str:
    return f"""Planning Analytics Context:

FORECAST:
- Current: {ctx.forecast_new:,.0f} units
- Previous: {ctx.forecast_old:,.0f} units
- Delta: {ctx.trend_delta:+,.0f} units
- Trend: {ctx.trend_direction}

RECORDS:
- Total: {ctx.total_records}
- Changed: {ctx.quantity_changed_count + ctx.supplier_changed_count + ctx.design_changed_count + ctx.roj_changed_count}
- New (no baseline): {ctx.new_records}

CHANGE DRIVERS:
- Quantity changes: {ctx.quantity_changed_count}
- Supplier changes: {ctx.supplier_changed_count}
- Design changes (BOD/FF): {ctx.design_changed_count}
- Schedule (ROJ) changes: {ctx.roj_changed_count}

TOP IMPACTED:
- Location: {ctx.top_impacted_location or 'N/A'}
- Supplier: {ctx.top_impacted_supplier or 'N/A'}
- Material: {ctx.top_impacted_material or 'N/A'}
- Material Group: {ctx.top_impacted_material_group or 'N/A'}

RISK:
- Highest risk level: {risk.highest_risk_level}
- High risk record count: {risk.high_risk_count}
- Risk breakdown: {json.dumps(risk.risk_breakdown)}

ROOT CAUSE:
- Primary driver: {root_cause.primary_driver}
- Change type: {root_cause.change_type_label}
- Is stable: {root_cause.is_stable}

PLANNING HEALTH: {ctx.planning_health}/100

DETERMINISTIC RECOMMENDATIONS (use as baseline):
{json.dumps(recommendations.actions, indent=2)}

Generate aiInsight, rootCause, and recommendedActions as JSON."""


# ---------------------------------------------------------------------------
# Deterministic Fallback
# ---------------------------------------------------------------------------

def _deterministic_fallback(
    ctx: AnalyticsContext,
    risk: RiskSummary,
    root_cause: RootCauseContext,
    recommendations: RecommendationContext,
) -> dict:
    """Full deterministic narrative when LLM is unavailable."""
    parts = []
    # Use matched_records as the changed count proxy — driver counts can overlap
    total_changed = ctx.total_records - (ctx.total_records - ctx.matched_records)
    # Simpler: derive from non-zero drivers, capped at total
    driver_max = max(
        ctx.quantity_changed_count,
        ctx.supplier_changed_count,
        ctx.design_changed_count,
        ctx.roj_changed_count,
    )
    total_changed = min(driver_max, ctx.total_records)
    pct = round(total_changed / ctx.total_records * 100, 1) if ctx.total_records else 0

    parts.append(f"{pct}% of records changed this planning cycle ({total_changed} of {ctx.total_records}).")

    if ctx.trend_direction == "increasing":
        parts.append(f"Forecast demand is trending upward (+{ctx.trend_delta:,.0f} units).")
    elif ctx.trend_direction == "decreasing":
        parts.append(f"Forecast demand is trending downward ({ctx.trend_delta:,.0f} units).")

    drivers = []
    if ctx.quantity_changed_count: drivers.append(f"{ctx.quantity_changed_count} quantity")
    if ctx.supplier_changed_count: drivers.append(f"{ctx.supplier_changed_count} supplier")
    if ctx.design_changed_count: drivers.append(f"{ctx.design_changed_count} design")
    if ctx.roj_changed_count: drivers.append(f"{ctx.roj_changed_count} schedule")
    if drivers:
        parts.append("Key drivers: " + ", ".join(drivers) + ".")

    if ctx.top_impacted_location:
        parts.append(f"Location {ctx.top_impacted_location} has the highest change concentration.")
    if risk.highest_risk_level != "Normal":
        parts.append(f"Risk level: {risk.highest_risk_level}.")

    root = (
        f"Primary driver is {root_cause.primary_driver} "
        f"({root_cause.primary_driver_count} records). "
        f"Change type: {root_cause.change_type_label}."
    )
    if ctx.top_impacted_location:
        root += f" Location {ctx.top_impacted_location} is the main source."

    return {
        "aiInsight": " ".join(parts),
        "rootCause": root,
        "recommendedActions": recommendations.actions,
    }
