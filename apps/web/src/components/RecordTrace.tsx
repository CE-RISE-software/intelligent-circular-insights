import type { SearchResult } from "../lib/types";
import { GlassCard } from "./GlassCard";

export function RecordTrace({ trace, testId }: { trace: SearchResult["trace"]; testId: string }) {
  return <GlassCard title="Request audit" testId={testId}>
    <p className="muted">
      Model · {trace.model ?? "not called"} · live attempts {trace.cost.llm_calls}
      {" "}· estimated spend ${trace.cost.usd.toFixed(6)}
    </p>
    {trace.steps.map((s, i) => <p key={i} className="faint"><strong>{s.name}</strong> — {s.detail}</p>)}
    {trace.prompt_hashes.map((hash, i) => <p key={i} className="faint mono" style={{ overflowWrap: "anywhere" }}>
      prompt hash · {hash}
    </p>)}
  </GlassCard>;
}
