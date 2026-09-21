import { useState } from "react";
import { carbonCalculate, pefCalculate, search, validateDpp } from "../lib/api";
import type { ApiResult } from "../lib/api";
import type { CarbonResult, PefResult, SearchResult, ValidationReport } from "../lib/types";
import { GlassCard, Pill } from "../components/GlassCard";
import { DeclinedPanel, FailedPanel, Loading } from "../components/Outcome";
import { MODE_LABELS, getTau, type BackendMode } from "../lib/mode";

/**
 * The same question, put to both backends at once.
 *
 * This view exists because the claim the project makes — two levels of rigour
 * under one interface, with a visible upgrade path between them — is much easier
 * to *see* than to describe. Both requests pass an explicit mode, which the client
 * deliberately excludes from the served-mode badge: the header must keep reporting
 * the session's own backend, not whichever of these two replied last.
 *
 * The interesting cells are the ones where the backends disagree, and the ones
 * where one of them honestly declines.
 */
const MODES: readonly BackendMode[] = ["normal", "ce-rise"] as const;

type Probe = "carbon" | "search" | "validate" | "footprint";

const PROBES: Record<Probe, { label: string; blurb: string }> = {
  carbon: {
    label: "Carbon · fairphone_4",
    blurb: "A product profile both backends can assess. The numbers should be identical: CE-RISE adds the graph without displacing the CSV engine, so a shared feature must survive the switch.",
  },
  footprint: {
    label: "Footprint · graph-solved",
    blurb: "A product system solved off RDF. Normal mode has no graph mounted and says so; this is where the modes genuinely differ.",
  },
  search: {
    label: "Search · recycled content",
    blurb: "The same question through the same inference path, with a different substrate underneath.",
  },
  validate: {
    label: "Validate · empty record",
    blurb: "Conformance is schema-driven and mode-independent. Identical output here is the control.",
  },
};

export default function Compare() {
  const [probe, setProbe] = useState<Probe>("carbon");
  const [left, setLeft] = useState<ApiResult<unknown> | null>(null);
  const [right, setRight] = useState<ApiResult<unknown> | null>(null);
  const [pending, setPending] = useState(false);

  async function run(which: Probe) {
    setProbe(which);
    setPending(true);
    setLeft(null);
    setRight(null);
    const [a, b] = await Promise.all(MODES.map(m => call(which, m)));
    setLeft(a ?? null);
    setRight(b ?? null);
    setPending(false);
  }

  return (
    <div className="page" data-testid="page-compare">
      <GlassCard
        title="Compare backends"
        testId="compare-form"
        subtitle="One question, both backends, side by side. Where they agree, the switch is safe; where they differ, the difference is the product."
      >
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {(Object.keys(PROBES) as Probe[]).map(p => (
            <button
              key={p}
              className={"pill " + (p === probe ? "teal" : "")}
              data-testid={`probe-${p}`}
              onClick={() => void run(p)}
              style={{ cursor: "pointer", fontSize: 11.5 }}
            >
              {PROBES[p].label}
            </button>
          ))}
        </div>
        <p className="faint" style={{ marginTop: 12, marginBottom: 0 }}>{PROBES[probe].blurb}</p>
      </GlassCard>

      {pending && <Loading label="asking both backends" />}

      {!pending && (left || right) && (
        <div className="compare-grid" data-testid="compare-grid">
          {MODES.map((m, i) => (
            <div className="compare-col" key={m}>
              <div className="compare-head">
                <strong style={{ color: "var(--cerise-navy)", fontSize: 14 }}>{MODE_LABELS[m]}</strong>
                <span className={`mode-badge ${m}`}><span className="dot" />{m}</span>
              </div>
              <Panel probe={probe} result={(i === 0 ? left : right) as ApiResult<unknown> | null} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

async function call(probe: Probe, mode: BackendMode): Promise<ApiResult<unknown>> {
  switch (probe) {
    case "carbon":
      return carbonCalculate("fairphone_4", mode);
    case "footprint":
      return pefCalculate({}, mode);
    case "search":
      return search({ q: "What is the recycled content of the battery?", tau: getTau() }, mode);
    case "validate":
      return validateDpp({}, "eu-dpp", mode);
  }
}

function Panel({ probe, result }: { probe: Probe; result: ApiResult<unknown> | null }) {
  if (result === null) return null;
  if (result.kind === "declined") return <DeclinedPanel result={result} />;
  if (result.kind === "failed") return <FailedPanel result={result} />;

  if (probe === "carbon") return <CarbonPanel data={result.data as CarbonResult} />;
  if (probe === "footprint") return <FootprintPanel data={result.data as PefResult} />;
  if (probe === "validate") return <ValidatePanel data={result.data as ValidationReport} />;
  return <SearchPanel data={result.data as SearchResult} />;
}

function Row({ label, value, mono = true }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 14, padding: "5px 0", fontSize: 12.5 }}>
      <span className="muted">{label}</span>
      <span className={mono ? "mono" : ""} style={{ textAlign: "right" }}>{value}</span>
    </div>
  );
}

function CarbonPanel({ data }: { data: CarbonResult }) {
  return (
    <div className="glass" style={{ padding: 18 }}>
      <Row label="Total" value={`${data.total.toFixed(4)} ${data.unit}`} />
      <Row label="Functional unit" value={data.functional_unit ?? "—"} mono={false} />
      <Row label="Stages" value={data.contributions.length} />
      <Row label="Proxy factors" value={data.uses_proxy_factors ? "yes" : "no"} />
      <Row label="Diagnostics" value={data.diagnostics.length} />
    </div>
  );
}

function FootprintPanel({ data }: { data: PefResult }) {
  return (
    <div className="glass" style={{ padding: 18 }}>
      <Row label="Total" value={`${data.total.toFixed(6)} ${data.unit}`} />
      <Row label="Functional unit" value={data.functional_unit ?? "—"} mono={false} />
      <Row label="Weighted DQR" value={data.data_quality?.toFixed(4) ?? "—"} />
      <Row label="Stages" value={data.by_stage.length} />
    </div>
  );
}

function ValidatePanel({ data }: { data: ValidationReport }) {
  return (
    <div className="glass" style={{ padding: 18 }}>
      <Row label="Profile" value={data.profile} />
      <Row label="Conforms" value={data.conforms ? "yes" : "no"} />
      <Row label="Paths checked" value={data.checked_paths} />
      <Row label="Violations" value={data.violations.length} />
    </div>
  );
}

function SearchPanel({ data }: { data: SearchResult }) {
  return (
    <div className="glass" style={{ padding: 18 }}>
      <div style={{ marginBottom: 10 }}>
        <Pill tone={data.decision === "answer" ? "green" : "amber"}>{data.decision}</Pill>
      </div>
      <Row label="Calibrated" value={data.confidence.calibrated.toFixed(3)} />
      <Row label="τ" value={data.operating_point.tau.toFixed(2)} />
      <Row label="Grounding" value={data.grounding.verdict} />
      <Row label="Evidence" value={data.evidence.length} />
      <Row label="Weak signal" value={data.weak_signal ?? "—"} />
      <p className="muted" style={{ marginTop: 12, marginBottom: 0, fontSize: 12.5 }}>
        {data.decision === "answer" ? data.answer : data.abstain_reason}
      </p>
    </div>
  );
}
