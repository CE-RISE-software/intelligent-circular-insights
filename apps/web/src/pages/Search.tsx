import { useState } from "react";
import { search } from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { SearchResult } from "../lib/types";
import { getTau } from "../lib/mode";
import { AuditPanel } from "../components/AuditPanel";
import { GlassCard, Pill } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Loading } from "../components/Outcome";
import { ModeWarningBanner } from "../components/ModeBadge";
import { useRequestedMode } from "../lib/useApi";

/**
 * The reliability path, end to end.
 *
 * An abstention is displayed as prominently as an answer, in the same surface and
 * with the same audit panel beside it. That is a deliberate inversion of the usual
 * pattern, where declining is rendered as a failure in grey text: here, declining
 * is the system working, and the envelope beside it says exactly why.
 */
const EXAMPLES = [
  "What is the recycled cobalt content of the battery pack?",
  "Which compliance certificates does the Fairphone 4 carry?",
  "What is the declared carbon footprint per functional unit?",
  "Is lead present above the RoHS threshold?",
];

export default function Search() {
  const mode = useRequestedMode();
  const [q, setQ] = useState("");
  const [product, setProduct] = useState("");
  const [result, setResult] = useState<ApiResult<SearchResult> | null>(null);
  const [pending, setPending] = useState(false);

  async function ask(question: string) {
    if (!question.trim()) return;
    setPending(true);
    const r = await search({
      q: question,
      product: product.trim() || null,
      tau: getTau(),
      session: "workbench",
    });
    setResult(r);
    setPending(false);
  }

  return (
    <div className="page" data-testid="page-search">
      <ModeWarningBanner />
      <GlassCard
        title="Search & Answer"
        subtitle="Retrieval, persistent fact memory, symbolic validation and a selective decision. The system answers when its calibrated confidence clears τ, and declines when it does not."
        testId="search-form"
      >
        <form
          onSubmit={e => {
            e.preventDefault();
            void ask(q);
          }}
          style={{ display: "grid", gap: 12 }}
        >
          <div>
            <label className="label" htmlFor="q">Question</label>
            <input
              id="q"
              className="field-control"
              data-testid="search-input"
              value={q}
              onChange={e => setQ(e.target.value)}
              placeholder="Ask about a product record…"
              style={{ width: "100%" }}
            />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, alignItems: "end" }}>
            <div>
              <label className="label" htmlFor="product">
                Scope to a product <span style={{ textTransform: "none", fontWeight: 500 }}>(optional)</span>
              </label>
              <input
                id="product"
                className="field-control"
                data-testid="search-product"
                value={product}
                onChange={e => setProduct(e.target.value)}
                placeholder="fairphone_4"
                style={{ width: "100%" }}
              />
            </div>
            <button className="btn" type="submit" disabled={pending || !q.trim()} data-testid="search-submit">
              {pending ? "Asking…" : "Ask"}
            </button>
          </div>
        </form>
        <p className="faint" style={{ marginTop: 12, marginBottom: 0 }}>
          Scoping is not cosmetic: fact memory is product-scoped, so an unscoped question can only
          use recalled facts that carry no product of their own.
        </p>
        <div style={{ display: "flex", gap: 7, flexWrap: "wrap", marginTop: 14 }}>
          {EXAMPLES.map(e => (
            <button
              key={e}
              className="pill"
              style={{ cursor: "pointer", fontSize: 11.5 }}
              onClick={() => { setQ(e); void ask(e); }}
            >
              {e}
            </button>
          ))}
        </div>
      </GlassCard>

      {pending && <Loading label={`asking the ${mode} backend`} />}
      {!pending && result?.kind === "declined" && <DeclinedPanel result={result} />}
      {!pending && result?.kind === "failed" && <FailedPanel result={result} />}
      {!pending && result?.kind === "ok" && <Answer result={result.data} />}
    </div>
  );
}

function Answer({ result }: { result: SearchResult }) {
  const abstained = result.decision !== "answer";
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1.55fr) minmax(320px,1fr)", gap: 14, alignItems: "start" }}>
      <div style={{ display: "grid", gap: 14, minWidth: 0 }}>
        <div className="glass answer-surface" style={{ padding: 22 }} data-testid="answer">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <Pill tone={abstained ? "amber" : "green"}>
              {abstained ? "abstained" : "answered"}
            </Pill>
            <span className="faint mono">{result.mode}</span>
          </div>
          {abstained ? (
            <div data-testid="abstention">
              <p style={{ margin: "0 0 10px", fontSize: 15, lineHeight: 1.55 }}>
                <strong>The system declined to answer.</strong>
              </p>
              <p className="muted" style={{ margin: 0 }}>
                {result.abstain_reason ??
                  "Calibrated confidence did not clear the operating point."}
              </p>
              <p className="faint" style={{ marginTop: 12, marginBottom: 0 }}>
                A decline is a result, not a failure. The panel beside this says which signal was
                weak, so the gap can be closed by adding evidence rather than by lowering τ.
              </p>
            </div>
          ) : (
            <p className="answer-copy" style={{ margin: 0, fontSize: 15, lineHeight: 1.65, whiteSpace: "pre-wrap" }}>
              {result.answer}
            </p>
          )}
        </div>

        {result.evidence.length > 0 && (
          <GlassCard title={`Evidence · ${result.evidence.length}`} testId="evidence">
            <div style={{ display: "grid", gap: 9 }}>
              {result.evidence.map(e => (
                <div key={e.id} className="evidence-card" style={{ padding: "11px 13px" }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 5 }}>
                    <Pill tone="teal">{e.kind}</Pill>
                    <span className="mono" style={{ fontSize: 11.5 }}>{e.ref}</span>
                    <span className="faint mono" style={{ marginLeft: "auto" }}>{e.score.toFixed(3)}</span>
                  </div>
                  <div className="muted" style={{ fontSize: 12.5 }}>{e.text}</div>
                </div>
              ))}
            </div>
          </GlassCard>
        )}
      </div>

      <AuditPanel result={result} />
    </div>
  );
}
