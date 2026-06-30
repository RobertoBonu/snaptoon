import { useState } from "react";
import { NavIcon } from "./_NavIcons";

const USERS = [
  { email: "marco.rossi@example.com", plan: "Creator", cred: 142, total: 200, created: "01/07/26", active: true, last: "03/07 14:23" },
  { email: "laura.bianchi@studio.it", plan: "Pro", cred: 580, total: 600, created: "28/06/26", active: true, last: "03/07 10:11" },
  { email: "test.user@example.com", plan: "Trial", cred: 12, total: 30, created: "25/06/26", active: false, last: "25/06 18:00" },
  { email: "giulia.rossi@agenzia.com", plan: "Creator", cred: 0, total: 200, created: "20/06/26", active: true, last: "02/07 09:00" },
];

const LOGS = [
  { ts: "03/07 14:23", user: "marco.rossi@example.com", op: "generate_panel", cost: 1, ok: true },
  { ts: "03/07 14:10", user: "marco.rossi@example.com", op: "generate_reference", cost: 1, ok: true },
  { ts: "03/07 13:55", user: "laura.bianchi@studio.it", op: "adapt_script", cost: 5, ok: true },
  { ts: "03/07 13:40", user: "giulia.rossi@agenzia.com", op: "generate_panel", cost: 1, ok: false },
  { ts: "03/07 12:00", user: "laura.bianchi@studio.it", op: "generate_cover", cost: 1, ok: true },
];

export function Admin() {
  const [newUserOpen, setNewUserOpen] = useState(false);
  const [logsOpen, setLogsOpen] = useState(false);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        input:focus,select:focus { outline:none;border-color:#F59E0B !important; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:4px 9px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:12px;font-weight:600;padding:4px 10px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-amber { background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25);color:#F59E0B;font-size:12px;font-weight:600;padding:4px 9px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        th,td { padding:8px 12px;text-align:left; }
        th { font-size:11px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:.06em; }
        td { font-size:13px; }
        tr:not(:last-child) td { border-bottom:1px solid #1E2436; }
      `}</style>

      {/* Sidebar */}
      <div style={{ width: 200, minWidth: 200, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "1.25rem 1rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
          <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} /></span>
        </div>
        {[{ icon: "🏠", l: "Home" }, { icon: "💳", l: "Account" }, { icon: "🛠", l: "Admin", active: true }].map(n => (
          <div key={n.l} style={{ display: "flex", alignItems: "center", gap: 8, padding: "10px 16px", borderRadius: 6, margin: "2px 6px", fontSize: 14, fontWeight: 500, color: (n as any).active ? "#F59E0B" : "#64748B", background: (n as any).active ? "#1A2035" : "transparent", borderLeft: (n as any).active ? "3px solid #F59E0B" : "3px solid transparent", cursor: "pointer" }}>
            <NavIcon label={n.l} active={(n as { active?: boolean }).active} /><span>{n.l}</span>
          </div>
        ))}
        <div style={{ flex: 1 }} />
        <div style={{ padding: "0.75rem", borderTop: "1px solid #1E2436" }}>
          <div style={{ fontSize: 11, color: "#334155", fontWeight: 600 }}>Accesso admin</div>
          <div style={{ fontSize: 12, color: "#475569" }}>roberto@snaptoon.it</div>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, padding: "1.5rem 2rem", overflowY: "auto" }}>
        <div style={{ paddingBottom: "1rem", borderBottom: "1px solid #1E2436", marginBottom: "1.25rem" }}>
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: "0 0 .2rem", letterSpacing: "-0.02em" }}>🛠 Admin</h1>
          <p style={{ fontSize: 12, color: "#64748B", margin: 0 }}>Solo per amministratori.</p>
        </div>

        {/* Metrics */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem", marginBottom: "1.25rem" }}>
          {[
            { label: "Utenti totali", value: "4", sub: "" },
            { label: "Attivi (7 giorni)", value: "3", sub: "" },
            { label: "Crediti consumati", value: "1.240", sub: "questo mese" },
            { label: "Costo stimato API", value: "€ 3,72", sub: "questo mese" },
          ].map(m => (
            <div key={m.label} style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 4 }}>{m.label}</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#F1F5F9", letterSpacing: "-0.02em" }}>{m.value}</div>
              {m.sub && <div style={{ fontSize: 11, color: "#334155" }}>{m.sub}</div>}
            </div>
          ))}
        </div>

        {/* New user */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, marginBottom: "0.75rem", overflow: "hidden" }}>
          <div onClick={() => setNewUserOpen(v => !v)} style={{ padding: "0.85rem 1.25rem", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0A0E17" }}>
            <span style={{ fontWeight: 600, fontSize: 14, color: "#CBD5E1" }}>+ Nuovo utente</span>
            <span style={{ color: "#475569" }}>{newUserOpen ? "▴" : "▾"}</span>
          </div>
          {newUserOpen && (
            <div style={{ padding: "1.25rem", display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.75rem" }}>
              {[{ label: "Email", type: "email", placeholder: "nome@dominio.com" }, { label: "Password temporanea", type: "password", placeholder: "min. 8 caratteri" }].map(f => (
                <div key={f.label}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "#64748B", marginBottom: 4 }}>{f.label}</label>
                  <input type={f.type} placeholder={f.placeholder} style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "7px 10px", color: "#E2E8F0", fontSize: 13 }} />
                </div>
              ))}
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "#64748B", marginBottom: 4 }}>Piano iniziale</label>
                <select style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "7px 10px", color: "#E2E8F0", fontSize: 13 }}>
                  <option>Trial (30 crediti)</option>
                  <option>Creator (200 crediti)</option>
                  <option>Pro (600 crediti)</option>
                </select>
              </div>
              <div style={{ gridColumn: "1/-1", display: "flex", justifyContent: "flex-end" }}>
                <button className="btn-primary" style={{ fontSize: 13, padding: "7px 16px" }}>Crea account</button>
              </div>
            </div>
          )}
        </div>

        {/* Users table */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, marginBottom: "0.75rem", overflow: "hidden" }}>
          <div style={{ padding: "0.85rem 1.25rem", background: "#0A0E17", borderBottom: "1px solid #1E2436" }}>
            <span style={{ fontWeight: 600, fontSize: 14, color: "#CBD5E1" }}>Utenti registrati</span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#0D1017" }}>
                  <th>Email</th>
                  <th>Piano</th>
                  <th>Crediti</th>
                  <th>Creato</th>
                  <th>Stato</th>
                  <th>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {USERS.map(u => (
                  <tr key={u.email} style={{ background: u.active ? "transparent" : "rgba(239,68,68,.03)" }}>
                    <td style={{ color: "#CBD5E1" }}>{u.email}</td>
                    <td><span style={{ fontSize: 11, background: u.plan === "Pro" ? "rgba(124,58,237,.15)" : "rgba(245,158,11,.1)", color: u.plan === "Pro" ? "#A78BFA" : "#F59E0B", padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>{u.plan}</span></td>
                    <td style={{ color: u.cred === 0 ? "#EF4444" : "#94A3B8" }}>{u.cred} / {u.total}</td>
                    <td style={{ color: "#64748B" }}>{u.created}</td>
                    <td>{u.active ? <span style={{ color: "#10B981", fontSize: 12 }}>✓ Attivo</span> : <span style={{ color: "#EF4444", fontSize: 12 }}>🚫 Disabilitato</span>}</td>
                    <td>
                      <div style={{ display: "flex", gap: 4 }}>
                        <button className="btn" title="Modifica">✏️</button>
                        <button className="btn-amber" title="Crediti">🪙</button>
                        {u.active
                          ? <button className="btn" style={{ color: "#EF4444", borderColor: "rgba(239,68,68,.3)" }} title="Disabilita">🚫</button>
                          : <button className="btn" style={{ color: "#10B981", borderColor: "rgba(16,185,129,.3)" }} title="Riabilita">✓</button>
                        }
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Global log */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, overflow: "hidden" }}>
          <div onClick={() => setLogsOpen(v => !v)} style={{ padding: "0.85rem 1.25rem", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0A0E17" }}>
            <span style={{ fontWeight: 600, fontSize: 14, color: "#CBD5E1" }}>📋 Log operazioni globali</span>
            <span style={{ color: "#475569" }}>{logsOpen ? "▴" : "▾"}</span>
          </div>
          {logsOpen && (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#0D1017" }}>
                  <th>Timestamp</th>
                  <th>Utente</th>
                  <th>Operazione</th>
                  <th>Costo</th>
                  <th>Esito</th>
                </tr>
              </thead>
              <tbody>
                {LOGS.map((l, i) => (
                  <tr key={i}>
                    <td style={{ color: "#64748B", fontFamily: "monospace", fontSize: 12 }}>{l.ts}</td>
                    <td style={{ color: "#94A3B8", fontSize: 12 }}>{l.user}</td>
                    <td style={{ color: "#CBD5E1", fontFamily: "monospace", fontSize: 12 }}>{l.op}</td>
                    <td style={{ color: "#94A3B8" }}>-{l.cost}</td>
                    <td>{l.ok ? <span style={{ color: "#10B981", fontSize: 12 }}>✓</span> : <span style={{ color: "#EF4444", fontSize: 12 }}>✗</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
