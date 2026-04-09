# Requirements Document

## Introduction

This feature enhances the Planning Intelligence dashboard across five areas: end-to-end data validation, dynamic KPI tooltips, a real Copilot chat side panel, improved backend Q&A support in the `/explain` endpoint, and general UX polish. The existing architecture (React TypeScript frontend, Azure Functions Python backend, Tailwind CSS, blob-based daily refresh) is preserved and extended.

## Glossary

- **Dashboard**: The Planning Intelligence React UI served from `frontend/`.
- **DashboardResponse**: The TypeScript interface representing the full JSON payload returned by `/planning-dashboard-v2`.
- **KPI Card**: Any of the major metric display components: PlanningHealthCard, ForecastCard, TrendCard, SummaryTiles, AIInsightCard, RootCauseCard, RiskCard, AlertBanner.
- **Tooltip**: A contextual hover overlay (or tap-accessible info icon on touch devices) that displays data-driven explanatory text for a KPI Card.
- **CopilotPanel**: The new side-panel chat component that replaces the `alert("Opening Copilot Studio...")` call.
- **ExplainEndpoint**: The Azure Function at route `explain` (`POST /api/explain`).
- **DashboardContext**: The subset of `DashboardResponse` fields sent to the ExplainEndpoint as grounding context: `planningHealth`, `status`, `forecastNew`, `forecastOld`, `trendDelta`, `trendDirection`, `changedRecordCount`, `totalRecords`, `riskSummary`, `aiInsight`, `rootCause`, `alerts`, `drivers`, `filters`, `dataMode`, `lastRefreshedAt`.
- **DebugPanel**: A collapsible UI overlay that displays raw computed values, UI field mappings, and calculation traces for validation purposes.
- **ValidationMode**: A runtime flag (`REACT_APP_DEBUG_MODE=true`) that enables the DebugPanel.
- **AnalyticsPipeline**: The Python processing chain: `blob_loader → normalizer → filters → comparator → analytics → response_builder`.
- **HealthScore**: The integer 0–100 computed by `_compute_health_score` in `response_builder.py`.
- **ChatMessage**: A single turn in the CopilotPanel conversation, with a `role` ("user" | "assistant") and `content` string.
- **StarterPrompt**: A predefined clickable question in the CopilotPanel derived from current dashboard context.
- **SupportingMetrics**: A structured object in the ExplainEndpoint response containing key numeric values used to ground the answer.
- **ContextUsed**: A field in the ExplainEndpoint response indicating which context fields were used to generate the answer.

---

## Requirements

### Requirement 1: End-to-End Data Validation

**User Story:** As a developer, I want to verify that every dashboard value is computed correctly from source data through the analytics pipeline to the UI, so that I can trust the numbers shown to planners.

#### Acceptance Criteria

<!-- UPDATED: debug-snapshot now supports POST with context parameters (mode, filters) -->
1. THE AnalyticsPipeline SHALL expose a `/debug-snapshot` endpoint (POST) that accepts an optional request body with `mode` (cached / live / blob), `location_id`, and `material_group` parameters, and returns raw intermediate values for the requested analysis scope: normalized record count, filtered record count, compared record count, changed record count, HealthScore inputs (total, changed, risk counts, design count, supplier count), and the final `DashboardResponse` fields.
2. WHEN `REACT_APP_DEBUG_MODE` is set to `"true"`, THE Dashboard SHALL render a DebugPanel overlay showing the raw `DashboardResponse` JSON fields: `planningHealth`, `forecastNew`, `forecastOld`, `trendDelta`, `trendDirection`, `changedRecordCount`, `totalRecords`, `riskSummary`, `dataMode`, and `lastRefreshedAt`.
3. THE DebugPanel SHALL be collapsible and SHALL NOT obscure primary dashboard content when expanded.
4. WHEN the DebugPanel is open, THE Dashboard SHALL display a "Copy JSON" button that copies the full raw `DashboardResponse` to the clipboard.
5. THE HealthScore computation SHALL be documented inline in `response_builder.py` with a comment block explaining each deduction step and its maximum impact.
6. IF `REACT_APP_DEBUG_MODE` is not set to `"true"`, THEN THE Dashboard SHALL NOT render the DebugPanel.
<!-- UPDATED: DebugPanel now shows card-to-field mapping and calculation trace per KPI -->
7. WHEN the DebugPanel is open, THE DebugPanel SHALL display a card-to-field mapping table showing which backend response field drives each UI card, and a calculation breakdown for major KPIs (HealthScore deductions, changed record percentage, risk level derivation).

---

### Requirement 2: Dynamic KPI Tooltips

**User Story:** As a planner, I want to hover over any KPI card and see a contextual explanation of what the value means and how it was derived, so that I can interpret the data without needing external documentation.

#### Acceptance Criteria

1. THE Dashboard SHALL render a Tooltip component on hover for each of the following KPI Cards: PlanningHealthCard, ForecastCard, TrendCard, SummaryTiles (Changed tile), RiskCard, AIInsightCard, RootCauseCard, and AlertBanner.
<!-- UPDATED: PlanningHealth tooltip now includes score band meaning, threshold explanation, and dominant factors -->
2. WHEN a user hovers over the PlanningHealthCard, THE Tooltip SHALL display: the current score, the status band label (Critical / Stable / Healthy) with its threshold range, the percentage of records changed, the highest risk level, design change count, supplier change count, and the dominant contributing factor that caused the most score deduction.
3. WHEN a user hovers over the ForecastCard, THE Tooltip SHALL display the current forecast quantity, the previous forecast quantity, the delta value, and the trend direction label.
4. WHEN a user hovers over the Changed tile in SummaryTiles, THE Tooltip SHALL display the changed record count, the total record count, and the percentage of records changed.
5. WHEN a user hovers over the RiskCard, THE Tooltip SHALL display the highest risk level, the high risk record count, and the per-category risk breakdown counts.
<!-- UPDATED: AIInsight tooltip now uses any available evidence, not limited to drivers field -->
6. WHEN a user hovers over the AIInsightCard, THE Tooltip SHALL display the primary evidence used in generating the insight, drawing from any available signals including: `drivers` (location, supplier, material group), trend direction, risk level, and changed record ratio — whichever fields are non-null in the current `DashboardResponse`.
<!-- UPDATED: RootCause tooltip now includes location, supplier, material group, and trend signal -->
7. WHEN a user hovers over the RootCauseCard, THE Tooltip SHALL display: the primary driver type from `drivers.changeType`, the top impacted location from `drivers.location`, the top impacted supplier from `drivers.supplier`, the top impacted material group from `drivers.materialGroup`, and the trend direction if available.
8. WHEN a user hovers over the AlertBanner, THE Tooltip SHALL display the alert severity, trigger type, and recommended action.
9. THE Tooltip component SHALL use the dark theme color palette (background `#161b22`, border `rgba(255,255,255,0.1)`, text `#e6edf3`) consistent with the existing dashboard theme.
<!-- UPDATED: Replaced rigid ms timing with smooth responsive behavior requirement -->
10. THE Tooltip SHALL appear and disappear with smooth, responsive transitions that do not feel laggy or abrupt; exact timing may be tuned per component but SHALL NOT exceed 300ms for appearance.
11. THE Tooltip SHALL NOT display hardcoded placeholder text; all content SHALL be derived from the live `DashboardResponse` data passed as props.
12. IF a required data field for a Tooltip is null or undefined, THEN THE Tooltip SHALL display "N/A" for that field rather than crashing or showing an empty string.
<!-- NEW: Mobile / touch device support -->
13. ON touch devices where hover is unavailable, THE Tooltip SHALL be accessible via a tap on an info icon (ⓘ) displayed adjacent to the KPI value, providing equivalent tooltip content.

---

### Requirement 3: Copilot Chat Side Panel

**User Story:** As a planner, I want to open a chat panel and ask questions about the current dashboard data, so that I can get grounded, context-aware answers without leaving the dashboard.

#### Acceptance Criteria

1. WHEN a user clicks "Ask Copilot" in the ActionsPanel, THE Dashboard SHALL open the CopilotPanel as a right-side drawer without navigating away from the dashboard.
2. THE CopilotPanel SHALL display a scrollable message history of ChatMessages.
3. WHEN the CopilotPanel opens, THE CopilotPanel SHALL display an initial assistant message that summarizes the current DashboardContext (planningHealth score, status, changedRecordCount, riskSummary level, and a one-line aiInsight excerpt).
<!-- NEW: Starter prompts derived from current context -->
4. WHEN the CopilotPanel opens, THE CopilotPanel SHALL display clickable StarterPrompts derived from the current dashboard context. StarterPrompts SHALL include at minimum: "Why is planning health critical?", "What changed most?", "What should the planner do next?", and one location-specific prompt if `drivers.location` is non-null (e.g., "Why is [location] driving the most changes?").
5. THE CopilotPanel SHALL render a text input field and a "Send" button at the bottom of the panel.
6. WHEN a user submits a question (via button or Enter key without Shift), THE CopilotPanel SHALL send a POST request to the ExplainEndpoint with the question text and the current DashboardContext as the `context` field.
7. WHILE a response is pending from the ExplainEndpoint, THE CopilotPanel SHALL display a loading indicator in the message list.
8. WHEN the ExplainEndpoint returns a response, THE CopilotPanel SHALL append the assistant's answer as a new ChatMessage in the message history.
<!-- UPDATED: Fallback to client-side explanation if backend unavailable -->
9. IF the ExplainEndpoint returns an error or is unreachable, THEN THE CopilotPanel SHALL provide a degraded but functional response using the local DashboardContext, constructing a plain-language answer from available fields (aiInsight, rootCause, recommendedActions) rather than showing only an error message.
<!-- NEW: Timeout handling -->
10. IF the ExplainEndpoint does not respond within 6 seconds, THE CopilotPanel SHALL display a timeout message, preserve the user's input in the text field, and allow the user to retry.
11. THE CopilotPanel SHALL include a close button (×) that dismisses the panel without clearing the message history within the same session.
12. THE CopilotPanel SHALL be styled with the dark theme and SHALL NOT overlap the main dashboard content on screens wider than 1024px (it SHALL push the layout or overlay on smaller screens).
13. WHEN the CopilotPanel is open, THE Dashboard SHALL display a visual indicator (e.g., highlighted border on the "Ask Copilot" button) showing the panel is active.

---

### Requirement 4: Backend Grounded Q&A Support

**User Story:** As a developer, I want the `/explain` endpoint to accept and use the current dashboard context sent from the frontend, so that answers are grounded in what the user is actually seeing.

#### Acceptance Criteria

1. THE ExplainEndpoint SHALL accept an optional `context` object in the request body containing any subset of DashboardContext fields.
2. WHEN a `context` object is provided, THE ExplainEndpoint SHALL use the provided context values to ground its response rather than re-fetching from the snapshot.
<!-- UPDATED: Response now includes supportingMetrics and contextUsed -->
3. THE ExplainEndpoint SHALL return a structured response with the fields: `question`, `answer`, `aiInsight`, `rootCause`, `recommendedActions`, `planningHealth`, `dataMode`, `lastRefreshedAt`, `supportingMetrics`, and `contextUsed`. The `supportingMetrics` field SHALL contain key numeric values used to ground the answer (e.g., changedRecordCount, totalRecords, trendDelta). The `contextUsed` field SHALL list which context fields were used to generate the answer.
4. WHEN the `question` field is provided, THE ExplainEndpoint SHALL generate an `answer` field that directly addresses the question using the available context.
5. IF the `context` object is not provided and `mode` is `"cached"`, THEN THE ExplainEndpoint SHALL fall back to loading the stored snapshot as before.
6. THE ExplainEndpoint SHALL validate that the `question` field is a non-empty string; IF the `question` field is empty or missing, THEN THE ExplainEndpoint SHALL return HTTP 400 with `{"error": "question is required"}`.
7. THE ExplainEndpoint SHALL return responses within 5 seconds for cached-mode requests.
8. THE ExplainEndpoint SHALL preserve backward compatibility: existing callers that do not send a `context` field SHALL continue to receive valid responses.

---

### Requirement 5: UX Improvements

**User Story:** As a planner, I want the dashboard to feel polished and consistent, so that I can use it confidently in enterprise settings.

#### Acceptance Criteria

1. THE Dashboard SHALL display a skeleton loading state (animated placeholder cards) instead of a spinner while data is being fetched.
2. WHEN `data.totalRecords` is 0, THE Dashboard SHALL display an empty state message: "No planning records available for the selected filters." in place of the KPI cards.
3. THE ActionsPanel buttons SHALL display a cursor-pointer style and a visible focus ring on keyboard focus.
4. WHEN a user hovers over any KPI Card, THE KPI Card SHALL transition its border color to `rgba(88, 166, 255, 0.4)` over 150ms to indicate interactivity.
5. THE Dashboard header SHALL display the `lastRefreshedAt` timestamp in the user's local timezone using `toLocaleString()`.
6. IF `data.lastRefreshedAt` is null or undefined, THEN THE Dashboard header SHALL display "Refresh pending" instead of an empty timestamp.
7. THE AlertBanner SHALL animate into view using a slide-down transition when it first renders.
<!-- UPDATED: Softened from "no component shall be removed or renamed" -->
8. THE existing dashboard layout, color tokens, and component structure SHALL be preserved unless a specific modification is required by another requirement in this document; components SHALL NOT be removed without a documented reason.

---

### Requirement 6: Response Contract Validation

**User Story:** As a developer, I want the frontend to safely handle any missing or null fields in the backend response, so that the dashboard never crashes due to unexpected API shapes.

#### Acceptance Criteria

1. THE frontend SHALL define a type-safe mapping between `DashboardResponse` fields and the props consumed by each KPI Card component, ensuring TypeScript compilation catches any field name mismatches.
2. BEFORE rendering any KPI Card, THE Dashboard SHALL apply null-safe access to all `DashboardResponse` fields using optional chaining (`?.`) or equivalent null guards.
3. IF the backend response is missing any top-level field expected by a KPI Card, THEN THE affected KPI Card SHALL render a graceful fallback state (e.g., "—" or "N/A") rather than throwing a runtime error.
4. THE frontend SHALL include a validation layer (a pure function `validateDashboardResponse`) that checks the received payload against expected field types and logs a warning to the console for any missing or type-mismatched field, without blocking the render.
5. THE `validateDashboardResponse` function SHALL be called once after the API response is received and before state is set, and SHALL NOT modify the response data.
6. IF the entire API response is null, empty, or unparseable, THEN THE Dashboard SHALL display the existing "No planning data available" empty state rather than a blank screen or uncaught error.
