const PROJECTS = [
  { id: 1, title: "La notte del riccio", pages: 8, date: "12/06/2025", style: "Fumetto" },
  { id: 2, title: "Viaggio a Marte", pages: 14, date: "20/06/2025", style: "Cinema" },
  { id: 3, title: "Il gatto detective", pages: 5, date: "26/06/2025", style: "Kids" },
];

const NAV = [
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile" },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera" },
  { icon: "📐", label: "Impagina" },
];

export function Home() {
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter', sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        .nav-item { display:flex;align-items:center;gap:10px;padding:10px 20px;border-radius:6px;margin:2px 8px;font-size:14px;font-weight:500;color:#64748B;cursor:pointer;transition:background .15s,color .15s; }
        .nav-item:hover { background:#1E2436;color:#E2E8F0; }
        .project-card { background:#161B26;border:1px solid #1E2436;border-radius:8px;padding:1.25rem;transition:border-color .15s;cursor:pointer; }
        .project-card:hover { border-color:#2D3748; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:13px;font-weight:500;padding:6px 12px;border-radius:6px;cursor:pointer;transition:background .15s; font-family:'Inter',sans-serif;}
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:1px solid #F59E0B;color:#0D1017;font-size:13px;font-weight:600;padding:6px 14px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-primary:hover { background:#FBBF24; }
      `}</style>

      {/* Sidebar */}
      <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
        {/* Logo */}
        <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
          <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
            SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} />
          </span>
        </div>

        {/* Project selector */}
        <div style={{ padding: "0.75rem 1rem 0.5rem" }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>Progetto attivo</div>
          <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 10px", fontSize: 13, color: "#CBD5E1", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>La notte del riccio</span>
            <span style={{ color: "#475569" }}>▾</span>
          </div>
          <div style={{ marginTop: 6 }}>
            <span style={{ fontSize: 12, color: "#F59E0B", cursor: "pointer" }}>+ Nuovo progetto</span>
          </div>
        </div>

        <div style={{ height: 1, background: "#1E2436", margin: "0.5rem 0" }} />

        {/* Nav */}
        <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", padding: "0.25rem 1.25rem" }}>Navigazione</div>
        {NAV.map(n => (
          <div key={n.label} className="nav-item">
            <span>{n.icon}</span>
            <span>{n.label}</span>
          </div>
        ))}

        <div style={{ flex: 1 }} />
        <div style={{ height: 1, background: "#1E2436" }} />

        {/* Credit badge */}
        <div style={{ padding: "0.75rem" }}>
          <div style={{ background: "#0D1017", border: "1px solid #1E2436", borderRadius: 8, padding: "0.75rem 1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
              <span style={{ fontSize: 10, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: ".06em" }}>💳 Crediti</span>
              <span style={{ fontSize: 10, fontWeight: 600, background: "rgba(100,116,139,.15)", color: "#94A3B8", padding: "2px 7px", borderRadius: 4 }}>Creator</span>
            </div>
            <div style={{ fontSize: "1rem", fontWeight: 700, color: "#E2E8F0", marginBottom: 6 }}>142 / 200</div>
            <div style={{ height: 3, background: "#1E2436", borderRadius: 4, overflow: "hidden" }}>
              <div style={{ width: "71%", height: "100%", background: "#10B981", borderRadius: 4 }} />
            </div>
          </div>
          <button className="btn" style={{ width: "100%", marginTop: 8, textAlign: "center" }}>🚪 Esci</button>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, padding: "2rem 2.5rem", overflowY: "auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: "1.25rem", borderBottom: "1px solid #1E2436", marginBottom: "1.5rem" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0, color: "#F1F5F9", letterSpacing: "-0.02em" }}>I tuoi progetti</h1>
          </div>
          <button className="btn-primary">+ Nuovo progetto</button>
        </div>

        {/* Project grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
          {PROJECTS.map(p => (
            <div key={p.id} className="project-card">
              {/* Thumbnail placeholder */}
              <div style={{ aspectRatio: "3/4", background: "#0D1017", border: "1px solid #1E2436", borderRadius: 6, marginBottom: "0.85rem", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: 32, opacity: .3 }}>🎨</span>
              </div>
              <div style={{ fontWeight: 600, fontSize: 15, color: "#F1F5F9", marginBottom: 4 }}>{p.title}</div>
              <div style={{ fontSize: 12, color: "#64748B", marginBottom: 12 }}>
                {p.pages} pagine · {p.style} · Creato il {p.date}
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                <button className="btn" style={{ flex: 1 }}>📋 Duplica</button>
                <button className="btn" style={{ flex: 1 }}>🗑 Elimina</button>
                <button className="btn-primary" style={{ flex: 1 }}>Apri →</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
