/**
 * The typed client. One `request` function, and every response passes through it.
 *
 * Two rules it enforces that the pages therefore cannot get wrong:
 *
 *  1. The served mode is read off the response header and published centrally, so
 *     the badge reflects what answered rather than what was asked.
 *  2. A 422 is a *value*, not an exception. The backend returns 422 when a mode
 *     honestly cannot serve a feature, and that is an answer a window should render
 *     — "no knowledge graph is mounted in this mode; switch to ce-rise" is more
 *     useful than a red box saying Error.
 */
import {
  getRequestedMode,
  getSelectedModel,
  recordServedMode,
  type BackendMode,
} from "./mode";
import type {
  CarbonResult,
  CoverageReport,
  CqCatalog,
  CqResult,
  ModelCatalog,
  Overview,
  ParsedDocument,
  PefResult,
  RepairResult,
  RouteResult,
  SearchResult,
  Settings,
  SingleDppAnswer,
  SparqlResult,
  SubjectList,
  SynthesisResult,
  ValidationReport,
  ProfileList,
} from "./types";

export interface Declined {
  kind: "declined";
  /** What could not be served, e.g. "PEF studio". */
  capability: string;
  /** The mode that declined it. */
  mode: string;
  reason: string;
  status: number;
}

export interface Failed {
  kind: "failed";
  message: string;
  status: number | null;
}

export type ApiResult<T> = { kind: "ok"; data: T } | Declined | Failed;

export function isOk<T>(r: ApiResult<T>): r is { kind: "ok"; data: T } {
  return r.kind === "ok";
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  /** Overrides the session preference. Used by the compare view to ask both. */
  mode?: BackendMode;
  signal?: AbortSignal;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<ApiResult<T>> {
  const headers = new Headers({ Accept: "application/json" });
  headers.set("X-Backend-Mode", options.mode ?? getRequestedMode());
  const model = getSelectedModel();
  if (model) headers.set("X-Model", model);
  if (options.body !== undefined) headers.set("Content-Type", "application/json");

  let res: Response;
  try {
    res = await fetch(path, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (err) {
    // The backend is down or unreachable. Nothing is known about the mode now, so
    // the badge is cleared rather than left showing a stale value.
    if (options.mode === undefined) {
      recordServedMode({ mode: null, source: null, warning: null });
    }
    return { kind: "failed", message: describe(err), status: null };
  }

  publishServedMode(res, options.mode);

  if (res.status === 422) {
    const body = await safeJson(res);
    if (body && typeof body === "object" && "reason" in body) {
      const b = body as Record<string, unknown>;
      return {
        kind: "declined",
        capability: String(b.capability ?? b.substrate ?? "this feature"),
        mode: String(b.mode ?? ""),
        reason: String(b.reason ?? "no reason given"),
        status: 422,
      };
    }
  }

  if (!res.ok) {
    const body = await safeJson(res);
    return { kind: "failed", message: message(body, res), status: res.status };
  }

  return { kind: "ok", data: (await res.json()) as T };
}

/**
 * Only the session's own requests move the badge. The compare view asks both
 * backends at once; letting its second call retitle the header would make the
 * badge flicker to a mode the user never selected.
 */
function publishServedMode(res: Response, overridden: BackendMode | undefined): void {
  if (overridden !== undefined) return;
  const mode = res.headers.get("X-Backend-Mode-Used");
  recordServedMode({
    mode: mode === "normal" || mode === "ce-rise" ? mode : null,
    source: res.headers.get("X-Backend-Mode-Source"),
    warning: res.headers.get("X-Backend-Mode-Warning"),
  });
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

function message(body: unknown, res: Response): string {
  if (body && typeof body === "object") {
    const b = body as Record<string, unknown>;
    if (typeof b.detail === "string") return b.detail;
    if (typeof b.reason === "string") return b.reason;
    if (Array.isArray(b.detail)) return b.detail.map(describeDetail).join("; ");
  }
  return `${res.status} ${res.statusText}`;
}

function describeDetail(item: unknown): string {
  if (item && typeof item === "object") {
    const d = item as Record<string, unknown>;
    const where = Array.isArray(d.loc) ? d.loc.join(".") : "";
    return where ? `${where}: ${String(d.msg ?? "")}` : String(d.msg ?? "");
  }
  return String(item);
}

function describe(err: unknown): string {
  if (err instanceof DOMException && err.name === "AbortError") return "cancelled";
  return err instanceof Error
    ? `cannot reach the API (${err.message})`
    : "cannot reach the API";
}

// ===================================================================== routes

export const getSettings = () => request<Settings>("/api/settings");

export const getHealth = () =>
  request<{ ok: boolean; version: string; modes_built: string[] }>("/api/health");

export const search = (
  body: { q: string; product?: string | null; tau?: number; session?: string },
  mode?: BackendMode,
) => request<SearchResult>("/api/search", { method: "POST", body, mode });

export const parseSingleDpp = (content: string, filename: string | null, mode?: BackendMode) =>
  request<ParsedDocument>("/api/single-dpp/parse", {
    method: "POST",
    body: { content, filename },
    mode,
  });

export const askSingleDpp = (
  q: string,
  content: string,
  filename: string | null,
  tau: number,
  mode?: BackendMode,
) =>
  request<SingleDppAnswer>("/api/single-dpp/ask", {
    method: "POST",
    body: { q, content, filename, tau },
    mode,
  });

export const carbonSubjects = (mode?: BackendMode) =>
  request<SubjectList>("/api/carbon/subjects", { mode });

export const carbonCalculate = (product_id: string, mode?: BackendMode) =>
  request<CarbonResult>("/api/carbon/calculate", {
    method: "POST",
    body: { product_id, include_trace: true },
    mode,
  });

/**
 * `profile` may be null, meaning "whatever this mode checks against".
 *
 * Omitted from the body rather than sent as null, so the choice is made once, by
 * the backend that knows which schemas it mounted. Sending a literal here is what
 * left Validate checking the EU DPP schema after the user had switched to CE-RISE.
 */
export const validateDpp = (dpp: unknown, profile: string | null, mode?: BackendMode) =>
  request<ValidationReport>("/api/validate", {
    method: "POST",
    body: profile ? { dpp, profile } : { dpp },
    mode,
  });

export const repairDpp = (
  dpp: unknown,
  profile: string | null,
  suggest_from_training: boolean,
  mode?: BackendMode,
) =>
  request<RepairResult>("/api/validate/repair", {
    method: "POST",
    body: profile ? { dpp, profile, suggest_from_training } : { dpp, suggest_from_training },
    mode,
  });

export const synthesizeDpp = (seed: unknown, profile: string | null, mode?: BackendMode) =>
  request<SynthesisResult>("/api/synthesize", {
    method: "POST",
    body: profile ? { seed, profile } : { seed },
    mode,
  });

export const validationProfiles = (mode?: BackendMode) =>
  request<ProfileList>("/api/validate/profiles", { mode });

export const modelCatalog = (mode?: BackendMode) =>
  request<ModelCatalog>("/api/ce-rise-models/catalog", { mode });

export const routeQuestion = (question: string, mode?: BackendMode) =>
  request<RouteResult>("/api/ce-rise-models/route", {
    method: "POST",
    body: { question },
    mode,
  });

export const substrateCoverage = (mode?: BackendMode) =>
  request<CoverageReport>("/api/ce-rise-models/coverage", { mode });

export const pefOverview = (mode?: BackendMode) => request<Overview>("/api/pef/overview", { mode });

export const pefCalculate = (
  body: { study_id?: string; scenario?: Record<string, string> },
  mode?: BackendMode,
) => request<PefResult>("/api/pef/calculate", { method: "POST", body, mode });

export const competencyQuestions = (mode?: BackendMode) =>
  request<CqCatalog>("/api/pef/competency-questions", { mode });

export const runCompetencyQuestion = (id: string, mode?: BackendMode) =>
  request<CqResult>(`/api/pef/competency-questions/${encodeURIComponent(id)}`, {
    method: "POST",
    mode,
  });

export const runSparql = (query: string, limit = 50, mode?: BackendMode) =>
  request<SparqlResult>("/api/pef/sparql", { method: "POST", body: { query, limit }, mode });
