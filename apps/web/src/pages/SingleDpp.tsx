import { useRef, useState } from "react";
import { askSingleDpp, parseSingleDpp } from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { ParsedDocument, SingleDppAnswer } from "../lib/types";
import { getTau } from "../lib/mode";
import { AuditPanel } from "../components/AuditPanel";
import { GlassCard, Pill, Stat } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Loading } from "../components/Outcome";
import { ModeWarningBanner } from "../components/ModeBadge";

/**
 * Ask about a passport that is not in the system.
 *
 * Paste or drop a document, see how it was read, ask questions answerable from it
 * alone. Nothing is indexed and nothing is stored — the window holds the document
 * and sends it with each question, so a passport somebody was only checking does
 * not quietly join the corpus.
 *
 * It looks like the Search window on purpose. The same inference path runs behind
 * it, with one adapter swapped, so the same reliability envelope comes back and the
 * audit panel beside the answer is literally the same component. In the demo this
 * window had its own pipeline, its own confidence number and no grounding check at
 * all — the place a user was most likely to paste something unfamiliar had the
 * weakest guarantees in the product.
 */
const EXAMPLE = JSON.stringify(
  {
    dpp_id: "bat-001",
    schema_version: "1.0",
    product: { brand: "Generic", model: "BEV pack 60 kWh", category: "battery" },
    materials: [
      { name: "Lithium", share_pct: 12 },
      { name: "Steel", share_pct: 40 },
    ],
    compliance: { standards: ["EN 62133-2"], ce_marking: true },
  },
  null,
  2,
);

const QUESTIONS = [
  "Which compliance standards does this carry?",
  "What is the material breakdown?",
  "Is CE marking declared?",
];

export default function SingleDpp() {
  const [content, setContent] = useState(EXAMPLE);
  const [filename, setFilename] = useState<string | null>("battery.json");
  const [doc, setDoc] = useState<ApiResult<ParsedDocument> | null>(null);
  const [reading, setReading] = useState(false);
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState<ApiResult<SingleDppAnswer> | null>(null);
  const [asking, setAsking] = useState(false);
  const documentRevision = useRef(0);
  const answerRevision = useRef(0);

  function invalidateDocument() {
    documentRevision.current++;
    answerRevision.current++;
    setDoc(null);
    setAnswer(null);
    setReading(false);
    setAsking(false);
  }

  async function read() {
    const ticket = ++documentRevision.current;
    answerRevision.current++;
    setReading(true);
    setAsking(false);
    setAnswer(null);
    const outcome = await parseSingleDpp(content, filename);
    if (ticket === documentRevision.current) {
      setDoc(outcome);
      setReading(false);
    }
  }

  async function ask(question: string) {
    if (!question.trim()) return;
    const ticket = ++answerRevision.current;
    const documentTicket = documentRevision.current;
    setAsking(true);
    setAnswer(null);
    const outcome = await askSingleDpp(question, content, filename, getTau());
    if (ticket === answerRevision.current && documentTicket === documentRevision.current) {
      setAnswer(outcome);
      setAsking(false);
    }
  }

  async function onFile(file: File | undefined) {
    if (!file) return;
    invalidateDocument();
    const ticket = documentRevision.current;
    const text = await file.text();
    if (ticket !== documentRevision.current) return;
    setContent(text);
    setFilename(file.name);
  }

  return (
    <div className="page" data-testid="page-single-dpp">
      <ModeWarningBanner />

      <GlassCard
        title="Single passport"
        testId="single-form"
        subtitle="A document that is not in the system. Questions are answered from it alone — the indexed corpus is never consulted — and nothing here is stored or indexed."
      >
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10 }}>
          <label className="btn secondary" style={{ cursor: "pointer" }}>
            Choose a file
            <input
              type="file"
              accept=".json,.txt,.md,application/json,text/plain"
              data-testid="single-file"
              style={{ display: "none" }}
              onChange={e => void onFile(e.target.files?.[0])}
            />
          </label>
          {filename && <span className="faint mono">{filename}</span>}
          <span className="faint" style={{ marginLeft: "auto" }}>
            {content.length.toLocaleString()} characters
          </span>
        </div>

        <textarea
          className="field-control mono"
          data-testid="single-input"
          value={content}
          onChange={e => {
            invalidateDocument();
            setContent(e.target.value);
          }}
          spellCheck={false}
          style={{ width: "100%", minHeight: 200, fontSize: 12, lineHeight: 1.5, resize: "vertical" }}
        />
        <button className="btn" onClick={() => void read()} disabled={reading}
                data-testid="single-read" style={{ marginTop: 12 }}>
          {reading ? "Reading…" : "Read the document"}
        </button>
        <p className="faint" style={{ marginTop: 10, marginBottom: 0 }}>
          Reading costs nothing and needs no model — it splits the document on its own
          structure so you can see what was found before asking anything of it.
        </p>
      </GlassCard>

      {reading && <Loading label="reading" />}
      {!reading && doc?.kind === "declined" && <DeclinedPanel result={doc} />}
      {!reading && doc?.kind === "failed" && <FailedPanel result={doc} />}
      {!reading && doc?.kind === "ok" && (
        <>
          <Sections doc={doc.data} />

          <GlassCard title="Ask about this passport" testId="single-ask">
            <form onSubmit={e => { e.preventDefault(); void ask(q); }}
                  style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 10 }}>
              <input
                className="field-control"
                data-testid="single-question"
                value={q}
                onChange={e => {
                  answerRevision.current++;
                  setAnswer(null);
                  setAsking(false);
                  setQ(e.target.value);
                }}
                placeholder="What does this document say about…?"
              />
              <button className="btn" type="submit" disabled={asking || !q.trim()}
                      data-testid="single-submit">
                {asking ? "Asking…" : "Ask"}
              </button>
            </form>
            <div style={{ display: "flex", gap: 7, flexWrap: "wrap", marginTop: 12 }}>
              {QUESTIONS.map(question => (
                <button key={question} className="pill" style={{ cursor: "pointer", fontSize: 11.5 }}
                        onClick={() => { setQ(question); void ask(question); }}>
                  {question}
                </button>
              ))}
            </div>
          </GlassCard>
        </>
      )}

      {asking && <Loading label="asking about this document" />}
      {!asking && answer?.kind === "declined" && <DeclinedPanel result={answer} />}
      {!asking && answer?.kind === "failed" && <FailedPanel result={answer} />}
      {!asking && answer?.kind === "ok" && <Answer result={answer.data} />}
    </div>
  );
}

function Sections({ doc }: { doc: ParsedDocument }) {
  return (
    <GlassCard
      title={`How this was read · ${doc.sections.length} sections`}
      testId="single-sections"
      actions={<Pill tone={doc.document_type === "json" ? "green" : ""}>{doc.document_type}</Pill>}
      subtitle="Split on the document's own structure, not on length: a passport keeps its meaning in its keys, and chunking by character count cuts across them."
    >
      {doc.warnings.length > 0 && (
        <div className="declined" style={{ marginBottom: 14 }} data-testid="single-warnings">
          <div className="head">⚠ About this document</div>
          <div className="reason">{doc.warnings.join(" ")}</div>
        </div>
      )}
      <div style={{ display: "flex", gap: 30, marginBottom: 16 }}>
        <Stat label="Title" value={doc.title} />
        <Stat label="Characters" value={doc.char_count.toLocaleString()} />
      </div>
      <table className="data-table">
        <thead><tr><th>Section</th><th>Pointer</th><th>What is in it</th></tr></thead>
        <tbody>
          {doc.sections.map(s => (
            <tr key={s.id} data-testid={`section-${s.id}`}>
              <td><strong>{s.title}</strong></td>
              <td className="mono" style={{ fontSize: 11.5 }}>{s.path || "(root)"}</td>
              <td className="muted">{s.summary}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </GlassCard>
  );
}

function Answer({ result }: { result: SingleDppAnswer }) {
  const abstained = result.decision !== "answer";
  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1.55fr) minmax(320px,1fr)", gap: 14, alignItems: "start" }}>
      <div style={{ display: "grid", gap: 14, minWidth: 0 }}>
        <div className="glass answer-surface" style={{ padding: 22 }} data-testid="single-answer">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <Pill tone={abstained ? "amber" : "green"}>{abstained ? "abstained" : "answered"}</Pill>
            <span className="faint mono">{result.document.filename ?? "document"}</span>
          </div>
          {abstained ? (
            <div data-testid="single-abstention">
              <p style={{ margin: "0 0 10px", fontSize: 15 }}>
                <strong>The system declined to answer from this document.</strong>
              </p>
              <p className="muted" style={{ margin: 0 }}>{result.abstain_reason}</p>
            </div>
          ) : (
            <p style={{ margin: 0, fontSize: 15, lineHeight: 1.65, whiteSpace: "pre-wrap" }}>
              {result.answer}
            </p>
          )}
        </div>

        {result.evidence.length > 0 && (
          <GlassCard title={`From these sections · ${result.evidence.length}`} testId="single-evidence">
            <div style={{ display: "grid", gap: 9 }}>
              {result.evidence.map(e => (
                <div key={e.id} className="evidence-card" style={{ padding: "11px 13px" }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 5 }}>
                    <Pill tone="teal">{e.kind}</Pill>
                    <span className="mono" style={{ fontSize: 11.5 }}>{e.ref}</span>
                    {e.score !== null && (
                      <span className="faint mono" style={{ marginLeft: "auto" }}>{e.score.toFixed(3)}</span>
                    )}
                  </div>
                  <div className="muted mono" style={{ fontSize: 11.5, whiteSpace: "pre-wrap" }}>{e.text}</div>
                </div>
              ))}
            </div>
          </GlassCard>
        )}
      </div>

      {/* The same panel the main search window uses, because the same path ran. */}
      <AuditPanel result={result} />
    </div>
  );
}
