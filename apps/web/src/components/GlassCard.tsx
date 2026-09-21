import type { CSSProperties, ReactNode } from "react";

export function GlassCard({
  title,
  subtitle,
  actions,
  children,
  style,
  variant = "",
  testId,
}: {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  style?: CSSProperties;
  variant?: string;
  testId?: string;
}) {
  return (
    <section className={`glass ${variant}`} style={{ padding: 20, ...style }} data-testid={testId}>
      {(title || actions) && (
        <header
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 16,
            marginBottom: subtitle ? 6 : 14,
          }}
        >
          <h3 style={{ margin: 0, fontSize: 15, letterSpacing: 0.1, color: "var(--cerise-navy)" }}>
            {title}
          </h3>
          {actions && <div style={{ display: "flex", gap: 8 }}>{actions}</div>}
        </header>
      )}
      {subtitle && <p className="muted" style={{ margin: "0 0 14px" }}>{subtitle}</p>}
      {children}
    </section>
  );
}

export function Stat({
  label,
  value,
  unit,
  hint,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  hint?: string;
}) {
  return (
    <div title={hint}>
      <div className="label">{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color: "var(--cerise-navy)", lineHeight: 1.15 }}>
        <span className="mono">{value}</span>
        {unit && <span style={{ fontSize: 12, marginLeft: 6, opacity: 0.6, fontWeight: 600 }}>{unit}</span>}
      </div>
    </div>
  );
}

export function Pill({ tone = "", children, title }: { tone?: string; children: ReactNode; title?: string }) {
  return <span className={`pill ${tone}`} title={title}>{children}</span>;
}
