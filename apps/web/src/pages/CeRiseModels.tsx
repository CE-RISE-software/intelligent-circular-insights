import { useState } from "react";
import { modelCatalog, routeQuestion, substrateCoverage } from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { RouteResult } from "../lib/types";
import { GlassCard, Pill, Stat } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Outcome } from "../components/Outcome";
import { ModeWarningBanner } from "../components/ModeBadge";
import { useApi } from "../lib/useApi";

/**
 * The CE-RISE data models, and which of them a question touches.
 *
 * The coverage table is the visible half of ADR 0005: fire rate per substrate,
 * reported separately rather than pooled. In CE-RISE mode two substrates are
 * mounted and both appear — that difference is the clearest demonstration in the
 * workbench that switching backend adds knowledge rather than exchanging it.
 */
export default function CeRiseModels() {
  const catalog = useApi(() => modelCatalog(), []);
  const coverage = useApi(() => substrateCoverage(), []);
  const [question, setQuestion] = useState("");
  const [routed, setRouted] = useState<ApiResult<RouteResult> | null>(null);
  const [pending, setPending] = useState(false);

  async function route() {
    if (!question.trim()) return;
    setPending(true);
    setRouted(await routeQuestion(question));
    setPending(false);
  }

  return (
    <div className="page" data-testid="page-models">
      <ModeWarningBanner />

      <GlassCard title="Mounted substrates" testId="substrate-coverage"
                 subtitle="Fire rate per substrate, not averaged across them. ADR 0005 measures whether a new substrate widens reach without costing precision, and a pooled number would hide exactly that.">
        <Outcome result={coverage.result} pending={coverage.pending} pendingLabel="reading coverage">
          {data => (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Substrate</th>
                  <th style={{ textAlign: "right" }}>Seen</th>
                  <th style={{ textAlign: "right" }}>Fired</th>
                  <th style={{ textAlign: "right" }}>Fire rate</th>
                  <th style={{ textAlign: "right" }}>Precision when fired</th>
                </tr>
              </thead>
              <tbody>
                {data.substrates.map(s => (
                  <tr key={s.substrate} data-testid={`substrate-${s.substrate}`}>
                    <td className="mono">{s.substrate}</td>
                    <td className="num">{s.questions_seen}</td>
                    <td className="num">{s.questions_fired}</td>
                    <td className="num">{(s.fire_rate * 100).toFixed(1)}%</td>
                    <td className="num">
                      {s.conditional_precision === null
                        ? <span className="faint">unlabelled</span>
                        : s.conditional_precision.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Outcome>
      </GlassCard>

      <GlassCard title="Route a question" testId="route-form"
                 subtitle="Which of the published data models a question would have to consult.">
        <form onSubmit={e => { e.preventDefault(); void route(); }}
              style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10 }}>
          <input
            className="field-control"
            data-testid="route-input"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="battery carbon footprint"
          />
          <button className="btn" type="submit" disabled={pending || !question.trim()}
                  data-testid="route-submit">
            {pending ? "Routing…" : "Route"}
          </button>
        </form>
        {routed?.kind === "declined" && <div style={{ marginTop: 12 }}><DeclinedPanel result={routed} /></div>}
        {routed?.kind === "failed" && <div style={{ marginTop: 12 }}><FailedPanel result={routed} /></div>}
        {routed?.kind === "ok" && (
          <div style={{ marginTop: 14 }} data-testid="route-result">
            {routed.data.matches.length === 0 ? (
              <p className="muted" style={{ margin: 0 }}>
                No model matched. That is an answer too — it says the question is outside the
                published schemas rather than that the router failed.
              </p>
            ) : (
              <table className="data-table">
                <thead><tr><th>Model</th><th>Layer</th><th style={{ textAlign: "right" }}>Score</th></tr></thead>
                <tbody>
                  {routed.data.matches.map(m => (
                    <tr key={m.id}>
                      <td><strong>{m.title}</strong><div className="faint mono">{m.id}</div></td>
                      <td><Pill tone="teal">{m.layer}</Pill></td>
                      <td className="num">{m.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </GlassCard>

      <Outcome result={catalog.result} pending={catalog.pending} pendingLabel="loading the catalogue">
        {data => (
          <GlassCard
            title="Catalogue"
            testId="model-catalog"
            actions={<Pill tone="amber" title="The models carry a different licence from this code.">{data.licence}</Pill>}
            subtitle="Derived from the vendored LinkML schemas rather than transcribed, so the list cannot drift from what the repositories actually publish."
          >
            <div style={{ display: "flex", gap: 30, marginBottom: 16 }}>
              <Stat label="Models" value={data.model_count} />
              <Stat label="Source" value={<a href={data.source_org} target="_blank" rel="noreferrer"
                     style={{ fontSize: 13, color: "var(--cerise-indigo)" }}>CE-RISE-models</a>} />
            </div>
            <table className="data-table">
              <thead>
                <tr><th>Model</th><th>Layer</th><th style={{ textAlign: "right" }}>Classes</th><th>Summary</th></tr>
              </thead>
              <tbody>
                {data.models.map(m => (
                  <tr key={m.id} data-testid={`model-${m.id}`}>
                    <td>
                      <a href={m.url} target="_blank" rel="noreferrer"
                         style={{ color: "var(--cerise-indigo)", fontWeight: 650, textDecoration: "none" }}>
                        {m.title}
                      </a>
                      <div className="faint mono">{m.id}{m.version ? ` · ${m.version}` : ""}</div>
                    </td>
                    <td><Pill tone="teal">{m.layer}</Pill></td>
                    <td className="num">{m.class_count}</td>
                    <td className="muted" style={{ maxWidth: 420 }}>{m.summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>
        )}
      </Outcome>
    </div>
  );
}
