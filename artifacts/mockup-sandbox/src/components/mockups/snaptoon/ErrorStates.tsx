import { useState } from "react";

type ErrorType = "404" | "credits" | "network" | "generic" | "session";

const ERROR_TYPES: { id: ErrorType; label: string }[] = [
  { id: "404", label: "404 — Non trovata" },
  { id: "session", label: "Sessione scaduta" },
  { id: "credits", label: "Crediti esauriti" },
  { id: "network", label: "Errore di rete / API" },
  { id: "generic", label: "Errore generico" },
];

function Sidebar() {
  return (
    <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
        <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
          SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} />
        </span>
      </div>
      {["📝 Testo", "🎨 Stile", "👥 Personaggi", "🖼 Genera", "📐 Impagina"].map(n => (
        <div key={n} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", borderRadius: 6, margin: "2px 8px", fontSize: 14, fontWeight: 500, color: "#64748B", cursor: "pointer" }}>
          {n}
        </div>
      ))}
      <div style={{ flex: 1 }} />
    </div>
  );
}

function Error404() {
  return (
    <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: "1rem", padding: "3rem" }}>
      <div style={{ fontSize: 72, lineHeight: 1, marginBottom: "0.5rem" }}>🗺️</div>
      <h1 style={{ fontSize: "2rem", fontWeight: 700, color: "#F1F5F9", margin: 0, letterSpacing: "-0.02em" }}>Pagina non trovata.</h1>
      <p style={{ fontSize: 15, color: "#64748B", textAlign: "center", maxWidth: 420, lineHeight: 1.6, margin: 0 }}>
        Il link che hai seguito non porta da nessuna parte, oppure il progetto è stato eliminato.
      </p>
      <button style={{ background: "#F59E0B", border: "none", color: "#0D1017", fontWeight: 600, fontSize: 14, padding: "10px 20px", borderRadius: 6, cursor: "pointer", marginTop: "0.5rem" }}>
        Torna alla home
      </button>
    </div>
  );
}

function ErrorSession() {
  return (
    <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: "1.25rem", padding: "3rem", background: "#0D1017" }}>
      {/* Simulated login page with toast */}
      <div style={{ width: "100%", maxWidth: 480 }}>
        {/* Persistent toast */}
        <div style={{ background: "rgba(245,158,11,.12)", border: "1px solid rgba(245,158,11,.3)", borderRadius: 8, padding: "12px 16px", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 18 }}>⏱️</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#F59E0B" }}>Sessione scaduta</div>
            <div style={{ fontSize: 12, color: "#94A3B8", marginTop: 2 }}>La sessione è scaduta. Accedi di nuovo.</div>
          </div>
        </div>

        {/* Login form */}
        <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 12, padding: "2rem" }}>
          <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#F59E0B" }}>SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 2, verticalAlign: "middle" }} /></div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <input type="email" placeholder="Email" style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "10px 12px", color: "#E2E8F0", fontSize: 14 }} />
            <input type="password" placeholder="Password" style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "10px 12px", color: "#E2E8F0", fontSize: 14 }} />
            <button style={{ background: "#F59E0B", border: "none", color: "#0D1017", fontWeight: 600, fontSize: 14, padding: "10px", borderRadius: 6, cursor: "pointer" }}>Accedi</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ErrorCredits() {
  return (
    <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
      {/* Background — blurred app context */}
      <div style={{ position: "absolute", inset: 0, background: "#0D1017", opacity: 0.85, zIndex: 1 }} />
      <div style={{ position: "absolute", inset: 0, padding: "2rem", zIndex: 0 }}>
        {/* Ghost app content */}
        {[1,2,3,4].map(i => (
          <div key={i} style={{ height: 80, background: "#161B26", border: "1px solid #1E2436", borderRadius: 6, marginBottom: 12, opacity: 0.5 }} />
        ))}
      </div>

      {/* Modal overlay */}
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 10 }}>
        <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 12, padding: "2rem", width: 420, boxShadow: "0 32px 80px rgba(0,0,0,.8)" }}>
          <div style={{ fontSize: 40, textAlign: "center", marginBottom: "1rem" }}>💳</div>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 700, color: "#F1F5F9", textAlign: "center", margin: "0 0 .75rem", letterSpacing: "-0.02em" }}>Crediti esauriti</h2>
          <p style={{ fontSize: 14, color: "#94A3B8", textAlign: "center", lineHeight: 1.65, margin: "0 0 1.5rem" }}>
            Hai usato tutti i crediti del tuo piano <strong style={{ color: "#F59E0B" }}>Creator</strong>. Per continuare a generare, passa a un piano superiore o contatta l'amministratore.
          </p>
          <div style={{ display: "flex", gap: 10 }}>
            <button style={{ flex: 1, background: "transparent", border: "1px solid #2D3748", color: "#CBD5E1", fontWeight: 500, fontSize: 14, padding: "10px", borderRadius: 6, cursor: "pointer" }}>
              Chiudi
            </button>
            <button style={{ flex: 1, background: "#F59E0B", border: "none", color: "#0D1017", fontWeight: 600, fontSize: 14, padding: "10px", borderRadius: 6, cursor: "pointer" }}>
              Vedi piani →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ErrorNetwork() {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      {/* Persistent sticky banner */}
      <div style={{ background: "rgba(245,158,11,.1)", borderBottom: "1px solid rgba(245,158,11,.25)", padding: "10px 2rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 16 }}>⚠️</span>
          <span style={{ fontSize: 13, color: "#FBBF24", fontWeight: 500 }}>Errore di connessione con il servizio AI. Riprova tra qualche istante.</span>
        </div>
        <button style={{ background: "rgba(245,158,11,.15)", border: "1px solid rgba(245,158,11,.3)", color: "#F59E0B", fontWeight: 600, fontSize: 12, padding: "5px 12px", borderRadius: 6, cursor: "pointer" }}>
          Riprova
        </button>
      </div>

      {/* Ghost page content */}
      <div style={{ flex: 1, padding: "2rem 2.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 1.5rem", letterSpacing: "-0.02em" }}>Genera vignette</h1>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem" }}>
          {[
            { done: true, n: 1 },
            { done: true, n: 2 },
            { done: false, n: 3, failed: true },
            { done: false, n: 4 },
          ].map(p => (
            <div key={p.n} style={{ background: "#161B26", border: `1px solid ${p.failed ? "rgba(245,158,11,.3)" : "#1E2436"}`, borderRadius: 8, overflow: "hidden" }}>
              <div style={{ height: 100, background: p.done ? "linear-gradient(135deg,#1a1a2e,#0d1b2a)" : p.failed ? "rgba(245,158,11,.05)" : "#0D1017", display: "flex", alignItems: "center", justifyContent: "center" }}>
                {p.done ? <span style={{ fontSize: 20 }}>✓</span> : p.failed ? <span style={{ fontSize: 20 }}>⚠️</span> : <span style={{ fontSize: 12, color: "#334155" }}>—</span>}
              </div>
              <div style={{ padding: "8px 10px" }}>
                <div style={{ fontSize: 11, color: "#64748B" }}>Vignetta {p.n}</div>
                {p.failed && <div style={{ fontSize: 11, color: "#F59E0B", marginTop: 4 }}>Generazione fallita</div>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ErrorGeneric() {
  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
      {/* Persistent error banner */}
      <div style={{ background: "rgba(239,68,68,.08)", borderBottom: "1px solid rgba(239,68,68,.2)", padding: "12px 2rem", display: "flex", alignItems: "flex-start", gap: 12 }}>
        <span style={{ fontSize: 16, marginTop: 1 }}>🔴</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#F87171", marginBottom: 2 }}>Si è verificato un errore.</div>
          <div style={{ fontSize: 12, color: "#94A3B8" }}>
            Se persiste, contatta l'amministratore.{" "}
            <span style={{ fontFamily: "monospace", background: "rgba(239,68,68,.1)", padding: "1px 6px", borderRadius: 3, color: "#EF4444", cursor: "pointer" }} title="Clicca per copiare">
              ID: err_8f3a2c1d9e0b
            </span>
          </div>
        </div>
        <button style={{ background: "transparent", border: "none", color: "#475569", cursor: "pointer", fontSize: 16 }}>✕</button>
      </div>

      {/* Ghost page content */}
      <div style={{ flex: 1, padding: "2rem 2.5rem" }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 1.5rem", letterSpacing: "-0.02em" }}>Testo</h1>
        {[1, 2, 3].map(i => (
          <div key={i} style={{ height: 56, background: "#161B26", border: "1px solid #1E2436", borderRadius: 6, marginBottom: 8, opacity: 0.6 }} />
        ))}
        <div style={{ marginTop: "1rem", padding: "1rem", background: "rgba(239,68,68,.05)", border: "1px solid rgba(239,68,68,.15)", borderRadius: 8, fontSize: 13, color: "#94A3B8" }}>
          L'operazione "Adatta a sceneggiatura" è stata interrotta. Il tuo testo sorgente è al sicuro.
        </div>
      </div>
    </div>
  );
}

export function ErrorStates() {
  const [active, setActive] = useState<ErrorType>("credits");

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        input { outline: none; }
      `}</style>

      {active !== "session" && <Sidebar />}

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Tab switcher — shows which error we're previewing */}
        <div style={{ background: "#0A0E17", borderBottom: "1px solid #1E2436", padding: "0.75rem 1.5rem", display: "flex", gap: 6, flexWrap: "wrap" }}>
          <span style={{ fontSize: 11, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".06em", alignSelf: "center", marginRight: 4 }}>Stato errore:</span>
          {ERROR_TYPES.map(e => (
            <button key={e.id} onClick={() => setActive(e.id)} style={{
              padding: "4px 12px", borderRadius: 20, fontSize: 12, fontWeight: 500, cursor: "pointer", border: "1px solid",
              background: active === e.id ? "#F59E0B" : "transparent",
              borderColor: active === e.id ? "#F59E0B" : "#2D3748",
              color: active === e.id ? "#0D1017" : "#64748B",
              fontFamily: "'Inter',sans-serif",
            }}>{e.label}</button>
          ))}
        </div>

        {active === "404" && <Error404 />}
        {active === "session" && <ErrorSession />}
        {active === "credits" && <ErrorCredits />}
        {active === "network" && <ErrorNetwork />}
        {active === "generic" && <ErrorGeneric />}
      </div>
    </div>
  );
}
