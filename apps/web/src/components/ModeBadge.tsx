import { useSyncExternalStore } from "react";
import {
  getRequestedMode,
  getServedMode,
  isModeMismatch,
  MODE_LABELS,
  subscribe,
  type BackendMode,
} from "../lib/mode";

/**
 * Which backend answered — not which one was asked for.
 *
 * Reading the response header rather than the local preference is the whole
 * point. If a deployment builds only the Normal bundle, or a header is mistyped,
 * the backend falls back and says so; a badge rendered from the preference would
 * keep claiming CE-RISE while flat-profile numbers came back. Amber means served
 * ≠ requested, which is a thing the operator needs to see immediately.
 */
export function ModeBadge() {
  const served = useSyncExternalStore(subscribe, getServedMode, getServedMode);
  const requested = useSyncExternalStore(subscribe, getRequestedMode, getRequestedMode);
  const mismatch = useSyncExternalStore(subscribe, isModeMismatch, isModeMismatch);

  if (served.mode === null) {
    return (
      <span className="mode-badge unknown" data-testid="mode-badge" data-mode="unknown"
            title="No response yet — the badge reports the backend that answered, so it stays blank until one has.">
        <span className="dot" />
        backend: —
      </span>
    );
  }

  const title = mismatch
    ? `You asked for ${MODE_LABELS[requested]}; ${MODE_LABELS[served.mode]} answered. ` +
      (served.warning ?? "The requested backend is not available here.")
    : `Served by the ${MODE_LABELS[served.mode]} backend (${served.source ?? "default"}).`;

  return (
    <span
      className={`mode-badge ${served.mode} ${mismatch ? "mismatch" : ""}`}
      data-testid="mode-badge"
      data-mode={served.mode}
      data-mismatch={mismatch ? "true" : "false"}
      title={title}
    >
      <span className="dot" />
      {MODE_LABELS[served.mode]}
      {mismatch && <span style={{ fontWeight: 500, opacity: 0.8 }}>· fell back</span>}
    </span>
  );
}

export function ModeWarningBanner() {
  const served = useSyncExternalStore(subscribe, getServedMode, getServedMode);
  const mismatch = useSyncExternalStore(subscribe, isModeMismatch, isModeMismatch);
  if (!mismatch || served.mode === null) return null;
  return (
    <div className="declined" data-testid="mode-warning">
      <div className="head">⚠ The backend fell back</div>
      <div className="reason">
        {served.warning ??
          `The requested backend is not enabled in this deployment; ${MODE_LABELS[served.mode]} answered instead.`}{" "}
        Numbers on this page come from {MODE_LABELS[served.mode]}.
      </div>
    </div>
  );
}

export function modeClass(mode: BackendMode): string {
  return mode === "ce-rise" ? "ce-rise" : "normal";
}
