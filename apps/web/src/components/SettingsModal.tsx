import { useState } from "react";
import {
  getSelectedModel,
  getTau,
  MODE_BLURBS,
  MODE_LABELS,
  setRequestedMode,
  setSelectedModel,
  setTau,
  type BackendMode,
} from "../lib/mode";
import { useRequestedMode } from "../lib/useApi";
import type { Settings } from "../lib/types";

/**
 * Settings, with the backend switch sitting beside the model choice.
 *
 * The switch only offers modes the backend reports as *built* (`mode_allowed`
 * comes from the bundle registry, not the configuration), so the UI cannot offer
 * a choice that would immediately fall back. Saving reloads: every window would
 * otherwise have to be individually invalidated, and a half-switched workbench
 * showing two backends' numbers at once is worse than a one-second reload.
 */
export function SettingsModal({ settings, onClose }: { settings: Settings; onClose: () => void }) {
  const current = useRequestedMode();
  const [mode, setMode] = useState<BackendMode>(current);
  const [model, setModel] = useState(getSelectedModel() ?? settings.model_default);
  const [tau, setTauLocal] = useState(getTau());

  const available = settings.mode_allowed.filter(
    (m): m is BackendMode => m === "normal" || m === "ce-rise",
  );

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(27,18,82,0.34)",
        display: "grid", placeItems: "center", zIndex: 100, backdropFilter: "blur(4px)",
      }}
      data-testid="settings-modal"
    >
      <div className="glass solid" onClick={e => e.stopPropagation()}
           style={{ padding: 28, width: 520, maxHeight: "86vh", overflowY: "auto" }}>
        <h2 style={{ marginTop: 0, color: "var(--cerise-navy)" }}>Settings</h2>

        <label className="label">Backend</label>
        <div className="mode-switch" data-testid="mode-switch">
          {available.map(m => (
            <button
              key={m}
              className={`mode-option ${m === mode ? "selected" : ""}`}
              data-testid={`mode-option-${m}`}
              aria-pressed={m === mode}
              onClick={() => setMode(m)}
            >
              <span className="radio" />
              <span>
                <span className="name">
                  {MODE_LABELS[m]}
                  {m === settings.mode_default && (
                    <span className="faint" style={{ fontWeight: 500, marginLeft: 7 }}>· default</span>
                  )}
                </span>
                <span className="blurb">{MODE_BLURBS[m]}</span>
              </span>
            </button>
          ))}
        </div>
        <p className="faint" style={{ marginTop: 10, marginBottom: 22 }}>
          Sent on every request as <code>X-Backend-Mode</code>. The badge in the header reads the
          response instead, so it shows which backend actually answered. Only backends this
          deployment has built are listed.
        </p>

        <label className="label">Language model</label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {settings.model_allowed.map(m => (
            <button
              key={m}
              className={"pill " + (m === model ? "teal" : "")}
              onClick={() => setModel(m)}
              data-testid={`model-option-${m}`}
              style={{
                cursor: "pointer",
                fontFamily: "var(--font-mono)",
                border: m === model ? "1px solid var(--cerise-indigo)" : undefined,
              }}
            >
              {m}{m === settings.model_default ? " · default" : ""}
            </button>
          ))}
        </div>
        <p className="faint" style={{ marginTop: 10, marginBottom: 22 }}>
          Retrieval, validation and both impact engines are deterministic and cost nothing to run.
          The model is used only where prose is composed.
        </p>

        <label className="label">Operating point · τ = <span className="mono">{tau.toFixed(2)}</span></label>
        <input
          type="range" min={0} max={1} step={0.05} value={tau}
          onChange={e => setTauLocal(Number.parseFloat(e.target.value))}
          data-testid="tau-slider"
          style={{ width: "100%", accentColor: "var(--cerise-purple)" }}
        />
        <p className="faint" style={{ marginTop: 8, marginBottom: 24 }}>
          The threshold a calibrated confidence must clear before the system answers rather than
          abstains. Raising it buys precision with coverage. It travels on every response, so any
          answer can be audited against the threshold that produced it.
        </p>

        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button className="btn secondary" onClick={onClose}>Cancel</button>
          <button
            className="btn"
            data-testid="settings-save"
            onClick={() => {
              setSelectedModel(model);
              setTau(tau);
              setRequestedMode(mode);
              onClose();
              window.location.reload();
            }}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
