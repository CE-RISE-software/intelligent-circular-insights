import { useState } from "react";
import { validateDpp, validationProfiles } from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { ValidationReport } from "../lib/types";
import { GlassCard, Pill, Stat } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Loading, Outcome } from "../components/Outcome";
import { ModeWarningBanner } from "../components/ModeBadge";
import { useApi } from "../lib/useApi";

const SAMPLES: Record<string, string> = {
  "Empty record": "{}",
  "Missing compliance": JSON.stringify(
    { dpp_id: "bat-001", product: { name: "Battery pack", category: "battery" }, materials: [] },
    null, 2,
  ),
  "Wrong types": JSON.stringify(
    { dpp_id: 42, product: "a string where an object belongs", materials: "not a list" },
    null, 2,
  ),
};

export default function Validate() {
  const profiles = useApi(() => validationProfiles(), []);
  const [profile, setProfile] = useState("eu-dpp");
  const [text, setText] = useState(SAMPLES["Missing compliance"] ?? "{}");
  const [parseError, setParseError] = useState<string | null>(null);
  const [result, setResult] = useState<ApiResult<ValidationReport> | null>(null);
  const [pending, setPending] = useState(false);

  async function run() {
    let parsed: unknown;
    try {
      parsed = JSON.parse(text);
    } catch (err) {
      // Caught here rather than sent: a malformed document is the editor's
      // problem, and a 422 from the backend would say something less useful.
      setParseError(err instanceof Error ? err.message : "not valid JSON");
      return;
    }
    setParseError(null);
    setPending(true);
    setResult(await validateDpp(parsed, profile));
    setPending(false);
  }

  return (
    <div className="page" data-testid="page-validate">
      <ModeWarningBanner />
      <GlassCard
        title="Validate"
        subtitle="Conformance against a schema profile. Violations are typed and located, because a bare boolean is useless to whoever has to repair the record."
        testId="validate-form"
      >
        <Outcome result={profiles.result} pending={profiles.pending} pendingLabel="loading profiles">
          {data => (
            <div style={{ marginBottom: 14 }}>
              <div className="label">Profile</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {data.profiles.map(p => (
                  <button
                    key={p.id}
                    className={"pill " + (p.id === profile ? "teal" : "")}
                    data-testid={`profile-${p.id}`}
                    onClick={() => setProfile(p.id)}
                    title={`${p.title} · ${p.layer}${p.version ? ` · ${p.version}` : ""}`}
                    style={{ cursor: "pointer", fontSize: 11.5 }}
                  >
                    {p.title}
                  </button>
                ))}
              </div>
            </div>
          )}
        </Outcome>

        <div className="label">Record</div>
        <div style={{ display: "flex", gap: 7, flexWrap: "wrap", marginBottom: 9 }}>
          {Object.entries(SAMPLES).map(([name, body]) => (
            <button key={name} className="pill" style={{ cursor: "pointer", fontSize: 11.5 }}
                    onClick={() => { setText(body); setParseError(null); }}>
              {name}
            </button>
          ))}
        </div>
        <textarea
          className="field-control mono"
          data-testid="validate-input"
          value={text}
          onChange={e => setText(e.target.value)}
          spellCheck={false}
          style={{ width: "100%", minHeight: 210, fontSize: 12, lineHeight: 1.5, resize: "vertical" }}
        />
        {parseError && (
          <p style={{ color: "#8f2222", fontSize: 12.5, margin: "8px 0 0" }} data-testid="parse-error">
            Not valid JSON — {parseError}
          </p>
        )}
        <button className="btn" onClick={() => void run()} disabled={pending}
                data-testid="validate-submit" style={{ marginTop: 14 }}>
          {pending ? "Checking…" : "Check conformance"}
        </button>
      </GlassCard>

      {pending && <Loading label="checking conformance" />}
      {!pending && result?.kind === "declined" && <DeclinedPanel result={result} />}
      {!pending && result?.kind === "failed" && <FailedPanel result={result} />}
      {!pending && result?.kind === "ok" && <Report report={result.data} />}
    </div>
  );
}

function Report({ report }: { report: ValidationReport }) {
  return (
    <GlassCard
      title="Conformance report"
      testId="validate-result"
      actions={
        <Pill tone={report.conforms ? "green" : "coral"}>
          {report.conforms ? "conforms" : `${report.violations.length} violations`}
        </Pill>
      }
    >
      <div style={{ display: "flex", gap: 30, marginBottom: 18 }}>
        <Stat label="Profile" value={report.profile} />
        <Stat label="Paths checked" value={report.checked_paths} />
        <Stat label="Violations" value={report.violations.length} />
      </div>
      {report.violations.length === 0 ? (
        <p className="muted" style={{ margin: 0 }}>Nothing to repair.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr><th>Kind</th><th>Location</th><th>Message</th><th>Expected</th><th>Actual</th></tr>
          </thead>
          <tbody>
            {report.violations.map((v, i) => (
              <tr key={`${v.location}-${i}`}>
                <td><Pill tone="coral">{v.kind}</Pill></td>
                <td className="mono" style={{ fontSize: 11.5 }}>{v.location || "(root)"}</td>
                <td>{v.message}</td>
                <td className="mono" style={{ fontSize: 11.5 }}>{v.expected ?? "—"}</td>
                <td className="mono" style={{ fontSize: 11.5 }}>{v.actual ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </GlassCard>
  );
}
