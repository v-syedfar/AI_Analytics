# Implementation Plan: Dashboard Enhancements

## Overview

Incremental implementation of five enhancement areas: backend debug/explain endpoints, frontend type additions, validation layer, Tooltip component, KPI card tooltip integration, CopilotPanel, and DashboardPage UX polish.

## Tasks

- [ ] 1. Add TypeScript type definitions
  - [ ] 1.1 Add `DashboardContext`, `ExplainRequest`, `ExplainResponse`, and `DebugSnapshotResponse` interfaces to `frontend/src/types/dashboard.ts`
    - Add after existing interfaces; reuse existing `HealthStatus`, `TrendDirection`, `RiskLevel`, `DataMode`, `AlertPayload` types
    - _Requirements: 3.6, 4.1, 4.3, 1.1_

- [ ] 2. Update `frontend/src/services/api.ts`
  - [ ] 2.1 Update `fetchExplain` to accept an optional `context: Partial<DashboardContext>` parameter and include it in the POST body
    - _Requirements: 4.1, 4.2, 3.6_
  - [ ] 2.2 Add `fetchDebugSnapshot(params?)` function that POSTs to `/api/debug-snapshot` and returns `DebugSnapshotResponse`
    - Accept optional `{ mode?, location_id?, material_group? }` params
    - _Requirements: 1.1_

- [ ] 3. Implement `validateDashboardResponse` in `frontend/src/services/validation.ts`
  - [ ] 3.1 Create `frontend/src/services/validation.ts` with the pure `validateDashboardResponse(data: unknown): data is DashboardResponse` function
    - Check all required fields: `dataMode`, `planningHealth`, `status`, `forecastNew`, `forecastOld`, `trendDirection`, `trendDelta`, `totalRecords`, `changedRecordCount`, `riskSummary`, `aiInsight`, `rootCause`, `recommendedActions`, `drivers`, `alerts`, `filters`
    - Log `console.warn` for each missing/mismatched field; never throw; never mutate
    - _Requirements: 6.4, 6.5_
  - [ ]* 3.2 Write property tests for `validateDashboardResponse` in `frontend/src/services/__tests__/validation.test.ts`
    - **Property 11: validateDashboardResponse purity and correctness**
    - **Validates: Requirements 6.4, 6.5**

- [ ] 4. Implement `Tooltip` component in `frontend/src/components/Tooltip.tsx`
  - [ ] 4.1 Create `Tooltip.tsx` with `TooltipProps { content: React.ReactNode; children: React.ReactNode }`
    - Desktop: show on `onMouseEnter`/`onMouseLeave`; touch: render ⓘ icon button that toggles visibility
    - Positioning: absolute, above by default, flips below if near viewport top
    - Styling: `bg-[#161b22]`, `border border-white/10`, `text-[#e6edf3]`, `rounded-lg`, `p-3`, `z-50`, `max-w-xs`
    - Transition: `opacity` + `translateY`, max 300ms
    - Render `"N/A"` for any null/undefined field in content
    - _Requirements: 2.9, 2.10, 2.12, 2.13_
  - [ ]* 4.2 Write property tests for Tooltip in `frontend/src/components/__tests__/Tooltip.test.tsx`
    - **Property 2: KPI card tooltip content completeness**
    - **Property 3: Tooltip content is data-driven**
    - **Property 4: Tooltip null field fallback**
    - **Validates: Requirements 2.1–2.8, 2.11, 2.12**

- [ ] 5. Implement `CopilotPanel` component in `frontend/src/components/CopilotPanel.tsx`
  - [ ] 5.1 Create `CopilotPanel.tsx` with props `{ isOpen, onClose, context: DashboardContext }`
    - Local state: `messages: ChatMessage[]`, `input: string`, `loading: boolean`, `error: string | null`
    - On open: initialize messages with one greeting assistant message referencing `planningHealth`, `status`, `changedRecordCount`, `riskSummary.level`, and first 120 chars of `aiInsight`
    - Render scrollable message list, 4 starter prompt chips (use `buildStarterPrompts`), textarea input, Send button
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [ ] 5.2 Implement message submission logic in `CopilotPanel.tsx`
    - Enter (no Shift) submits; Shift+Enter inserts newline
    - POST to `/explain` via `fetchExplain` with `question` and `context`; 6-second timeout
    - On success: append assistant `ChatMessage`; on timeout: show timeout message, preserve input; on error: construct fallback from `context.aiInsight`, `context.rootCause`, `context.recommendedActions`
    - _Requirements: 3.6, 3.7, 3.8, 3.9, 3.10_
  - [ ] 5.3 Implement panel layout and close behavior in `CopilotPanel.tsx`
    - Right-side drawer; on screens ≥ 1024px push layout (`pr-[400px]` on `<main>`); overlay on smaller screens
    - Close button (×) hides panel without clearing message history
    - Dark theme styling consistent with dashboard
    - _Requirements: 3.11, 3.12_
  - [ ]* 5.4 Write property tests for `CopilotPanel` in `frontend/src/components/__tests__/CopilotPanel.test.tsx`
    - **Property 5: CopilotPanel initial state**
    - **Property 6: CopilotPanel message history growth**
    - **Property 7: CopilotPanel history preserved on close**
    - **Property 8: CopilotPanel sends context with every question**
    - **Validates: Requirements 3.2–3.4, 3.6, 3.8, 3.11**

- [ ] 6. Checkpoint — Ensure all frontend component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Update `DashboardPage.tsx` — validation, state, and context wiring
  - [ ] 7.1 Call `validateDashboardResponse` after API response and before setting state; add null/empty guard that shows "No planning data available" empty state
    - Import from `../services/validation`
    - _Requirements: 6.4, 6.5, 6.6_
  - [ ] 7.2 Replace spinner with skeleton loading state using three `animate-pulse bg-gray-800` placeholder cards
    - _Requirements: 5.1_
  - [ ] 7.3 Add empty state: when `data.totalRecords === 0`, render centered "No planning records available for the selected filters." in place of KPI cards
    - _Requirements: 5.2_
  - [ ] 7.4 Add `lastRefreshedAt` display in dashboard header using `toLocaleString()`; show "Refresh pending" when null/undefined
    - _Requirements: 5.5, 5.6_
  - [ ] 7.5 Add `copilotOpen` state; wire "Ask Copilot" button in `ActionsPanel` to toggle it; add highlighted border (`border-blue-400`) on the button when panel is open; add `pr-[400px]` to `<main>` when panel open on ≥ 1024px
    - _Requirements: 3.1, 3.12, 3.13_
  - [ ] 7.6 Render `<CopilotPanel>` with `isOpen`, `onClose`, and `context` (derived from current `data` state as `DashboardContext`)
    - _Requirements: 3.1, 3.6_

- [ ] 8. Wrap KPI cards with Tooltip in `DashboardPage.tsx`
  - [ ] 8.1 Wrap `PlanningHealthCard` with `<Tooltip>` — content: score, status band + threshold, changed%, highest risk level, design count, supplier count, dominant deduction factor
    - _Requirements: 2.1, 2.2_
  - [ ] 8.2 Wrap `ForecastCard` with `<Tooltip>` — content: `forecastNew`, `forecastOld`, `trendDelta`, `trendDirection`
    - _Requirements: 2.1, 2.3_
  - [ ] 8.3 Wrap `SummaryTiles` Changed tile with `<Tooltip>` — content: `changedRecordCount`, `totalRecords`, changed%
    - _Requirements: 2.1, 2.4_
  - [ ] 8.4 Wrap `RiskCard` with `<Tooltip>` — content: `highestRiskLevel`, `highRiskCount`, `riskBreakdown` entries
    - _Requirements: 2.1, 2.5_
  - [ ] 8.5 Wrap `AIInsightCard` with `<Tooltip>` — content: primary evidence from non-null signals (`drivers`, `trendDirection`, `riskSummary.level`, changed ratio)
    - _Requirements: 2.1, 2.6_
  - [ ] 8.6 Wrap `RootCauseCard` with `<Tooltip>` — content: `drivers.changeType`, `drivers.location`, `drivers.supplier`, `drivers.materialGroup`, `trendDirection`
    - _Requirements: 2.1, 2.7_
  - [ ] 8.7 Wrap `AlertBanner` with `<Tooltip>` — content: `alerts.severity`, `alerts.triggerType`, `alerts.recommendedAction`
    - _Requirements: 2.1, 2.8_
  - [ ] 8.8 Add KPI card hover border transition: `transition-colors duration-150 hover:border-[rgba(88,166,255,0.4)]` on each card wrapper
    - _Requirements: 5.4_
  - [ ]* 8.9 Write property tests for null-safe rendering and timestamp display in `frontend/src/pages/__tests__/DashboardPage.test.tsx`
    - **Property 12: Null-safe rendering with incomplete responses**
    - **Property 13: Timestamp display**
    - **Validates: Requirements 5.5, 5.6, 6.2, 6.3**

- [ ] 9. Add `DebugPanel` inline in `DashboardPage.tsx`
  - [ ] 9.1 Implement `DebugPanel` as an inline component rendered only when `process.env.REACT_APP_DEBUG_MODE === "true"`
    - Fixed overlay, bottom-right, collapsible toggle
    - Section 1: raw JSON viewer for fields: `planningHealth`, `forecastNew`, `forecastOld`, `trendDelta`, `trendDirection`, `changedRecordCount`, `totalRecords`, `riskSummary`, `dataMode`, `lastRefreshedAt`
    - Section 2: static card-to-field mapping table (per design)
    - Section 3: calculation trace — HealthScore deductions, changed%, risk level derivation
    - Section 4: "Copy JSON" button (clipboard API; show error toast if unavailable)
    - _Requirements: 1.2, 1.3, 1.4, 1.6, 1.7_

- [ ] 10. Implement `/api/debug-snapshot` backend endpoint
  - [ ] 10.1 Add `debug_snapshot` Azure Function route in `planning_intelligence/function_app.py`
    - Accept POST with optional body `{ mode, location_id, material_group }`
    - Call `normalize_rows → filter_records → compare_records` capturing intermediate counts
    - Call `_compute_health_score` and capture `healthScoreInputs`
    - Return `DebugSnapshotResponse` JSON; handle blob load failure (HTTP 500), live mode missing `current_rows` (HTTP 400)
    - _Requirements: 1.1_
  - [ ] 10.2 Add inline comment block in `response_builder.py` documenting each `_compute_health_score` deduction step and its maximum impact
    - _Requirements: 1.5_
  - [ ]* 10.3 Write property tests for `/debug-snapshot` in `planning_intelligence/tests/test_debug_snapshot.py`
    - **Property 1: Debug snapshot response completeness**
    - **Validates: Requirements 1.1**

- [ ] 11. Update `/api/explain` backend endpoint
  - [ ] 11.1 Update the `explain` route in `planning_intelligence/function_app.py` to accept optional `context` in the request body
    - When `context` provided: use its values to ground the answer; skip snapshot re-fetch
    - When `context` absent and `mode: "cached"`: fall back to snapshot load (existing behavior)
    - Validate `question` is non-empty string; return HTTP 400 `{"error": "question is required"}` otherwise
    - _Requirements: 4.1, 4.2, 4.5, 4.6, 4.8_
  - [ ] 11.2 Update the `explain` route response to include `supportingMetrics` and `contextUsed` fields
    - `supportingMetrics`: `{ changedRecordCount, totalRecords, trendDelta, planningHealth }`
    - `contextUsed`: list of context field names actually used to generate the answer
    - _Requirements: 4.3, 4.4_
  - [ ]* 11.3 Write property tests for `/explain` in `planning_intelligence/tests/test_explain_endpoint.py`
    - **Property 9: Explain endpoint response contract**
    - **Property 10: Explain endpoint backward compatibility**
    - **Validates: Requirements 4.1–4.4, 4.8**

- [ ] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use `fast-check` (frontend) and `hypothesis` (backend)
- Tasks 1–9 are frontend-only; tasks 10–11 are backend-only; they can be worked in parallel
