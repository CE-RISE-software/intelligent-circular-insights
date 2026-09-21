/**
 * Which backend this session is asking for, and which one actually answered.
 *
 * These are two different facts and the UI keeps them apart on purpose. The
 * *requested* mode is a local preference; the *served* mode is whatever the last
 * response's `X-Backend-Mode-Used` header said. A badge that renders the request
 * would keep claiming "ce-rise" after a deployment that never built that bundle
 * silently fell back — which is the exact failure the header exists to expose.
 */

export type BackendMode = "normal" | "ce-rise";

export const MODE_LABELS: Record<BackendMode, string> = {
  normal: "Normal",
  "ce-rise": "CE-RISE",
};

export const MODE_BLURBS: Record<BackendMode, string> = {
  normal:
    "Flat product profiles, published emission factors, JSON-Schema conformance and lexical retrieval. Fast and broad.",
  "ce-rise":
    "Adds the WP3 knowledge graph: a product system solved off RDF, competency questions, and triples behind every number.",
};

const LS_MODE = "ici.backendMode";
const LS_MODEL = "ici.model";
const LS_TAU = "ici.tau";

function isMode(value: unknown): value is BackendMode {
  return value === "normal" || value === "ce-rise";
}

function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null; // private windows, blocked storage: a preference is not worth a crash
  }
}

function write(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* preference is lost, the app is not */
  }
}

// ---------------------------------------------------------------- requested
export function getRequestedMode(): BackendMode {
  const stored = read(LS_MODE);
  return isMode(stored) ? stored : "normal";
}

export function setRequestedMode(mode: BackendMode): void {
  write(LS_MODE, mode);
  notify();
}

export function getSelectedModel(): string | null {
  return read(LS_MODEL);
}

export function setSelectedModel(model: string): void {
  write(LS_MODEL, model);
}

export function getTau(): number {
  const raw = read(LS_TAU);
  const parsed = raw === null ? NaN : Number.parseFloat(raw);
  return Number.isFinite(parsed) && parsed >= 0 && parsed <= 1 ? parsed : 0.5;
}

export function setTau(tau: number): void {
  write(LS_TAU, String(tau));
}

// ------------------------------------------------------------------- served
export interface ServedMode {
  mode: BackendMode | null;
  /** "header" when the request was honoured, "default" when it was not. */
  source: string | null;
  /** Set when the backend refused the requested mode and fell back. */
  warning: string | null;
}

let served: ServedMode = { mode: null, source: null, warning: null };
const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) listener();
}

/** Called by the API client on every response, success or failure. */
export function recordServedMode(next: ServedMode): void {
  if (
    next.mode === served.mode &&
    next.source === served.source &&
    next.warning === served.warning
  ) {
    return;
  }
  served = next;
  notify();
}

export function getServedMode(): ServedMode {
  return served;
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * True when the backend did not serve what was asked for. The badge turns amber
 * on this, because a silently downgraded backend produces answers of a different
 * rigour under the same interface.
 */
export function isModeMismatch(): boolean {
  return served.mode !== null && served.mode !== getRequestedMode();
}
