import { useState } from "react";

const NAV = [
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile", active: true },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera" },
  { icon: "📐", label: "Impagina" },
];

const CATEGORIES = ["I miei stili", "Fumetto", "Illustrazione", "Fotografia", "Cinema", "Kids", "Fot. d'autore"];

const PRESETS = [
  { id: 1, name: "Heavy Ink Noir", cat: "Fumetto", active: true, desc: "Deep ambient black inks, heavy chiaroscuro, dramatic shadows. Urban crime aesthetic." },
  { id: 2, name: "Silver Age Comics", cat: "Fumetto", active: false, desc: "Bold outlines, flat CMYK halftone dots, vibrant primary palette, retro superhero energy." },
  { id: 3, name: "Ligne Claire", cat: "Fumetto", active: false, desc: "Clean uniform line weight, bright flat fills, zero shadows. Hergé-inspired European tradition." },
  { id: 4, name: "Manga Shonen", cat: "Fumetto", active: false, desc: "High contrast B&W, speed lines, expressive distortion, screen tones, kinetic energy." },
  { id: 5, name: "Horror Woodcut", cat: "Fumetto", active: false, desc: "Rough cross-hatching, aged texture, cold desaturated palette, scratched relief look." },
  { id: 6, name: "Pop Art", cat: "Fumetto", active: false, desc: "Lichtenstein-style Ben-Day dots, thick black outlines, saturated primary colors." },
];

function Sidebar() {
  return (
    <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
        <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} /></span>
      </div>
      <div style={{ padding: "0.75rem 1rem 0.5rem" }}>
        <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 10px", fontSize: 13, color: "#CBD5E1", display: "flex", justifyContent: "space-between" }}>
          <span>La notte del riccio</span><span style={{ color: "#475569" }}>▾</span>
        </div>
      </div>
      <div style={{ height: 1, background: "#1E2436", margin: "0.5rem 0" }} />
      {NAV.map(n => (
        <div key={n.label} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", borderRadius: 6, margin: "2px 8px", fontSize: 14, fontWeight: 500, color: (n as any).active ? "#F59E0B" : "#64748B", background: (n as any).active ? "#1A2035" : "transparent", borderLeft: (n as any).active ? "3px solid #F59E0B" : "3px solid transparent", cursor: "pointer" }}>
          <span>{n.icon}</span><span>{n.label}</span>
        </div>
      ))}
      <div style={{ flex: 1 }} />
      <div style={{ height: 1, background: "#1E2436" }} />
      <div style={{ padding: "0.75rem" }}>
        <div style={{ background: "#0D1017", border: "1px solid #1E2436", borderRadius: 8, padding: "0.75rem 1rem" }}>
          <div style={{ fontWeight: 700, color: "#E2E8F0", marginBottom: 6 }}>142 / 200</div>
          <div style={{ height: 3, background: "#1E2436", borderRadius: 4 }}><div style={{ width: "71%", height: "100%", background: "#10B981", borderRadius: 4 }} /></div>
        </div>
      </div>
    </div>
  );
}

export function Stile() {
  const [tab, setTab] = useState("libreria");
  const [cat, setCat] = useState("Fumetto");
  const [activeStyle, setActiveStyle] = useState(1);

  const filtered = PRESETS.filter(p => p.cat === cat);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 11px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .tab-btn { padding:8px 16px;border:none;background:transparent;color:#64748B;font-size:14px;font-weight:500;cursor:pointer;border-bottom:2px solid transparent;font-family:'Inter',sans-serif; }
        .tab-btn.active { color:#F59E0B;border-bottom-color:#F59E0B; }
        .cat-chip { padding:5px 12px;border-radius:20px;font-size:12px;font-weight:500;cursor:pointer;border:1px solid #2D3748;background:transparent;color:#64748B;font-family:'Inter',sans-serif;transition:all .15s; }
        .cat-chip.active { background:#F59E0B;border-color:#F59E0B;color:#0D1017; }
      `}</style>

      <Sidebar />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div style={{ padding: "1.5rem 2rem 0", borderBottom: "1px solid #1E2436" }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", letterSpacing: "-0.02em" }}>Stile visivo</h1>
          <p style={{ fontSize: 13, color: "#64748B", margin: "0 0 1rem" }}>Progetto: La notte del riccio</p>
          <div style={{ display: "flex", gap: 0 }}>
            {["Selezione","Sfoglia libreria","Personalizza","Aspetto pagina","Anteprima prompt"].map(t => (
              <button key={t} className={`tab-btn${tab === t.toLowerCase().replace(" ","") || (t === "Sfoglia libreria" && tab === "libreria") ? " active" : ""}`}
                onClick={() => setTab(t === "Sfoglia libreria" ? "libreria" : t.toLowerCase().replace(" ","").slice(0,10))}>{t}</button>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, padding: "1.5rem 2rem", overflowY: "auto" }}>
          {/* Active style card */}
          {tab !== "libreria" && (
            <div style={{ background: "#161B26", border: "2px solid #F59E0B", borderRadius: 10, padding: "1.25rem", marginBottom: "1.5rem", display: "flex", gap: "1.25rem" }}>
              <div style={{ width: 120, aspectRatio: "3/4", background: "linear-gradient(135deg,#1a1a2e,#0d1b2a)", borderRadius: 6, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32 }}>🖤</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span style={{ fontWeight: 700, fontSize: 18, color: "#F1F5F9" }}>Heavy Ink Noir</span>
                  <span style={{ background: "rgba(245,158,11,.15)", color: "#F59E0B", fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 4 }}>ATTIVO</span>
                </div>
                <span style={{ fontSize: 12, color: "#7C3AED", fontWeight: 500, background: "rgba(124,58,237,.1)", padding: "2px 8px", borderRadius: 4 }}>Fumetto</span>
                <p style={{ fontSize: 13, color: "#94A3B8", lineHeight: 1.6, marginTop: 10 }}>Deep ambient black inks, heavy chiaroscuro, dramatic shadows. Urban crime aesthetic with mid-century European noir influence.</p>
                <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                  <button className="btn">Sfoglia libreria</button>
                  <button className="btn">✏️ Personalizza</button>
                </div>
              </div>
            </div>
          )}

          {tab === "libreria" && (
            <>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: "1.25rem" }}>
                {CATEGORIES.map(c => (
                  <button key={c} className={`cat-chip${c === cat ? " active" : ""}`} onClick={() => setCat(c)}>{c}</button>
                ))}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem" }}>
                {filtered.map(p => (
                  <div key={p.id} style={{ background: "#161B26", border: `1px solid ${p.id === activeStyle ? "#F59E0B" : "#1E2436"}`, borderRadius: 8, overflow: "hidden", cursor: "pointer" }}
                    onClick={() => setActiveStyle(p.id)}>
                    <div style={{ aspectRatio: "16/9", background: `linear-gradient(135deg,#${p.id % 2 === 0 ? "1e3a2f" : "1a1a2e"},#${p.id % 3 === 0 ? "2a1f1f" : "0d1b2a"})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24 }}>
                      {p.id === 1 ? "🖤" : p.id === 2 ? "🦸" : p.id === 3 ? "🔵" : p.id === 4 ? "⚡" : p.id === 5 ? "💀" : "🟡"}
                    </div>
                    <div style={{ padding: "0.75rem 0.85rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, fontSize: 14, color: "#F1F5F9" }}>{p.name}</span>
                        {p.id === activeStyle && <span style={{ fontSize: 9, fontWeight: 700, background: "rgba(245,158,11,.2)", color: "#F59E0B", padding: "2px 6px", borderRadius: 3 }}>ATTIVO</span>}
                      </div>
                      <p style={{ fontSize: 12, color: "#64748B", lineHeight: 1.5, margin: "0 0 10px", overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{p.desc}</p>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button className="btn" style={{ flex: 1, fontSize: 11 }}>👁 Anteprima</button>
                        <button className="btn-primary" style={{ flex: 1, fontSize: 11 }}>✨ Applica</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
