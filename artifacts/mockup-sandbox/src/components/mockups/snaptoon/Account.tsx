import { useState } from "react";
import { NavIcon } from "./_NavIcons";

const NAV_SIDE = [
  { icon: "🏠", label: "Home" },
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile" },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera" },
  { icon: "📐", label: "Impagina" },
];

const HISTORY = [
  { date: "03/07 14:23", op: "Genera vignetta", delta: -1, bal: 142 },
  { date: "03/07 14:10", op: "Genera variante reference", delta: -1, bal: 143 },
  { date: "03/07 12:50", op: "Adatta sceneggiatura", delta: -5, bal: 144 },
  { date: "03/07 11:30", op: "Genera copertina", delta: -1, bal: 149 },
  { date: "02/07 18:00", op: "Genera vignetta", delta: -1, bal: 150 },
  { date: "02/07 16:40", op: "Genera vignetta", delta: -1, bal: 151 },
  { date: "02/07 15:10", op: "Genera reference personaggio", delta: -1, bal: 152 },
  { date: "01/07 09:00", op: "Rinnovo piano Creator", delta: +200, bal: 153 },
];

export function Account() {
  const [pwForm, setPwForm] = useState(false);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        input:focus { outline:none;border-color:#F59E0B !important; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:13px;font-weight:500;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:13px;font-weight:600;padding:8px 16px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-danger { border:1px solid rgba(239,68,68,.3);background:transparent;color:#EF4444;font-size:13px;font-weight:500;padding:8px 14px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .section { background:#161B26;border:1px solid #1E2436;borderRadius:8px;padding:1.25rem 1.5rem;marginBottom:1rem; }
      `}</style>

      {/* Sidebar */}
      <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
          <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} /></span>
        </div>
        <div style={{ padding: "0.75rem 1rem 0.5rem" }}>
          <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 10px", fontSize: 13, color: "#CBD5E1" }}>La notte del riccio</div>
        </div>
        <div style={{ height: 1, background: "#1E2436", margin: "0.5rem 0" }} />
        {NAV_SIDE.map(n => (
          <div key={n.label} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", borderRadius: 6, margin: "2px 8px", fontSize: 14, fontWeight: 500, color: "#64748B", cursor: "pointer" }}>
            <NavIcon label={n.label} /><span>{n.label}</span>
          </div>
        ))}
        <div style={{ height: 1, background: "#1E2436", margin: "0.5rem 0" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", borderRadius: 6, margin: "2px 8px", fontSize: 14, fontWeight: 500, color: "#F59E0B", background: "#1A2035", borderLeft: "3px solid #F59E0B", cursor: "pointer" }}>
          <NavIcon label="Account" active /><span>Account</span>
        </div>
        <div style={{ flex: 1 }} />
      </div>

      {/* Main */}
      <div style={{ flex: 1, padding: "2rem 2.5rem", overflowY: "auto", maxWidth: 780 }}>
        <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", letterSpacing: "-0.02em" }}>Account e crediti</h1>
        <p style={{ fontSize: 13, color: "#64748B", margin: "0 0 1.5rem" }}>marco.rossi@example.com</p>

        {/* Credits */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1.25rem 1.5rem", marginBottom: "0.75rem" }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>Saldo crediti</div>
          <div style={{ fontSize: "2rem", fontWeight: 800, color: "#F1F5F9", letterSpacing: "-0.03em", marginBottom: 4 }}>142 <span style={{ fontSize: "1rem", fontWeight: 400, color: "#475569" }}>/ 200</span></div>
          <div style={{ height: 5, background: "#0D1017", borderRadius: 4, overflow: "hidden", marginBottom: 6 }}>
            <div style={{ width: "71%", height: "100%", background: "#10B981", borderRadius: 4 }} />
          </div>
          <span style={{ fontSize: 12, background: "rgba(124,58,237,.15)", color: "#A78BFA", padding: "3px 10px", borderRadius: 20, fontWeight: 600 }}>Piano Creator</span>
        </div>

        {/* Plan */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1.25rem 1.5rem", marginBottom: "0.75rem" }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 10 }}>Piano attivo</div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: "#F1F5F9" }}>Creator</span>
            <span style={{ fontSize: 11, background: "rgba(124,58,237,.15)", color: "#A78BFA", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>Attivo</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 12 }}>
            {["200 crediti al mese", "5 progetti", "Qualità Bassa + Media"].map(f => (
              <div key={f} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#94A3B8" }}>
                <span style={{ color: "#10B981" }}>✓</span>{f}
              </div>
            ))}
          </div>
          <p style={{ fontSize: 12, color: "#475569", margin: 0, fontStyle: "italic" }}>Contatta l'amministratore per gestire l'abbonamento.</p>
        </div>

        {/* History */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1.25rem 1.5rem", marginBottom: "0.75rem" }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 10 }}>Storico operazioni</div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ color: "#475569" }}>
                <th style={{ textAlign: "left", padding: "6px 0", fontWeight: 500, borderBottom: "1px solid #1E2436" }}>Data</th>
                <th style={{ textAlign: "left", padding: "6px 0", fontWeight: 500, borderBottom: "1px solid #1E2436" }}>Operazione</th>
                <th style={{ textAlign: "right", padding: "6px 0", fontWeight: 500, borderBottom: "1px solid #1E2436" }}>Costo</th>
                <th style={{ textAlign: "right", padding: "6px 0", fontWeight: 500, borderBottom: "1px solid #1E2436" }}>Saldo</th>
              </tr>
            </thead>
            <tbody>
              {HISTORY.map((h, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #1E2436" }}>
                  <td style={{ padding: "8px 0", color: "#64748B" }}>{h.date}</td>
                  <td style={{ padding: "8px 0", color: "#CBD5E1" }}>{h.op}</td>
                  <td style={{ padding: "8px 0", textAlign: "right", color: h.delta > 0 ? "#10B981" : "#94A3B8", fontWeight: 500 }}>{h.delta > 0 ? `+${h.delta}` : h.delta}</td>
                  <td style={{ padding: "8px 0", textAlign: "right", color: "#64748B" }}>{h.bal}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Settings */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1.25rem 1.5rem", marginBottom: "0.75rem" }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 12 }}>Impostazioni personali</div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: pwForm ? 12 : 0 }}>
            <div>
              <div style={{ fontSize: 12, color: "#475569", marginBottom: 2 }}>Email</div>
              <div style={{ fontSize: 14, color: "#CBD5E1" }}>marco.rossi@example.com</div>
            </div>
            <button className="btn" onClick={() => setPwForm(v => !v)}>🔑 Cambia password</button>
          </div>
          {pwForm && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 12, padding: "12px", background: "#0D1017", borderRadius: 6, border: "1px solid #2D3748" }}>
              {["Vecchia password", "Nuova password", "Conferma nuova password"].map(label => (
                <div key={label}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "#64748B", marginBottom: 4 }}>{label}</label>
                  <input type="password" style={{ width: "100%", background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 12px", color: "#E2E8F0", fontSize: 13 }} />
                </div>
              ))}
              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
                <button className="btn" onClick={() => setPwForm(false)}>Annulla</button>
                <button className="btn-primary">Salva password</button>
              </div>
            </div>
          )}
        </div>

        {/* Logout */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1.25rem 1.5rem" }}>
          <button className="btn-danger">🚪 Esci da SnapToon</button>
        </div>
      </div>
    </div>
  );
}
