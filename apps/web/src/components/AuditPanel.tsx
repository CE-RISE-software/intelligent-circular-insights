import { useState } from "react";
import type { SearchResult } from "../lib/types";
import { Pill } from "./GlassCard";

/**
 * The reliability envelope, shown rather than summarised.
 *
 * The demo's audit panel reported a single confidence number. This one reports
 * the whole envelope, because a scalar cannot answer the question a practitioner
 * actually asks when the system declines: *which* signal was weak. The domain
 * keeps signals as a named vector all the way through precisely so this panel can
 * exist (ARCHITECTURE §9.1), and τ travels on the response because the threshold
 * is a policy choice that has to be auditable.
 */

/** What each named signal measures, in the words a reviewer would use. */
const SIGNAL_META: Record<string, { label: string; meaning: string }> = {
  retrieval_margin: {
    label: "Retrieval margin",
    meaning: "How far the best passage outscored the runner-up. Low means the evidence was ambiguous.",
  },
  snippet_agreement: {
    label: "Snippet agreement",
    meaning: "Whether the retrieved passages agree with each other. Low means the sources conflict.",
  },
  symbolic_fired: {
    label: "Symbolic support",
    meaning: "Whether a validated rule fired on this subject. Low means nothing symbolic backed the claim.",
  },
  generation_probability: {
    label: "Generation probability",
    meaning: "The model's own confidence in the composed text.",
  },
  memory_support: {
    label: "Memory support",
    meaning: "Whether a previously validated fact about this product corroborated the answer.",
  },
  neg_posterior_width: {
    label: "Posterior width",
    meaning: "Negated interval width from the bias-aware layer. Reserved; absent until data-trust is mounted.",
  },
  neg_target_sensitivity: {
    label: "Target sensitivity",
    meaning: "How much the conclusion moves under a bias tilt. Reserved.",
  },
};

const VERDICT_META: Record<string, { label: string; tone: string; meaning: string }> = {
  fully_grounded: {
    label: "Fully grounded",
    tone: "green",
    meaning: "Every claim in the answer resolved to a passage that was actually in the context pack.",
  },
  unresolved_claims: {
    label: "Unresolved claims",
    tone: "coral",
    meaning: "At least one claim cited nothing, or cited an id that was not in the pack. An answer cannot ship in this state.",
  },
  not_applicable: {
    label: "Not applicable",
    tone: "",
    meaning: "No composed answer was available to verify, or this was a deterministic result.",
  },
};

export function AuditPanel({ result }: { result: SearchResult }) {
  const [openTrace, setOpenTrace] = useState(false);
  const { confidence, operating_point, grounding, decision, weak_signal } = result;
  const verdict = VERDICT_META[grounding.verdict] ?? {
    label: grounding.verdict,
    tone: "",
    meaning: "",
  };
  const signals = Object.entries(confidence.signals);

  return (
    <div className="glass audit-surface" style={{ padding: 20, display: "grid", gap: 18 }}
         data-testid="audit-panel">
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <h3 style={{ margin: 0, fontSize: 14, color: "var(--cerise-navy)" }}>Reliability envelope</h3>
        <Pill tone={decision === "answer" ? "green" : "amber"}>
          {decision === "answer" ? "answered" : "abstained"}
        </Pill>
      </header>

      {/* --- calibrated confidence against the operating point --------------- */}
      <div>
        <div className="label">
          Calibrated confidence vs τ
          <span className="faint" style={{ textTransform: "none", letterSpacing: 0, marginLeft: 8, fontWeight: 500 }}>
            via {confidence.calibrator}
          </span>
        </div>
        <div className="tau-track" data-testid="tau-track">
          <div className="fill" style={{ width: `${clamp(confidence.calibrated) * 100}%` }} />
          <div className="marker" style={{ left: `${clamp(operating_point.tau) * 100}%` }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12, fontSize: 12 }}>
          <span className="muted">
            raw <span className="mono">{fmt(confidence.raw)}</span> → calibrated{" "}
            <strong className="mono" data-testid="calibrated">{fmt(confidence.calibrated)}</strong>
          </span>
          <span className="muted">
            τ = <span className="mono" data-testid="tau">{fmt(operating_point.tau)}</span>
            {operating_point.coverage_target !== null && (
              <> · coverage target <span className="mono">{fmt(operating_point.coverage_target)}</span></>
            )}
          </span>
        </div>
        <p className="faint" style={{ margin: "8px 0 0" }}>
          {decision === "answer"
            ? "Above the threshold, so the system answered. The invariant that an answer must clear τ is enforced in the domain, not here."
            : result.abstain_reason ?? "The system declined; no supported answer was available."}
        </p>
      </div>

      {/* --- the named signal vector ---------------------------------------- */}
      <div>
        <div className="label">Signals</div>
        {signals.length === 0 ? (
          <p className="faint" style={{ margin: 0 }}>No signals were recorded for this request.</p>
        ) : (
          <div data-testid="signal-vector">
            {signals.map(([name, value]) => {
              const meta = SIGNAL_META[name] ?? { label: name, meaning: "" };
              const weak = name === weak_signal;
              return (
                <div className={`signal-row ${weak ? "weak" : ""}`} key={name}
                     title={meta.meaning} data-signal={name} data-weak={weak ? "true" : "false"}>
                  <span className="name">{meta.label}</span>
                  <span className="track">
                    <span className="fill" style={{ width: `${clamp(value) * 100}%` }} />
                  </span>
                  <span className="value">{fmt(value)}</span>
                </div>
              );
            })}
          </div>
        )}
        {weak_signal && (
          <p style={{ margin: "10px 0 0", fontSize: 12.5, color: "#8f2222", lineHeight: 1.5 }}
             data-testid="weak-signal">
            <strong>Weakest signal: {SIGNAL_META[weak_signal]?.label ?? weak_signal}.</strong>{" "}
            {SIGNAL_META[weak_signal]?.meaning}
          </p>
        )}
      </div>

      {/* --- grounding ------------------------------------------------------ */}
      <div>
        <div className="label">Grounding</div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span data-testid="grounding-verdict">
            <Pill tone={verdict.tone} title={verdict.meaning}>{verdict.label}</Pill>
          </span>
          <span className="muted">
            <span className="mono">{grounding.claims_resolved}</span> of{" "}
            <span className="mono">{grounding.claims_total}</span> claims resolved to evidence in the pack
          </span>
        </div>
        {verdict.meaning && <p className="faint" style={{ margin: "8px 0 0" }}>{verdict.meaning}</p>}
        {grounding.unresolved?.map(claim => (
          <p key={claim.id} className="faint" data-testid="unresolved-claim">
            Unresolved: {claim.text}
          </p>
        ))}
      </div>

      {/* --- provenance ------------------------------------------------------ */}
      {result.provenance.length > 0 && (
        <div>
          <div className="label">Provenance · {result.provenance.length}</div>
          <div style={{ display: "grid", gap: 8 }} data-testid="provenance">
            {result.provenance.map((p, i) => (
              <div key={`${p.ref}-${i}`} className="evidence-card" style={{ padding: "10px 12px" }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                  <Pill tone="teal">{p.kind}</Pill>
                  <span className="mono" style={{ fontSize: 11.5 }}>{p.ref}</span>
                </div>
                {p.excerpt && <div className="muted" style={{ fontSize: 12 }}>{p.excerpt}</div>}
                {p.source_file && <div className="faint mono" style={{ marginTop: 4 }}>{p.source_file}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* --- trace ----------------------------------------------------------- */}
      <div>
        <button className="btn secondary" onClick={() => setOpenTrace(o => !o)}
                data-testid="toggle-trace" style={{ width: "100%" }}>
          {openTrace ? "Hide" : "Show"} inference trace · {result.trace.steps.length} steps
        </button>
        {openTrace && (
          <div style={{ marginTop: 10, display: "grid", gap: 6 }} data-testid="trace">
            <div className="faint" data-testid="model-audit">
              Model · {result.trace.model ?? "not called"}
              {result.trace.cost && (
                <> · live attempts {result.trace.cost.llm_calls} · estimated spend ${result.trace.cost.usd.toFixed(6)}</>
              )}
            </div>
            {result.trace.prompt_hashes?.map((hash, i) => (
              <div className="faint mono" key={`${hash}-${i}`} style={{ overflowWrap: "anywhere" }}>
                prompt hash · {hash}
              </div>
            ))}
            {result.trace.steps.map((s, i) => (
              <div key={`${s.name}-${i}`} style={{ display: "grid", gridTemplateColumns: "22px 1fr", gap: 8 }}>
                <span className="faint mono">{i + 1}</span>
                <span style={{ fontSize: 12.5 }}>
                  <strong>{s.name}</strong>
                  {s.detail && <span className="muted"> — {s.detail}</span>}
                </span>
              </div>
            ))}
            <div className="faint mono" style={{ marginTop: 6 }}>
              correlation id · {result.trace.correlation_id}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function clamp(v: number): number {
  return Math.max(0, Math.min(1, v));
}

function fmt(v: number): string {
  return v.toFixed(3);
}
