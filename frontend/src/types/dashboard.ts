export type TrendDirection = "Increase" | "Decrease" | "Stable" | "Volatile";
export type HealthStatus = "Healthy" | "Stable" | "At Risk" | "Critical";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type AlertSeverity = "info" | "warning" | "high" | "critical";
export type DataMode = "blob" | "cached" | "mock";

export interface SupplierDetail {
  supplier: string;
  previousSupplier: string | null;
  affectedMaterials: string[];
  riskLevel: string;
}

export interface DesignDetail {
  materialId: string;
  locationId: string;
  materialGroup: string;
  bodPrevious: string | null;
  bodCurrent: string | null;
  ffPrevious: string | null;
  ffCurrent: string | null;
  riskLevel: string;
}

export interface RojDetail {
  materialId: string;
  locationId: string;
  rojPrevious: string | null;
  rojCurrent: string | null;
  rojReasonCode: string | null;
}

export interface DatacenterSummary {
  locationId: string;
  dcSite: string | null;
  total: number;
  changed: number;
}

export interface MaterialGroupSummary {
  materialGroup: string;
  total: number;
  changed: number;
  qtyChanged: number;
  designChanged: number;
  supplierChanged: number;
}

export interface AlertPayload {
  shouldTrigger: boolean;
  severity: AlertSeverity;
  triggerType: string;
  message: string;
  drivers: Record<string, string | null>;
  recommendedAction: string;
}

export interface DetailRecord {
  locationId: string;
  materialGroup: string;
  materialId: string;
  supplier: string | null;
  forecastQtyCurrent: number | null;
  forecastQtyPrevious: number | null;
  qtyDelta: number | null;
  rojCurrent: string | null;
  rojPrevious: string | null;
  bodCurrent: string | null;
  bodPrevious: string | null;
  ffCurrent: string | null;
  ffPrevious: string | null;
  changeType: string;
  riskLevel: string;
  qtyChanged: boolean;
  supplierChanged: boolean;
  designChanged: boolean;
  rojChanged: boolean;
  dcSite: string | null;
  country: string | null;
  lastModifiedBy: string | null;
  lastModifiedDate: string | null;
}

export interface DashboardResponse {
  dataMode: DataMode;
  lastRefreshedAt: string;
  planningHealth: number;
  status: HealthStatus;
  forecastNew: number;
  forecastOld: number;
  trendDirection: TrendDirection;
  trendDelta: number;
  datacenterCount: number;
  materialGroups: string[];
  totalRecords: number;
  changedRecordCount: number;
  unchangedRecordCount: number;
  newRecordCount: number;
  supplierSummary: {
    changed: number;
    topSupplier: string | null;
    details: SupplierDetail[];
  };
  designSummary: {
    status: string;
    bodChangedCount: number;
    formFactorChangedCount: number;
    details: DesignDetail[];
  };
  rojSummary: {
    status: string;
    changedCount: number;
    details: RojDetail[];
  };
  riskSummary: {
    level: RiskLevel;
    highestRiskLevel: string;
    quantityChangedCount: number;
    supplierChangedCount: number;
    designChangedCount: number;
    rojChangedCount: number;
    highRiskCount: number;
    riskBreakdown: Record<string, number>;
  };
  aiInsight: string;
  rootCause: string;
  recommendedActions: string[];
  drivers: {
    location: string | null;
    supplier: string | null;
    material: string | null;
    materialGroup: string | null;
    changeType: string;
  };
  alerts: AlertPayload;
  datacenterSummary: DatacenterSummary[];
  materialGroupSummary: MaterialGroupSummary[];
  detailRecords: DetailRecord[];
  filters: {
    locationId: string | null;
    materialGroup: string | null;
  };
}

export interface DashboardContext {
  planningHealth: number;
  status: HealthStatus;
  forecastNew: number;
  forecastOld: number;
  trendDelta: number;
  trendDirection: TrendDirection;
  changedRecordCount: number;
  totalRecords: number;
  riskSummary: {
    level: RiskLevel;
    highestRiskLevel: string;
    highRiskCount: number;
    riskBreakdown: Record<string, number>;
    quantityChangedCount: number;
    supplierChangedCount: number;
    designChangedCount: number;
    rojChangedCount: number;
  };
  aiInsight: string;
  rootCause: string;
  recommendedActions: string[];
  alerts: AlertPayload;
  drivers: {
    location: string | null;
    supplier: string | null;
    material: string | null;
    materialGroup: string | null;
    changeType: string;
  };
  filters: {
    locationId: string | null;
    materialGroup: string | null;
  };
  dataMode: DataMode;
  lastRefreshedAt: string;
  // Enriched MCP fields for Copilot Q&A
  datacenterSummary: DatacenterSummary[];
  materialGroupSummary: MaterialGroupSummary[];
  supplierSummary: {
    changed: number;
    topSupplier: string | null;
  };
  designSummary: {
    status: string;
    bodChangedCount: number;
    formFactorChangedCount: number;
  };
  rojSummary: {
    status: string;
    changedCount: number;
  };
  datacenterCount: number;
  materialGroups: string[];
  highRiskRecordCount: number;
  // Detail records for supplier queries and analysis
  detailRecords: DetailRecord[];
}

export interface ExplainRequest {
  question: string;
  location_id?: string;
  material_group?: string;
  context?: Partial<DashboardContext>;
}

export interface ExplainResponse {
  question: string;
  answer: string;
  queryType: string;
  answerMode: string;
  scopeType?: string;
  scopeValue?: string;
  aiInsight: string;
  rootCause: string;
  recommendedActions: string[];
  planningHealth: number;
  dataMode: DataMode;
  lastRefreshedAt: string;
  supportingMetrics: {
    changedRecordCount: number;
    totalRecords: number;
    trendDelta: number;
    planningHealth: number;
  };
  contextUsed: string[];
  comparisonMetrics?: {
    entity1: string;
    entity2?: string;
    metrics: Record<string, any>;
  };
  supplierMetrics?: {
    location: string;
    suppliers: Array<{
      supplier: string;
      affectedRecords: number;
      forecastImpact: number;
      designChanges: number;
      availabilityIssues: number;
      rojIssues: number;
      riskLevel: string;
    }>;
  };
  recordComparison?: {
    materialId: string;
    locationId: string;
    current: Record<string, any>;
    previous: Record<string, any>;
    changes: Record<string, any>;
    riskLevel: string;
  };
}

export interface DebugSnapshotResponse {
  normalizedCount: number;
  filteredCount: number;
  comparedCount: number;
  changedCount: number;
  healthScoreInputs: {
    total: number;
    changed: number;
    riskCounts: Record<string, number>;
    designCount: number;
    supplierCount: number;
    highestRisk: string;
    deductions: {
      changeRatio: number;
      riskLevel: number;
      designPenalty: number;
      supplierPenalty: number;
    };
  };
  dashboardResponse: DashboardResponse;
}
