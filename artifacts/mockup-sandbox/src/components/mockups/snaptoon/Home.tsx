import { useState } from "react";

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

type ViewMode = "default" | "empty" | "creating" | "deleting";

function Sidebar() {
  return (
    <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
        <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
          SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} />
        </span>
      </div>
      <div style={{ padding: "0.75rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>Progetto attivo</div>
        <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 10px", fontSize: 13, color: "#CBD5E1", display: "flex", justifyContent: "space-between" }}>
          <span>La notte del riccio</span><span style={{ color: "#475569" }}>▾</span>
        </div>
        <div style={{ marginTop: 6 }}><span style={{ fontSize: 12, color: "#F59E0B", cursor: "pointer" }}>+ Nuovo progetto</span></div>
      </div>
      <div style={{ height: 1, background: "#1E2436", margin: "0.5rem 0" }} />
      <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", padding: "0.25rem 1.25rem" }}>Navigazione</div>
      {NAV.map(n => (
        <div key={n.label} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", borderRadius: 6, margin: "2px 8px", fontSize: 14, fontWeight: 500, color: "#64748B", cursor: "pointer" }}>
          <span>{n.icon}</span><span>{n.label}</span>
        </div>
      ))}
      <div style={{ flex: 1 }} />
      <div style={{ height: 1, background: "#1E2436" }} />
      <div style={{ padding: "0.75rem" }}>
        <div style={{ background: "#0D1017", border: "1px solid #1E2436", borderRadius: 8, padding: "0.75rem 1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ fontSize: 10, fontWeight: 600, color: "#475569", textTransform: "uppercase" }}>💳 Crediti</span>
            <span style={{ fontSize: 10, fontWeight: 600, background: "rgba(100,116,139,.15)", color: "#94A3B8", padding: "2px 7px", borderRadius: 4 }}>Creator</span>
          </div>
          <div style={{ fontWeight: 700, color: "#E2E8F0", marginBottom: 6 }}>142 / 200</div>
          <div style={{ height: 3, background: "#1E2436", borderRadius: 4 }}><div style={{ width: "71%", height: "100%", background: "#10B981", borderRadius: 4 }} /></div>
        </div>
        <button style={{ border: "1px solid #2D3748", background: "transparent", color: "#CBD5E1", fontSize: 12, padding: "6px 0", borderRadius: 6, cursor: "pointer", width: "100%", marginTop: 8 }}>🚪 Esci</button>
      </div>
    </div>
  );
}

export function Home() {
  const [view, setView] = useState<ViewMode>("default");
  const [deleteTarget, setDeleteTarget] = useState("La notte del riccio");
  const [deleteInput, setDeleteInput] = useState("");

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        input:focus { outline:none;border-color:#F59E0B !important; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 10px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif;transition:background .15s; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:1px solid #F59E0B;color:#0D1017;font-size:12px;font-weight:600;padding:5px 14px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-primary:hover { background:#FBBF24; }
        .btn-danger { background:transparent;border:1px solid rgba(239,68,68,.4);color:#EF4444;font-size:12px;font-weight:500;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .project-card { background:#161B26;border:1px solid #1E2436;border-radius:8px;padding:1.25rem;transition:border-color .15s;cursor:pointer; }
        .project-card:hover { border-color:#2D3748; }
      `}</style>

      {/* State switcher */}
      <div style={{ position: "fixed", bottom: 16, right: 16, zIndex: 100, background: "#161B26", border: "1px solid #2D3748", borderRadius: 8, padding: "8px 12px", display: "flex", gap: 6, flexDirection: "column", fontSize: 11, fontFamily: "'Inter',sans-serif" }}>
        <div style={{ color: "#475569", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 2 }}>Stato</div>
        {(["default","empty","creating","deleting"] as ViewMode[]).map(v => (
          <button key={v} onClick={() => setView(v)} style={{ padding: "3px 10px", borderRadius: 4, border: "1px solid", fontFamily: "'Inter',sans-serif", fontSize: 11, cursor: "pointer", background: view === v ? "#F59E0B" : "transparent", borderColor: view === v ? "#F59E0B" : "#2D3748", color: view === v ? "#0D1017" : "#64748B" }}>{v}</button>
        ))}
      </div>

      <Sidebar />

      <div style={{ flex: 1, padding: "2rem 2.5rem", overflowY: "auto", position: "relative" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: "1.25rem", borderBottom: "1px solid #1E2436", marginBottom: "1.5rem" }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0, color: "#F1F5F9", letterSpacing: "-0.02em" }}>I tuoi progetti</h1>
          <button className="btn-primary" style={{ fontSize: 13 }} onClick={() => setView("creating")}>+ Nuovo progetto</button>
        </div>

        {/* EMPTY STATE */}
        {view === "empty" && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "5rem 2rem", textAlign: "center" }}>
            <div style={{ fontSize: 64, marginBottom: "1rem" }}>📂</div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#CBD5E1", margin: "0 0 .5rem" }}>Nessun progetto ancora.</h2>
            <p style={{ fontSize: 14, color: "#475569", margin: "0 0 1.5rem", maxWidth: 360 }}>Crea il tuo primo progetto e inizia a trasformare le tue storie in fumetti.</p>
            <button className="btn-primary" style={{ fontSize: 14, padding: "10px 20px" }}>+ Crea il tuo primo progetto</button>
          </div>
        )}

        {/* DEFAULT — project grid */}
        {(view === "default" || view === "creating" || view === "deleting") && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
            {PROJECTS.map(p => (
              <div key={p.id} className="project-card">
                <div style={{ aspectRatio: "2/3", background: "#0D1017", border: "1px solid #1E2436", borderRadius: 6, marginBottom: "0.85rem", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <span style={{ fontSize: 32, opacity: .3 }}>🎨</span>
                </div>
                <div style={{ fontWeight: 600, fontSize: 15, color: "#F1F5F9", marginBottom: 4 }}>{p.title}</div>
                <div style={{ fontSize: 12, color: "#64748B", marginBottom: 12 }}>{p.pages} pagine · {p.style} · Creato il {p.date}</div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="btn" style={{ flex: 1 }}>📋 Duplica</button>
                  <button className="btn" style={{ flex: 1 }} onClick={() => { setDeleteTarget(p.title); setView("deleting"); }}>🗑</button>
                  <button className="btn-primary" style={{ flex: 1 }}>Apri →</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* CREATING modal */}
        {view === "creating" && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(13,16,23,.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}>
            <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 12, padding: "2rem", width: 440, boxShadow: "0 32px 80px rgba(0,0,0,.7)" }}>
              <h2 style={{ fontSize: "1.15rem", fontWeight: 700, margin: "0 0 1.25rem", color: "#F1F5F9" }}>Nuovo progetto</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", marginBottom: "1.25rem" }}>
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 5 }}>Nome progetto</label>
                  <input placeholder="es. Il mio fumetto" style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "9px 12px", color: "#E2E8F0", fontSize: 14 }} />
                </div>
                <div>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 5 }}>Lunghezza prevista</label>
                  <select style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "9px 12px", color: "#E2E8F0", fontSize: 14 }}>
                    <option>Striscia (1-2 pagine)</option>
                    <option>Breve (3-8 pagine)</option>
                    <option>Medio (9-24 pagine)</option>
                    <option>Lungo (25+ pagine)</option>
                  </select>
                </div>
              </div>
              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button className="btn" style={{ fontSize: 13, padding: "8px 16px" }} onClick={() => setView("default")}>Annulla</button>
                <button className="btn-primary" style={{ fontSize: 13, padding: "8px 16px" }}>Crea progetto →</button>
              </div>
            </div>
          </div>
        )}

        {/* DELETING — confirm dialog */}
        {view === "deleting" && (
          <div style={{ position: "fixed", inset: 0, background: "rgba(13,16,23,.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50 }}>
            <div style={{ background: "#161B26", border: "1px solid rgba(239,68,68,.3)", borderRadius: 12, padding: "2rem", width: 440, boxShadow: "0 32px 80px rgba(0,0,0,.7)" }}>
              <div style={{ fontSize: 32, marginBottom: "0.75rem", textAlign: "center" }}>🗑️</div>
              <h2 style={{ fontSize: "1.1rem", fontWeight: 700, margin: "0 0 .5rem", color: "#F1F5F9", textAlign: "center" }}>Elimina progetto</h2>
              <p style={{ fontSize: 13, color: "#94A3B8", textAlign: "center", lineHeight: 1.6, margin: "0 0 1.25rem" }}>
                Questa operazione è <strong style={{ color: "#EF4444" }}>irreversibile</strong>. Tutte le vignette e i file verranno eliminati.
              </p>
              <div style={{ marginBottom: "1.25rem" }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#94A3B8", marginBottom: 6 }}>
                  Scrivi <strong style={{ color: "#F1F5F9" }}>"{deleteTarget}"</strong> per confermare
                </label>
                <input value={deleteInput} onChange={e => setDeleteInput(e.target.value)} placeholder={deleteTarget} style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "9px 12px", color: "#E2E8F0", fontSize: 14 }} />
              </div>
              <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                <button className="btn" style={{ fontSize: 13, padding: "8px 16px" }} onClick={() => { setView("default"); setDeleteInput(""); }}>Annulla</button>
                <button className="btn-danger" style={{ fontSize: 13, padding: "8px 16px", opacity: deleteInput === deleteTarget ? 1 : 0.4, cursor: deleteInput === deleteTarget ? "pointer" : "not-allowed" }}>Elimina definitivamente</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
