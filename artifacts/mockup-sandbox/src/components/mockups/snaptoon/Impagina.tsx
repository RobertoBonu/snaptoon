const NAV = [
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile" },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera" },
  { icon: "📐", label: "Impagina", active: true },
];

const PAGES = [
  { n: 1, cage: "2×2 simmetrica", panels: 4, dialoghi: 5, rendered: true },
  { n: 2, cage: "1+2+3 crescendo", panels: 6, dialoghi: 4, rendered: true },
  { n: 3, cage: "3×3 griglia", panels: 9, dialoghi: 8, rendered: false },
  { n: 4, cage: "2+1 splash", panels: 3, dialoghi: 2, rendered: false },
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

export function Impagina() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 11px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-disabled { border:1px solid #1E2436;background:transparent;color:#334155;font-size:12px;font-weight:500;padding:5px 11px;border-radius:6px;cursor:not-allowed;font-family:'Inter',sans-serif; }
      `}</style>

      <Sidebar />

      <div style={{ flex: 1, padding: "2rem 2.5rem", overflowY: "auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: "1.25rem", borderBottom: "1px solid #1E2436", marginBottom: "1.25rem" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", letterSpacing: "-0.02em" }}>Impagina</h1>
            <p style={{ fontSize: 13, color: "#64748B", margin: 0 }}>Progetto: La notte del riccio · 4 pagine</p>
          </div>
        </div>

        {/* Global progress */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontSize: 14, color: "#CBD5E1", fontWeight: 500 }}>2 / 4 pagine renderizzate</span>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn">📐 Renderizza tutte le pagine</button>
              <button className="btn-primary">📥 Esporta PDF</button>
            </div>
          </div>
          <div style={{ height: 4, background: "#0D1017", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ width: "50%", height: "100%", background: "#F59E0B", borderRadius: 4 }} />
          </div>
        </div>

        {/* Pages list */}
        {PAGES.map(page => (
          <div key={page.n} style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, marginBottom: "0.75rem", overflow: "hidden" }}>
            {/* Page header */}
            <div style={{ padding: "0.85rem 1.25rem", background: "#0A0E17", borderBottom: "1px solid #1E2436", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span style={{ fontWeight: 600, fontSize: 15, color: "#CBD5E1" }}>Pagina {page.n}</span>
                <span style={{ fontSize: 12, color: "#475569", marginLeft: 12 }}>{page.cage} · {page.panels} vignette · {page.dialoghi} dialoghi</span>
              </div>
              {page.rendered && <span style={{ fontSize: 11, fontWeight: 600, background: "rgba(16,185,129,.15)", color: "#10B981", padding: "3px 8px", borderRadius: 4 }}>✓ Renderizzata</span>}
            </div>

            {/* Content */}
            <div style={{ padding: "1.25rem", display: "flex", gap: "1.5rem", alignItems: "flex-start" }}>
              {/* Page preview */}
              <div style={{ width: 200, flexShrink: 0 }}>
                <div style={{ aspectRatio: "2/3", background: page.rendered ? "linear-gradient(160deg,#1a1a2e,#0d1b2a,#1a1f1a)" : "#0D1017", border: "1px solid #2D3748", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
                  {page.rendered ? (
                    <div style={{ width: "100%", height: "100%", padding: 8, display: "grid", gridTemplateColumns: page.cage.includes("2×2") ? "1fr 1fr" : "1fr 1fr 1fr", gap: 4 }}>
                      {Array.from({ length: page.cage.includes("2×2") ? 4 : page.cage.includes("1+2+3") ? 3 : 3 }).map((_, i) => (
                        <div key={i} style={{ background: `hsl(${220 + i * 30},30%,${15 + i * 3}%)`, borderRadius: 2 }} />
                      ))}
                    </div>
                  ) : (
                    <span style={{ fontSize: 28, opacity: .2 }}>📐</span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div style={{ flex: 1 }}>
                {!page.rendered && (
                  <div style={{ background: "rgba(245,158,11,.06)", border: "1px solid rgba(245,158,11,.15)", borderRadius: 6, padding: "8px 12px", marginBottom: 12, fontSize: 12, color: "#94A3B8" }}>
                    Questa pagina non è ancora stata renderizzata.
                  </div>
                )}
                <div style={{ display: "flex", gap: 8 }}>
                  <button className={page.rendered ? "btn" : "btn-primary"} style={{ fontSize: 12 }}>
                    {page.rendered ? "♻️ Rigenera pagina" : "🎨 Renderizza pagina"}
                  </button>
                  {page.rendered
                    ? <button className="btn" style={{ fontSize: 12 }}>📥 Scarica PNG</button>
                    : <button className="btn-disabled" style={{ fontSize: 12 }}>📥 Scarica PNG</button>
                  }
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
