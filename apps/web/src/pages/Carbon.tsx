import { useState } from "react";
import { carbonCalculate, carbonSubjects } from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { CarbonResult } from "../lib/types";
import { GlassCard, Pill, Stat } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Loading, Outcome } from "../components/Outcome";
import { ModeWarningBanner } from "../components/ModeBadge";
import { useApi } from "../lib/useApi";

/**
 * Deterministic product-level assessment.
 *
 * This window works in *both* modes, and that is the point rather than an
 * oversight: CE-RISE mode adds the graph without displacing the CSV factor engine,
 * so the five products the graph has never heard of keep working. An earlier build
 * swapped the engine and this window went blank on the more rigorous backend.
 */
export default function Carbon() {
  const subjects = useApi(() => carbonSubjects(), []);
  const [selected, setSelected] = useState<string | null>(null);
  const [result, setResult] = useState<ApiResult<CarbonResult> | null>(null);
  const [pending, setPending] = useState(false);

  async function assess(id: string) {
    setSelected(id);
    setPending(true);
    setResult(await carbonCalculate(id));
    setPending(false);
  }

  return (
    <div className="page" data-testid="page-carbon">
      <ModeWarningBanner />
      <GlassCard
        title="Carbon"
        subtitle="Flat product profiles multiplied by published emission factors. Every number carries its derivation, and inferred inputs are badged so a reader is never misled about which figures are measured."
        testId="carbon-subjects"
      >
        <Outcome result={subjects.result} pending={subjects.pending} pendingLabel="loading subjects">
          {data => (
            <>
              <div className="label">
                {data.subjects.length} assessable {data.subjects.length === 1 ? "subject" : "subjects"} in this backend
              </div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {data.subjects.map(s => (
                  <button
                    key={s.id}
                    className={"pill " + (s.id === selected ? "teal" : "")}
                    data-testid={`carbon-subject-${s.id}`}
                    onClick={() => void assess(s.id)}
                    style={{
                      cursor: "pointer",
                      fontFamily: "var(--font-mono)",
                      fontSize: 11.5,
                      border: s.id === selected ? "1px solid var(--cerise-indigo)" : undefined,
                    }}
                  >
                    {s.id}
                  </button>
                ))}
              </div>
              <p className="faint" style={{ marginTop: 12, marginBottom: 0 }}>
                Read from the profile directory rather than hard-coded, so the list cannot drift
                from the data the engine actually has.
              </p>
            </>
          )}
        </Outcome>
      </GlassCard>

      {pending && <Loading label={`assessing ${selected}`} />}
      {!pending && result?.kind === "declined" && <DeclinedPanel result={result} />}
      {!pending && result?.kind === "failed" && <FailedPanel result={result} />}
      {!pending && result?.kind === "ok" && <CarbonReport result={result.data} />}
    </div>
  );
}

function CarbonReport({ result }: { result: CarbonResult }) {
  const [derivationOpen, setDerivationOpen] = useState(false);
  const provenance = result.provenance ?? [];

  return (
    <>
      <GlassCard title={result.product_id} testId="carbon-result"
                 subtitle={`${result.indicator.replace("_", " ")} · ${result.functional_unit ?? "product lifecycle"}`}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 18 }}>
          <Stat label="Total" value={result.total.toFixed(2)} unit={result.unit} />
          {result.uncertainty && (
            <Stat
              label="Uncertainty band"
              value={`${result.uncertainty[0].toFixed(1)} – ${result.uncertainty[1].toFixed(1)}`}
              unit={result.unit}
              hint="Propagated from the engine's declared input ranges."
            />
          )}
          <div>
            <div className="label">Basis</div>
            <Pill tone={result.uses_proxy_factors ? "amber" : "green"}>
              {result.uses_proxy_factors ? "uses proxy factors" : "measured inputs"}
            </Pill>
          </div>
        </div>
      </GlassCard>

      <GlassCard title="Contributions by stage" testId="carbon-stages">
        <table className="data-table">
          <thead>
            <tr>
              <th>Stage</th>
              <th style={{ textAlign: "right" }}>Amount</th>
              <th style={{ textAlign: "right" }}>Share</th>
              <th>Basis</th>
            </tr>
          </thead>
          <tbody>
            {result.contributions.map(c => (
              <tr key={c.label}>
                <td>{c.label}</td>
                <td className="num">{c.amount.toFixed(3)} {c.unit}</td>
                <td className="num">{c.share === null ? "—" : `${(c.share * 100).toFixed(1)}%`}</td>
                <td>{c.is_proxy ? <Pill tone="amber">inferred</Pill> : <Pill tone="green">measured</Pill>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </GlassCard>

      {provenance.length > 0 && (
        <GlassCard
          title={`Derivation · ${provenance.length} sources`}
          testId="carbon-provenance"
          subtitle="Where each factor came from. A number with no traceable factor is not publishable, so it is shown rather than summarised."
          actions={
            <button
              className="btn secondary"
              type="button"
              data-testid="toggle-carbon-derivation"
              aria-expanded={derivationOpen}
              aria-controls="carbon-derivation-steps"
              onClick={() => setDerivationOpen(open => !open)}
            >
              {derivationOpen ? "Hide derivation steps" : "View derivation steps"}
            </button>
          }
        >
          {result.arithmetic && (
            <pre className="mono" style={{
              margin: derivationOpen ? "0 0 14px" : 0, padding: 12, borderRadius: 10, fontSize: 11.5,
              background: "rgba(27,18,82,0.05)", overflowX: "auto", whiteSpace: "pre-wrap",
            }}>{result.arithmetic}</pre>
          )}
          {derivationOpen && (
            <div
              id="carbon-derivation-steps"
              data-testid="carbon-derivation-steps"
              aria-label="Carbon derivation steps"
              tabIndex={0}
              style={{
                maxHeight: 200,
                overflowY: "auto",
                overscrollBehavior: "contain",
                paddingRight: 4,
              }}
            >
              <div className="label" style={{ marginBottom: 8 }}>Calculation steps</div>
              <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 8 }}>
                {provenance.map((p, i) => (
                  <li key={`${p.ref}-${i}`} className="evidence-card" style={{ padding: "10px 12px" }}>
                    <div style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
                      <Pill tone="teal">{i + 1}</Pill>
                      <div style={{ minWidth: 0 }}>
                        <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.5 }}>
                          {p.excerpt || p.ref}
                        </div>
                        <div className="faint mono" style={{ marginTop: 4, overflowWrap: "anywhere" }}>
                          {p.kind} · {p.ref}
                        </div>
                        {p.source_file && (
                          <div className="faint mono" style={{ marginTop: 4, overflowWrap: "anywhere" }}>
                            {p.source_file}
                          </div>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
              <p className="faint" style={{ margin: "10px 0 0" }}>
                These are the provenance records captured by the engine during this calculation;
                opening the panel does not rerun or reinterpret the result.
              </p>
            </div>
          )}
        </GlassCard>
      )}

      {result.diagnostics.length > 0 && (
        <GlassCard title={`Diagnostics · ${result.diagnostics.length}`} testId="carbon-diagnostics"
                   subtitle="Kept rather than suppressed. A missing input that was silently defaulted is the difference between a figure and a guess.">
          <ul className="muted" style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 4 }}>
            {result.diagnostics.map((d, i) => <li key={i}>{d}</li>)}
          </ul>
        </GlassCard>
      )}
    </>
  );
}
