import type { GroundedFill, RecordIssue, RepairResult, UnverifiedSuggestion } from "../lib/types";
import { GlassCard, Pill } from "./GlassCard";
import { RecordTrace } from "./RecordTrace";

/**
 * The result of an evidence-backed repair.
 *
 * The layout carries a rule, not just a style. Grounded fills and unverified
 * suggestions are rendered in *different surfaces*, under different headings, with
 * different colours and a different verb — "filled from" versus "proposed for
 * review". ADR 0011 requires them kept apart in the payload; keeping them apart in
 * the payload and then showing them in one table would undo that at the only point
 * a person actually looks.
 *
 * The suggestion area is deliberately the least inviting thing on the page. It has
 * no apply button. A value that nothing in the evidence supports should cost a
 * human decision to accept, and a one-click "accept all" is how a guess ends up in
 * a compliance document with nobody's name against it.
 */
export function RecordAssist({ result }: { result: RepairResult }) {
  return (
    <>
      <GlassCard
        title="Repair"
        testId="repair-result"
        actions={
          <Pill tone={result.conforms ? "green" : "coral"}>
            {result.conforms ? "conforms after repair" : `${result.after.violations.length} still open`}
          </Pill>
        }
        subtitle="Every field below was filled because a retrieved source stated it. Nothing here comes from the model's own knowledge."
      >
        {result.grounded_fills.length === 0 ? (
          <p className="muted" style={{ margin: 0 }} data-testid="no-fills">
            No field could be filled from evidence. That is a result, not a failure —
            it says the sources do not contain what this record is missing.
          </p>
        ) : (
          <table className="data-table" data-testid="grounded-fills">
            <thead>
              <tr>
                <th>Field</th>
                <th>Filled with</th>
                <th>Because this source said so</th>
                <th style={{ textAlign: "right" }}>Model score</th>
              </tr>
            </thead>
            <tbody>
              {result.grounded_fills.map((f: GroundedFill) => (
                <tr key={f.path} data-testid={`fill-${f.path}`}>
                  <td className="mono" style={{ fontSize: 11.5 }}>{f.path}</td>
                  <td><strong>{render(f.value)}</strong></td>
                  <td>
                    <span className="mono" style={{ fontSize: 11.5 }}>{f.evidence_ref}</span>
                    <div className="faint mono">{f.evidence_id} · {f.source_pointer}</div>
                  </td>
                  <td className="num" title="A model feature, not a calibrated probability. Not comparable with a search result's confidence.">
                    {f.model_score.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </GlassCard>

      {(result.cannot_be_grounded.length > 0 || result.rejected.length > 0) && (
        <GlassCard
          title="Left open"
          testId="unresolved"
          subtitle="Reported rather than filled. A gap named is a gap someone can close; a gap guessed is a gap nobody knows about."
        >
          <IssueList label="No source states this" issues={result.cannot_be_grounded} testId="cannot-ground" />
          <IssueList label="Proposed but not supported" issues={result.rejected} testId="rejected" />
        </GlassCard>
      )}

      {result.unverified_suggestions.length > 0 && (
        <SuggestionReview suggestions={result.unverified_suggestions} />
      )}

      <GlassCard title="Repaired preview · suggestions not applied" testId="repair-preview">
        <pre className="mono" style={{ overflowX: "auto" }}>{JSON.stringify(result.record, null, 2)}</pre>
      </GlassCard>
      <RecordTrace trace={result.trace} testId="repair-trace" />
    </>
  );
}

function IssueList({ label, issues, testId }: { label: string; issues: RecordIssue[]; testId: string }) {
  if (issues.length === 0) return null;
  return (
    <div style={{ marginBottom: 14 }} data-testid={testId}>
      <div className="label">{label} · {issues.length}</div>
      <table className="data-table">
        <tbody>
          {issues.map((i, n) => (
            <tr key={`${i.path}-${n}`}>
              <td className="mono" style={{ fontSize: 11.5, width: 240 }}>{i.path || "(root)"}</td>
              <td className="muted">{i.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Model-prior candidates, quarantined.
 *
 * Its own surface, its own warning, its own colour, and no way to apply anything
 * from here. The heading says what these are before the values appear, because by
 * the time someone has read a plausible value they have already half-believed it.
 */
function SuggestionReview({ suggestions }: { suggestions: UnverifiedSuggestion[] }) {
  return (
    <section className="suggestion-review" data-testid="unverified-suggestions">
      <header>
        <span className="tag">not evidence</span>
        <h3>For human review · {suggestions.length}</h3>
      </header>
      <p>
        These came from the model's own training, not from any source in this workspace.
        Nothing here has been applied to the record and nothing here has been checked.
        Treat each one as a question to answer, not an answer to accept — and record
        where you verified it before it goes into a passport.
      </p>
      <table className="data-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Suggested</th>
            <th>Why the model thinks so</th>
            <th style={{ textAlign: "right" }}>Model score</th>
          </tr>
        </thead>
        <tbody>
          {suggestions.map((s, i) => (
            <tr key={`${s.path}-${i}`} data-testid={`suggestion-${s.path}`}>
              <td className="mono" style={{ fontSize: 11.5 }}>{s.path}</td>
              <td>{render(s.value)}</td>
              <td className="muted">{s.rationale}</td>
              <td className="num">{s.model_score.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <footer>
        Model scores are capped at 0.30 and are not calibrated probabilities.{" "}
        {suggestions.every(s => s.requires_review)
          ? "Every row above requires review."
          : "Some rows above require review."}{" "}
        Source: <span className="mono">{suggestions[0]?.source ?? "model_training"}</span>.
      </footer>
    </section>
  );
}

function render(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
