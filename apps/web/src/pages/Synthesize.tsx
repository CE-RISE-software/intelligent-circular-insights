import { useState } from "react";
import { synthesizeDpp, validationProfiles } from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { SynthesisResult } from "../lib/types";
import { GlassCard, Pill, Stat } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Loading, Outcome } from "../components/Outcome";
import { ModeWarningBanner } from "../components/ModeBadge";
import { useApi } from "../lib/useApi";

/**
 * Build a passport from a few facts — or be told, with a reason, that it cannot be.
 *
 * The strictest window in the workbench, and the page is written to make that feel
 * like the feature rather than an obstacle. There is no partial result: the record
 * is generated, grounded field by field, and re-checked against the bound profile,
 * and anything short of all three is a decline with the reason on screen. A
 * plausible invalid passport is worse than no passport.
 *
 * Unlike repair, there is no suggestions panel here. Repair mends a document
 * somebody wrote and can review; synthesis writes one from nothing, where an
 * unverified field has no author to answer for it.
 */
const EXAMPLES: Record<string, string> = {
  "Battery pack": JSON.stringify(
    { dpp_id: "bat-001", product: { brand: "Generic", model: "BEV pack 60 kWh" } },
    null, 2,
  ),
  "Nothing retrievable": JSON.stringify(
    { dpp_id: "zzz-000", product: { brand: "Qqzzx", model: "Wubbleflorp 9000" } },
    null, 2,
  ),
};

export default function Synthesize() {
  const profiles = useApi(() => validationProfiles(), []);
  const [profile, setProfile] = useState("eu-dpp");
  const [text, setText] = useState(EXAMPLES["Battery pack"] ?? "{}");
  const [parseError, setParseError] = useState<string | null>(null);
  const [result, setResult] = useState<ApiResult<SynthesisResult> | null>(null);
  const [pending, setPending] = useState(false);

  async function run() {
    let seed: unknown;
    try {
      seed = JSON.parse(text);
    } catch (err) {
      setParseError(err instanceof Error ? err.message : "not valid JSON");
      return;
    }
    setParseError(null);
    setPending(true);
    setResult(await synthesizeDpp(seed, profile));
    setPending(false);
  }

  return (
    <div className="page" data-testid="page-synthesize">
      <ModeWarningBanner />
      <GlassCard
        title="Synthesize a passport"
        testId="synthesize-form"
        subtitle="Supply what you know. Everything else has to be grounded in retrievable evidence about this product — if it cannot be, the request is declined rather than filled in."
      >
        <Outcome result={profiles.result} pending={profiles.pending} pendingLabel="loading profiles">
          {data => (
            <div style={{ marginBottom: 14 }}>
              <div className="label">Target profile</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {data.profiles.map(p => (
                  <button
                    key={p.id}
                    className={"pill " + (p.id === profile ? "teal" : "")}
                    data-testid={`synth-profile-${p.id}`}
                    onClick={() => setProfile(p.id)}
                    style={{ cursor: "pointer", fontSize: 11.5 }}
                  >
                    {p.title}
                  </button>
                ))}
              </div>
            </div>
          )}
        </Outcome>

        <div className="label">Seed facts</div>
        <div style={{ display: "flex", gap: 7, flexWrap: "wrap", marginBottom: 9 }}>
          {Object.entries(EXAMPLES).map(([name, body]) => (
            <button key={name} className="pill" style={{ cursor: "pointer", fontSize: 11.5 }}
                    onClick={() => { setText(body); setParseError(null); }}>
              {name}
            </button>
          ))}
        </div>
        <textarea
          className="field-control mono"
          data-testid="synth-input"
          value={text}
          onChange={e => setText(e.target.value)}
          spellCheck={false}
          style={{ width: "100%", minHeight: 180, fontSize: 12, lineHeight: 1.5, resize: "vertical" }}
        />
        {parseError && (
          <p style={{ color: "#8f2222", fontSize: 12.5, margin: "8px 0 0" }} data-testid="synth-parse-error">
            Not valid JSON — {parseError}
          </p>
        )}
        <button className="btn" onClick={() => void run()} disabled={pending}
                data-testid="synth-submit" style={{ marginTop: 14 }}>
          {pending ? "Building…" : "Build the passport"}
        </button>
        <p className="faint" style={{ marginTop: 12, marginBottom: 0 }}>
          This one costs a model call. Conformance checking on the Validate window does not,
          and neither does either impact engine.
        </p>
      </GlassCard>

      {pending && <Loading label="gathering evidence and composing" />}
      {!pending && result?.kind === "declined" && <DeclinedPanel result={result} />}
      {!pending && result?.kind === "failed" && <FailedPanel result={result} />}
      {!pending && result?.kind === "ok" && <Passport result={result.data} />}
    </div>
  );
}

function Passport({ result }: { result: SynthesisResult }) {
  return (
    <>
      <GlassCard
        title={result.dpp_id}
        testId="synth-result"
        actions={<Pill tone="green">conforms to {result.profile}</Pill>}
        subtitle="Returned only because it conforms. The use case raises rather than handing back a record with a caveat attached."
      >
        <div style={{ display: "flex", gap: 30, marginBottom: 16 }}>
          <Stat label="Passport id" value={result.dpp_id} />
          <Stat label="Profile" value={result.profile} />
          <Stat label="Fields" value={Object.keys(result.record).length} />
        </div>
        <pre className="mono" style={{
          margin: 0, padding: 14, borderRadius: 10, fontSize: 11.5, lineHeight: 1.55,
          background: "rgba(27,18,82,0.05)", overflowX: "auto", maxHeight: 420,
        }}>{JSON.stringify(result.record, null, 2)}</pre>
      </GlassCard>

      {result.trace.steps.length > 0 && (
        <GlassCard title="How this was built" testId="synth-trace">
          <div style={{ display: "grid", gap: 6 }}>
            {result.trace.steps.map((s, i) => (
              <div key={`${s.name}-${i}`} style={{ display: "grid", gridTemplateColumns: "22px 1fr", gap: 8 }}>
                <span className="faint mono">{i + 1}</span>
                <span style={{ fontSize: 12.5 }}>
                  <strong>{s.name}</strong>
                  {s.detail && <span className="muted"> — {s.detail}</span>}
                </span>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </>
  );
}
