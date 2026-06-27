const NAV = [
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile" },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera", active: true },
  { icon: "📐", label: "Impagina" },
];

const PANELS = [
  { n: 1, done: true, cast: ["Marco", "Luisa"], desc: "Marco si affaccia dalla finestra del vecchio palazzo. Piove forte. Luisa lo osserva dall'ombra del portico." },
  { n: 2, done: true, cast: ["Luisa"], desc: "Primo piano di Luisa. Sguardo deciso, mascella contratta. Tiene in mano una lettera bagnata." },
  { n: 3, done: false, cast: ["Marco", "Luisa"], desc: "I due si fronteggiano sul pianerottolo. La luce fioca della lampada proietta ombre lunghe." },
  { n: 4, done: false, cast: ["Marco"], desc: "Marco apre la porta. Il suo volto cambia espressione quando vede l'interno della stanza." },
];

export function Genera() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter', sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        .nav-item { display:flex;align-items:center;gap:10px;padding:10px 20px;border-radius:6px;margin:2px 8px;font-size:14px;font-weight:500;color:#64748B;cursor:pointer;transition:background .15s; }
        .nav-item.active { background:#1A2035;color:#F59E0B;border-left:3px solid #F59E0B;padding-left:17px; }
        .nav-item:not(.active):hover { background:#1E2436;color:#E2E8F0; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 10px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif;transition:background .15s; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:1px solid #F59E0B;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-primary:hover { background:#FBBF24; }
        .panel-card { background:#161B26;border:1px solid #1E2436;border-radius:8px;overflow:hidden; }
        .panel-card:hover { border-color:#2D3748; }
      `}</style>

      {/* Sidebar */}
      <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
          <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
            SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} />
          </span>
        </div>

        <div style={{ padding: "0.75rem 1rem 0.5rem" }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>Progetto attivo</div>
          <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 10px", fontSize: 13, color: "#CBD5E1", display: "flex", justifyContent: "space-between" }}>
            <span>La notte del riccio</span>
            <span style={{ color: "#475569" }}>▾</span>
          </div>
        </div>

        <div style={{ height: 1, background: "#1E2436", margin: "0.5rem 0" }} />
        <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", padding: "0.25rem 1.25rem" }}>Navigazione</div>

        {NAV.map(n => (
          <div key={n.label} className={`nav-item${n.active ? " active" : ""}`}>
            <span>{n.icon}</span><span>{n.label}</span>
          </div>
        ))}

        <div style={{ flex: 1 }} />
        <div style={{ height: 1, background: "#1E2436" }} />

        <div style={{ padding: "0.75rem" }}>
          <div style={{ background: "#0D1017", border: "1px solid #1E2436", borderRadius: 8, padding: "0.75rem 1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <span style={{ fontSize: 10, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: ".06em" }}>💳 Crediti</span>
              <span style={{ fontSize: 10, fontWeight: 600, background: "rgba(100,116,139,.15)", color: "#94A3B8", padding: "2px 7px", borderRadius: 4 }}>Creator</span>
            </div>
            <div style={{ fontWeight: 700, color: "#E2E8F0", marginBottom: 6 }}>142 / 200</div>
            <div style={{ height: 3, background: "#1E2436", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ width: "71%", height: "100%", background: "#10B981", borderRadius: 4 }} />
            </div>
          </div>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, padding: "2rem 2.5rem", overflowY: "auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: "1.25rem", borderBottom: "1px solid #1E2436", marginBottom: "1.25rem" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", color: "#F1F5F9", letterSpacing: "-0.02em" }}>Genera vignette</h1>
            <p style={{ fontSize: 13, color: "#64748B", margin: 0 }}>Progetto: La notte del riccio · 8 vignette</p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn">🚀 Genera mancanti (2)</button>
            <button className="btn-primary">🌙 Genera TUTTO (4)</button>
          </div>
        </div>

        {/* Status bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0.65rem 1rem", background: "#0A0E17", border: "1px solid #1E2436", borderRadius: 6, marginBottom: "1.25rem" }}>
          <span style={{ fontWeight: 700, color: "#F59E0B", fontSize: 15 }}>2/4</span>
          <span style={{ fontSize: 13, color: "#94A3B8" }}>vignette generate — Pagina 1</span>
          <div style={{ flex: 1, height: 4, background: "#1E2436", borderRadius: 4, overflow: "hidden", marginLeft: 8 }}>
            <div style={{ width: "50%", height: "100%", background: "#F59E0B", borderRadius: 4 }} />
          </div>
        </div>

        {/* Warning */}
        <div style={{ background: "rgba(245,158,11,.08)", border: "1px solid rgba(245,158,11,.2)", borderRadius: 6, padding: "10px 14px", marginBottom: "1.25rem", fontSize: 13, color: "#F59E0B" }}>
          ⚠️ 1 personaggio senza reference. Vai su Personaggi per generarla prima.
        </div>

        {/* Page expander */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, overflow: "hidden", marginBottom: "0.75rem" }}>
          {/* Expander header */}
          <div style={{ padding: "0.85rem 1rem", background: "#0A0E17", borderBottom: "1px solid #1E2436", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: "#CBD5E1" }}>📖 Pagina 1 — 4 vignette</span>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 11, color: "#475569" }}>Gabbia: 2×2 · 4 vignette</span>
              <button className="btn" style={{ fontSize: 11 }}>💾 Salva gabbia</button>
              <span style={{ color: "#475569", fontSize: 12 }}>▴</span>
            </div>
          </div>

          {/* Panel grid */}
          <div style={{ padding: "1rem", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem" }}>
            {PANELS.map(p => (
              <div key={p.n} className="panel-card">
                {/* Header */}
                <div style={{ padding: "6px 10px", background: "#0A0E17", borderBottom: "1px solid #1E2436", fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".05em" }}>
                  Vignetta {p.n}
                </div>

                {/* Image area */}
                <div style={{ aspectRatio: "4/3", background: "#0D1017", display: "flex", alignItems: "center", justifyContent: "center", borderBottom: "1px solid #1E2436", overflow: "hidden", position: "relative" }}>
                  {p.done ? (
                    <>
                      {/* Simulated generated image gradient */}
                      <div style={{
                        position: "absolute", inset: 0,
                        background: p.n === 1
                          ? "linear-gradient(135deg,#1a2035 0%,#2d1f3d 50%,#1a2035 100%)"
                          : "linear-gradient(135deg,#1f2a1a 0%,#2a1f1f 50%,#1a1f2a 100%)",
                        display: "flex", alignItems: "center", justifyContent: "center"
                      }}>
                        <span style={{ fontSize: 24, opacity: .6 }}>{p.n === 1 ? "🌧️" : "📄"}</span>
                      </div>
                      <div style={{ position: "absolute", top: 6, right: 6, background: "rgba(16,185,129,.2)", border: "1px solid #10B981", borderRadius: 4, padding: "2px 6px", fontSize: 10, color: "#10B981", fontWeight: 600 }}>✓</div>
                    </>
                  ) : (
                    <span style={{ fontSize: 12, color: "#334155", fontStyle: "italic" }}>— non ancora generata —</span>
                  )}
                </div>

                {/* Body */}
                <div style={{ padding: "8px 10px" }}>
                  <div style={{ fontSize: 11, color: "#64748B", lineHeight: 1.5, marginBottom: 6, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                    {p.desc}
                  </div>
                  <div style={{ fontSize: 11, color: "#475569", marginBottom: 8 }}>👥 {p.cast.join(", ")}</div>

                  <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                    <button className={p.done ? "btn" : "btn-primary"} style={{ flex: 1, fontSize: 11 }}>
                      {p.done ? "🔄 Rigenera" : "✨ Genera"}
                    </button>
                    <button className="btn" style={{ padding: "5px 8px" }}>🎬</button>
                  </div>
                  <div style={{ display: "flex", gap: 4 }}>
                    <button className="btn" style={{ flex: 1, fontSize: 11 }}>👁 Prompt</button>
                    <button className="btn" style={{ flex: 1, fontSize: 11 }}>🎈 Balloon</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Add page */}
        <button className="btn" style={{ width: "100%", padding: "10px", textAlign: "center", borderStyle: "dashed" }}>
          ➕ Pagina dopo
        </button>
      </div>
    </div>
  );
}
