import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { getSettings } from "./lib/api";
import type { Settings } from "./lib/types";
import { ModeBadge } from "./components/ModeBadge";
import { SettingsModal } from "./components/SettingsModal";
import Search from "./pages/Search";
import Carbon from "./pages/Carbon";
import Validate from "./pages/Validate";
import CeRiseModels from "./pages/CeRiseModels";
import PefStudio from "./pages/PefStudio";
import Compare from "./pages/Compare";

const PEF_SUBNAV = [
  { to: "/pef/overview", label: "Overview" },
  { to: "/pef/calculator", label: "Calculator" },
  { to: "/pef/questions", label: "Competency questions" },
  { to: "/pef/sparql", label: "SPARQL" },
];

interface NavItem {
  to: string;
  label: string;
  glyph: string;
  subnav?: Array<{ to: string; label: string }>;
}

const NAV: NavItem[] = [
  { to: "/search", label: "Search & Answer", glyph: "🔍" },
  { to: "/carbon", label: "Carbon", glyph: "🌿" },
  { to: "/validate", label: "Validate", glyph: "✅" },
  { to: "/models", label: "CE-RISE Models", glyph: "🧭" },
  { to: "/pef", label: "PEF Studio", glyph: "⚗️", subnav: PEF_SUBNAV },
  { to: "/compare", label: "Compare backends", glyph: "⚖️" },
];

export default function App() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    void getSettings().then(r => {
      if (r.kind === "ok") setSettings(r.data);
    });
  }, []);

  return (
    <div style={{ display: "grid", gridTemplateRows: "auto 1fr", height: "100%" }}>
      <Header settings={settings} onSettings={() => setSettingsOpen(true)} />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "236px 1fr",
          gap: 16,
          padding: 16,
          minHeight: 0,
          height: "100%",
          overflow: "hidden",
        }}
      >
        <Sidebar />
        <main style={{ minHeight: 0, height: "100%", overflow: "hidden" }}>
          <Routes>
            <Route path="/" element={<Navigate to="/search" replace />} />
            <Route path="/search" element={<Search />} />
            <Route path="/carbon" element={<Carbon />} />
            <Route path="/validate" element={<Validate />} />
            <Route path="/models" element={<CeRiseModels />} />
            <Route path="/pef" element={<Navigate to="/pef/overview" replace />} />
            <Route path="/pef/overview" element={<PefStudio tab="overview" />} />
            <Route path="/pef/calculator" element={<PefStudio tab="calculator" />} />
            <Route path="/pef/questions" element={<PefStudio tab="questions" />} />
            <Route path="/pef/sparql" element={<PefStudio tab="sparql" />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="*" element={<Navigate to="/search" replace />} />
          </Routes>
        </main>
      </div>
      {settingsOpen && settings && (
        <SettingsModal settings={settings} onClose={() => setSettingsOpen(false)} />
      )}
    </div>
  );
}

function Header({ settings, onSettings }: { settings: Settings | null; onSettings: () => void }) {
  return (
    <header
      className="glass panel-hero"
      style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "12px 20px", margin: 16, marginBottom: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div
          style={{
            width: 36, height: 36, borderRadius: 10, background: "var(--grad-primary)",
            display: "grid", placeItems: "center", color: "#fff", fontWeight: 700,
            fontSize: 12, letterSpacing: 0.5, boxShadow: "0 6px 18px rgba(61,43,186,0.32)",
          }}
        >
          ICI
        </div>
        <div style={{ fontWeight: 700, color: "var(--cerise-navy)", letterSpacing: 0.2 }}>
          Intelligent Circular Insights
        </div>
        {settings && <span className="pill teal">v{settings.version}</span>}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <ModeBadge />
        <button className="btn secondary" onClick={onSettings} data-testid="open-settings">
          ⚙ Settings
        </button>
      </div>
    </header>
  );
}

function Sidebar() {
  const location = useLocation();
  return (
    <nav className="glass panel-hero"
         style={{ padding: 12, display: "flex", flexDirection: "column", gap: 6, overflowY: "auto" }}>
      {NAV.map(item => {
        const active = location.pathname.startsWith(item.to);
        return (
          <div key={item.to}>
            <NavLink
              to={item.to}
              data-testid={`nav-${item.to.slice(1)}`}
              className={() => "nav-link-glass" + (active ? " active" : "")}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "10px 12px", borderRadius: 10,
                color: active ? "#fff" : "var(--cerise-navy)",
                background: active ? "var(--grad-primary)" : "transparent",
                textDecoration: "none", fontWeight: 600, fontSize: 13.5,
                boxShadow: active ? "0 6px 18px rgba(61,43,186,0.30)" : "none",
                transition: "background 200ms, box-shadow 200ms",
              }}
            >
              <span style={{ fontSize: 17 }}>{item.glyph}</span>
              {item.label}
            </NavLink>
            {active && item.subnav && (
              <div style={{
                display: "grid", gap: 5, margin: "6px 0 6px 26px",
                paddingLeft: 10, borderLeft: "1px solid rgba(255,255,255,0.50)",
              }}>
                {item.subnav.map(s => (
                  <NavLink
                    key={s.to}
                    to={s.to}
                    data-testid={`subnav-${s.to.split("/").pop()}`}
                    className={({ isActive }) => "nav-link-glass" + (isActive ? " active" : "")}
                    style={({ isActive }) => ({
                      display: "flex", alignItems: "center", minHeight: 30,
                      padding: "6px 10px", borderRadius: 9,
                      color: isActive ? "#fff" : "var(--cerise-navy)",
                      background: isActive ? "rgba(110,45,200,0.70)" : "rgba(255,255,255,0.20)",
                      textDecoration: "none", fontSize: 12.5, fontWeight: 650,
                    })}
                  >
                    {s.label}
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}
