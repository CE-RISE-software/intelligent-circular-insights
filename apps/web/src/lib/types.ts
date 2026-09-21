/**
 * Response shapes, mirroring the FastAPI routers in `apps/api/routers`.
 *
 * Hand-written rather than generated, and kept small on purpose: these describe
 * only what a window reads. Every field here was checked against a live response
 * from both backends, not inferred from the Python.
 */

export type Decision = "answer" | "abstain" | "escalate";
export type GroundingVerdict = "fully_grounded" | "unresolved_claims" | "not_applicable";

export interface Settings {
  model_default: string;
  model_allowed: string[];
  mode_default: string;
  /** Modes actually *built*, so the switch cannot offer one that would fail. */
  mode_allowed: string[];
  version: string;
}

export interface SubjectList {
  mode: string;
  subjects: Array<{ id: string; kind: string }>;
}

// ------------------------------------------------------------ search & answer
export interface EvidenceItem {
  id: string;
  kind: string;
  ref: string;
  score: number | null;
  text: string;
}

export interface ProvenanceItem {
  kind: string;
  ref: string;
  source_file: string | null;
  excerpt: string | null;
}

export interface SearchResult {
  decision: Decision;
  mode: string;
  answer: string | null;
  abstain_reason: string | null;
  /** Which confidence signal was weakest when the system declined. */
  weak_signal: string | null;
  confidence: {
    raw: number;
    calibrated: number;
    calibrator: string;
    signals: Record<string, number>;
  };
  operating_point: { tau: number; coverage_target: number | null };
  grounding: {
    verdict: GroundingVerdict;
    claims_total: number;
    claims_resolved: number;
    unresolved: Array<{ id: string; text: string; cited: string[] }>;
  };
  evidence: EvidenceItem[];
  provenance: ProvenanceItem[];
  trace: {
    correlation_id: string;
    model: string | null;
    prompt_hashes: string[];
    cost: {
      prompt_tokens: number;
      completion_tokens: number;
      reasoning_tokens: number;
      llm_calls: number;
      usd: number;
    };
    steps: Array<{ name: string; detail: string; duration_ms: number | null }>;
  };
  data_trust: { clean_value: number; interval: [number, number] } | null;
}

// ------------------------------------------------------------------- carbon
export interface Contribution {
  label: string;
  amount: number;
  unit: string;
  share: number | null;
  /** True when the number rests on an inferred input rather than a measured one. */
  is_proxy: boolean;
}

export interface CarbonResult {
  mode: string;
  product_id: string;
  indicator: string;
  total: number;
  unit: string;
  functional_unit: string | null;
  contributions: Contribution[];
  uncertainty: [number, number] | null;
  diagnostics: string[];
  uses_proxy_factors: boolean;
  provenance?: ProvenanceItem[];
  arithmetic?: string | null;
}

// ----------------------------------------------------------------- validate
export interface Violation {
  kind: string;
  location: string;
  message: string;
  expected: string | null;
  actual: string | null;
}

export interface ValidationReport {
  mode: string;
  profile: string;
  conforms: boolean;
  checked_paths: number;
  violations: Violation[];
}

export interface ProfileList {
  mode: string;
  profiles: Array<{ id: string; title: string; layer: string; version: string | null }>;
}

// ------------------------------------------------------------ CE-RISE models
export interface CeRiseModel {
  id: string;
  title: string;
  layer: string;
  summary: string;
  url: string;
  version: string | null;
  licence: string;
  namespace: string | null;
  class_count: number;
  keywords: string[];
}

export interface ModelCatalog {
  mode: string;
  source_org: string;
  licence: string;
  model_count: number;
  models: CeRiseModel[];
}

export interface RouteResult {
  mode: string;
  question: string;
  matches: Array<{ id: string; title: string; layer: string; score: number }>;
}

export interface CoverageReport {
  mode: string;
  substrates: Array<{
    substrate: string;
    questions_seen: number;
    questions_fired: number;
    fire_rate: number;
    conditional_precision: number | null;
  }>;
}

// -------------------------------------------------------------- PEF Studio
export interface Overview {
  mode: string;
  graph: { triples: number; activities: number; datasets: number; studies: string[] };
  competency_questions: {
    live: number;
    answered: number;
    total_in_paper: number;
    share_of_paper: number;
  };
  compliance_note: string;
}

export interface PefResult {
  mode: string;
  functional_unit: string | null;
  total: number;
  unit: string;
  data_quality: number | null;
  by_stage: Array<{ stage: string; amount: number; share: number | null; is_proxy: boolean }>;
  uncertainty: [number, number] | null;
  diagnostics: string[];
  uses_proxy_factors: boolean;
}

export interface CompetencyQuestion {
  id: string;
  question: string;
  pef_requirement: string;
  why_it_matters: string;
}

export interface CqCatalog {
  mode: string;
  total_in_paper: number;
  questions: CompetencyQuestion[];
}

export interface CqResult {
  mode: string;
  id: string;
  question: string;
  pef_requirement: string;
  sparql: string;
  answered: boolean;
  rows: Array<Record<string, string | null>>;
  error: string | null;
}

export interface SparqlResult {
  mode: string;
  columns: string[];
  rows: Array<Record<string, string | null>>;
  truncated: boolean;
}

// ----------------------------------------------------- record assistance
/**
 * A field the system filled *because a source said so*, with that source named.
 *
 * `model_score` is a model feature, deliberately not called "confidence": it is
 * not a calibrated probability and must never be read alongside a search result's.
 */
export interface GroundedFill {
  path: string;
  value: unknown;
  evidence_id: string;
  evidence_ref: string;
  source_pointer: string;
  model_score: number;
}

/**
 * A candidate the model produced from its own priors. Not evidence, not applied
 * to the record, and rendered where it cannot be mistaken for either (ADR 0011).
 */
export interface UnverifiedSuggestion {
  path: string;
  value: unknown;
  rationale: string;
  model_score: number;
  source: string;
  status: string;
  requires_review: boolean;
}

export interface RecordIssue {
  path: string;
  reason: string;
}

export interface RepairResult {
  mode: string;
  record: Record<string, unknown>;
  conforms: boolean;
  after: Omit<ValidationReport, "mode">;
  grounded_fills: GroundedFill[];
  cannot_be_grounded: RecordIssue[];
  rejected: RecordIssue[];
  unverified_suggestions: UnverifiedSuggestion[];
  trace: { correlation_id: string; steps: Array<{ name: string; detail: string }> };
}

export interface SynthesisResult {
  mode: string;
  dpp_id: string;
  record: Record<string, unknown>;
  profile: string;
  conforms: boolean;
  applied_schemas: string[];
  trace: { correlation_id: string; steps: Array<{ name: string; detail: string }> };
}
