import type { ReactNode } from "react";
import type { ApiResult, Declined, Failed } from "../lib/api";
import { MODE_LABELS, setRequestedMode, type BackendMode } from "../lib/mode";

/**
 * Rendering the three things a request can be.
 *
 * A 422 is not an error. The backend returns one when a mode honestly cannot
 * serve a feature, and "no knowledge graph is mounted in this mode; switch to
 * ce-rise" is a more useful thing to put on screen than a red box — so it gets an
 * amber panel and a button that does the switch.
 */
export function DeclinedPanel({ result }: { result: Declined }) {
  const target: BackendMode | null = result.reason.includes("ce-rise") ? "ce-rise" : null;
  return (
    <div className="declined" data-testid="declined">
      <div className="head">
        <span>⊘</span>
        {MODE_LABELS[(result.mode as BackendMode) ?? "normal"] ?? result.mode} cannot serve{" "}
        {result.capability}
      </div>
      <div className="reason">{result.reason}</div>
      {target && (
        <div>
          <button
            className="btn"
            data-testid="switch-mode"
            onClick={() => {
              setRequestedMode(target);
              window.location.reload();
            }}
          >
            Switch to {MODE_LABELS[target]}
          </button>
        </div>
      )}
    </div>
  );
}

export function FailedPanel({ result }: { result: Failed }) {
  return (
    <div className="failed" data-testid="failed">
      <strong>Request failed{result.status ? ` (${result.status})` : ""}.</strong> {result.message}
    </div>
  );
}

export function Loading({ label = "working" }: { label?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "18px 2px" }}
         data-testid="loading">
      <span className="spin" />
      <span className="muted">{label}…</span>
    </div>
  );
}

/** Render an `ApiResult` without each page repeating the three-way branch. */
export function Outcome<T>({
  result,
  pending,
  children,
  pendingLabel,
}: {
  result: ApiResult<T> | null;
  pending: boolean;
  pendingLabel?: string;
  children: (data: T) => ReactNode;
}) {
  if (pending) return <Loading label={pendingLabel} />;
  if (result === null) return null;
  if (result.kind === "declined") return <DeclinedPanel result={result} />;
  if (result.kind === "failed") return <FailedPanel result={result} />;
  return <>{children(result.data)}</>;
}
