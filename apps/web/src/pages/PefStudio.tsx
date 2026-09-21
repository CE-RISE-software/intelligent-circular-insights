import { useState } from "react";
import {
  competencyQuestions,
  pefCalculate,
  pefOverview,
  runCompetencyQuestion,
  runSparql,
} from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { CqResult, SparqlResult } from "../lib/types";
import { GlassCard, Pill, Stat } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Loading, Outcome } from "../components/Outcome";
import { ModeWarningBanner } from "../components/ModeBadge";
import { useApi } from "../lib/useApi";

/**
 * The WP3 integration: a footprint solved off an RDF graph rather than a table.
 *
 * Only CE-RISE mode mounts the graph. In Normal mode every endpoint here returns a
 * typed 422 with a reason, which the shared `DeclinedPanel` renders as an amber
 * panel and a button that switches backend — a more useful thing to put in front
 * of someone than a hidden tab or a red error.
 */
export type PefTab = "overview" | "calculator" | "questions" | "sparql";

export default function PefStudio({ tab }: { tab: PefTab }) {
  return (
    <div className="page" data-testid={`page-pef-${tab}`}>
      <ModeWarningBanner />
      {tab === "overview" && <Overview />}
      {tab === "calculator" && <Calculator />}
      {tab === "questions" && <Questions />}
      {tab === "sparql" && <Sparql />}
    </div>
  );
}

function Overview() {
  const { result, pending } = useApi(() => pefOverview(), []);
  return (
    <Outcome result={result} pending={pending} pendingLabel="loading the graph">
      {data => (
        <>
          <GlassCard title="Knowledge graph" testId="pef-overview"
                     subtitle="The PEFDPP ontology and the battery case study, loaded once at startup.">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))", gap: 20 }}>
              <Stat label="Triples" value={data.graph.triples.toLocaleString()} />
              <Stat label="Activities" value={data.graph.activities} />
              <Stat label="Datasets" value={data.graph.datasets} />
              <Stat label="Studies" value={data.graph.studies.length} />
            </div>
            {data.graph.studies.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div className="label">Declared studies</div>
                <div style={{ display: "flex", gap: 7, flexWrap: "wrap" }}>
                  {data.graph.studies.map(s => <Pill key={s} tone="teal">{s}</Pill>)}
                </div>
              </div>
            )}
          </GlassCard>

          <GlassCard title="Competency-question coverage" testId="pef-coverage"
                     subtitle="Stated against the paper's full set rather than only what works here, so the number is one a reader can judge.">
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))", gap: 20 }}>
              <Stat label="Implemented" value={data.competency_questions.live} />
              <Stat label="Answering" value={data.competency_questions.answered} />
              <Stat label="In the paper" value={data.competency_questions.total_in_paper} />
              <Stat label="Share" value={`${(data.competency_questions.share_of_paper * 100).toFixed(2)}%`} />
            </div>
          </GlassCard>

          <div className="declined" data-testid="compliance-note">
            <div className="head">Scope of this result</div>
            <div className="reason">{data.compliance_note}</div>
          </div>
        </>
      )}
    </Outcome>
  );
}

function Calculator() {
  const { result, pending } = useApi(() => pefCalculate({}), []);
  return (
    <Outcome result={result} pending={pending} pendingLabel="solving the product system">
      {data => (
        <>
          <GlassCard title="PEF result" testId="pef-result"
                     subtitle={data.functional_unit ?? "per functional unit"}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 20 }}>
              <Stat label="Climate change" value={data.total.toFixed(6)} unit={data.unit} />
              {data.data_quality !== null && (
                <Stat label="Weighted DQR" value={data.data_quality.toFixed(4)}
                      hint="Contribution-weighted across the datasets that carry the result. Lower is better." />
              )}
              {data.uncertainty && (
                <Stat label="Uncertainty"
                      value={`${data.uncertainty[0].toFixed(4)} – ${data.uncertainty[1].toFixed(4)}`}
                      unit={data.unit} />
              )}
            </div>
          </GlassCard>

          <GlassCard title="By life-cycle stage" testId="pef-stages"
                     subtitle="The stage is read off the ActivityLink, not the Activity — an activity can appear at more than one stage of the same system.">
            <table className="data-table">
              <thead>
                <tr><th>Stage</th><th style={{ textAlign: "right" }}>Amount</th><th style={{ textAlign: "right" }}>Share</th><th>Basis</th></tr>
              </thead>
              <tbody>
                {data.by_stage.map(s => (
                  <tr key={s.stage}>
                    <td>{s.stage}</td>
                    <td className="num">{s.amount.toFixed(6)}</td>
                    <td className="num">{s.share === null ? "—" : `${(s.share * 100).toFixed(1)}%`}</td>
                    <td>{s.is_proxy ? <Pill tone="amber">proxy factor</Pill> : <Pill tone="green">licensed</Pill>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </GlassCard>

          {data.diagnostics.length > 0 && (
            <GlassCard title={`Diagnostics · ${data.diagnostics.length}`} testId="pef-diagnostics">
              <ul className="muted" style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 4 }}>
                {data.diagnostics.map((d, i) => <li key={i}>{d}</li>)}
              </ul>
            </GlassCard>
          )}
        </>
      )}
    </Outcome>
  );
}

function Questions() {
  const catalog = useApi(() => competencyQuestions(), []);
  const [open, setOpen] = useState<string | null>(null);
  const [answer, setAnswer] = useState<ApiResult<CqResult> | null>(null);
  const [pending, setPending] = useState(false);

  async function run(id: string) {
    setOpen(id);
    setPending(true);
    setAnswer(await runCompetencyQuestion(id));
    setPending(false);
  }

  return (
    <Outcome result={catalog.result} pending={catalog.pending} pendingLabel="loading questions">
      {data => (
        <>
          <GlassCard
            title={`Competency questions · ${data.questions.length} of ${data.total_in_paper}`}
            testId="cq-list"
            subtitle="Each one is a SPARQL query against the graph, tied to the PEF requirement it demonstrates. Running one shows the query as well as the rows, because a result nobody can check is not evidence."
          >
            <div style={{ display: "grid", gap: 8 }}>
              {data.questions.map(q => (
                <div key={q.id} className="evidence-card" style={{ padding: "12px 14px" }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 650, fontSize: 13.5 }}>{q.question}</div>
                      <div className="faint mono" style={{ marginTop: 3 }}>{q.id} · {q.pef_requirement}</div>
                      <div className="muted" style={{ marginTop: 5 }}>{q.why_it_matters}</div>
                    </div>
                    <button className="btn secondary" data-testid={`run-cq-${q.id}`}
                            onClick={() => void run(q.id)} style={{ flexShrink: 0 }}>
                      Run
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          {open && pending && <Loading label={`running ${open}`} />}
          {open && !pending && answer?.kind === "declined" && <DeclinedPanel result={answer} />}
          {open && !pending && answer?.kind === "failed" && <FailedPanel result={answer} />}
          {open && !pending && answer?.kind === "ok" && <CqAnswer result={answer.data} />}
        </>
      )}
    </Outcome>
  );
}

function CqAnswer({ result }: { result: CqResult }) {
  const columns = result.rows[0] ? Object.keys(result.rows[0]) : [];
  return (
    <GlassCard
      title={result.question}
      testId="cq-result"
      subtitle={`${result.id} · ${result.pef_requirement}`}
      actions={<Pill tone={result.answered ? "green" : "coral"}>
        {result.answered ? `${result.rows.length} rows` : "no answer"}
      </Pill>}
    >
      {result.error && <div className="failed" style={{ marginBottom: 14 }}>{result.error}</div>}
      {result.rows.length > 0 && (
        <div style={{ overflowX: "auto", marginBottom: 14 }}>
          <table className="data-table">
            <thead><tr>{columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>
              {result.rows.map((row, i) => (
                <tr key={i}>{columns.map(c => <td key={c} className="mono" style={{ fontSize: 11.5 }}>{row[c] ?? "—"}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="label">The query behind it</div>
      <pre className="mono" style={{
        margin: 0, padding: 12, borderRadius: 10, fontSize: 11,
        background: "rgba(27,18,82,0.05)", overflowX: "auto", lineHeight: 1.5,
      }}>{result.sparql}</pre>
    </GlassCard>
  );
}

const DEFAULT_QUERY = `SELECT ?activity ?stage WHERE {
  ?link a <https://w3id.org/mintjesba/pefdpp/ActivityLink> ;
        <https://w3id.org/mintjesba/pefdpp/linksActivity> ?activity ;
        <https://w3id.org/mintjesba/pefdpp/hasLifeCycleStage> ?stage .
}`;

function Sparql() {
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [result, setResult] = useState<ApiResult<SparqlResult> | null>(null);
  const [pending, setPending] = useState(false);

  async function run() {
    setPending(true);
    setResult(await runSparql(query, 50));
    setPending(false);
  }

  return (
    <>
      <GlassCard
        title="SPARQL"
        testId="sparql-form"
        subtitle="Read-only. Updates and federation are refused before execution rather than after, so a hostile query never reaches the store."
      >
        <textarea
          className="field-control mono"
          data-testid="sparql-input"
          value={query}
          onChange={e => setQuery(e.target.value)}
          spellCheck={false}
          style={{ width: "100%", minHeight: 170, fontSize: 11.5, lineHeight: 1.55, resize: "vertical" }}
        />
        <button className="btn" onClick={() => void run()} disabled={pending}
                data-testid="sparql-submit" style={{ marginTop: 12 }}>
          {pending ? "Running…" : "Run query"}
        </button>
      </GlassCard>

      {pending && <Loading label="querying the graph" />}
      {!pending && result?.kind === "declined" && <DeclinedPanel result={result} />}
      {!pending && result?.kind === "failed" && <FailedPanel result={result} />}
      {!pending && result?.kind === "ok" && (
        <GlassCard
          title={`${result.data.rows.length} rows`}
          testId="sparql-result"
          actions={result.data.truncated ? <Pill tone="amber">truncated</Pill> : undefined}
        >
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead><tr>{result.data.columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
              <tbody>
                {result.data.rows.map((row, i) => (
                  <tr key={i}>
                    {result.data.columns.map(c => (
                      <td key={c} className="mono" style={{ fontSize: 11.5 }}>{row[c] ?? "—"}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}
    </>
  );
}
