import { useState } from "react";
import { NavIcon } from "./_NavIcons";

const NAV = [
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile" },
  { icon: "👥", label: "Personaggi", active: true },
  { icon: "🖼", label: "Genera" },
  { icon: "📐", label: "Impagina" },
];

const CHARACTERS = [
  { name: "Marco Riccio", status: "ok", desc: "Uomo sui 40, barba grigia incolta, giacca di pelle marrone consumata. Occhi stanchi ma acuti, zigomi pronunciati.", variants: 3 },
  { name: "Luisa Ferretti", status: "ok", desc: "Donna 35 anni, capelli corti neri, impermeabile rosso scuro. Mascella decisa, sguardo fermo.", variants: 1 },
  { name: "Il Commissario", status: "missing", desc: "Uomo 55 anni, capelli bianchi, baffi grigi curati. Corporatura robusta, abito grigio ferro.", variants: 0 },
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
          <NavIcon label={n.label} active={(n as { active?: boolean }).active} /><span>{n.label}</span>
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

function StatusDot({ status }: { status: string }) {
  const color = status === "ok" ? "#10B981" : status === "corrupted" ? "#F59E0B" : "#475569";
  const label = status === "ok" ? "🟢" : status === "corrupted" ? "🟠" : "⚪";
  return <span title={status}>{label}</span>;
}

export function Personaggi() {
  const [open, setOpen] = useState<string[]>(["Il Commissario"]);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        textarea:focus,input:focus { outline:none;border-color:#F59E0B !important; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 11px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-amber { background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);color:#F59E0B;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
      `}</style>

      <Sidebar />

      <div style={{ flex: 1, padding: "2rem 2.5rem", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: "1.25rem", borderBottom: "1px solid #1E2436", marginBottom: "1.25rem" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", letterSpacing: "-0.02em" }}>Personaggi</h1>
            <p style={{ fontSize: 13, color: "#64748B", margin: 0 }}>Progetto: La notte del riccio</p>
          </div>
          <button className="btn" style={{ fontSize: 13 }}>+ Aggiungi personaggio</button>
        </div>

        {/* Global status */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <span style={{ fontSize: 14, color: "#CBD5E1", fontWeight: 500 }}>2 / 3 personaggi hanno un'immagine di riferimento</span>
            <button className="btn-amber">🚀 Genera reference per i 1 mancanti</button>
          </div>
          <div style={{ height: 4, background: "#0D1017", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ width: "66%", height: "100%", background: "#10B981", borderRadius: 4 }} />
          </div>
        </div>

        {/* Character list */}
        {CHARACTERS.map(char => (
          <div key={char.name} style={{ marginBottom: "0.75rem" }}>
            <div
              onClick={() => setOpen(o => o.includes(char.name) ? o.filter(x => x !== char.name) : [...o, char.name])}
              style={{ background: "#161B26", border: `1px solid ${char.status === "missing" && open.includes(char.name) ? "#F59E0B" : "#1E2436"}`, borderRadius: open.includes(char.name) ? "8px 8px 0 0" : 8, padding: "0.85rem 1.25rem", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}
            >
              <span style={{ fontWeight: 600, fontSize: 15, color: "#F1F5F9", display: "flex", alignItems: "center", gap: 8 }}>
                <StatusDot status={char.status} />{char.name}
              </span>
              <span style={{ color: "#475569" }}>{open.includes(char.name) ? "▴" : "▾"}</span>
            </div>

            {open.includes(char.name) && (
              <div style={{ background: "#0D1017", border: "1px solid #1E2436", borderTop: "none", borderRadius: "0 0 8px 8px", padding: "1.25rem" }}>
                <div style={{ display: "flex", gap: "1.5rem" }}>
                  {/* Thumbnail */}
                  <div style={{ flexShrink: 0 }}>
                    <div style={{ width: 120, height: 160, background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 8 }}>
                      {char.status === "ok"
                        ? <div style={{ width: "100%", height: "100%", background: `linear-gradient(160deg,#${char.name === "Marco Riccio" ? "2a1f1a" : "1a1a2e"},#${char.name === "Marco Riccio" ? "1a2a1f" : "2a1f2a"})`, borderRadius: 5, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32 }}>{char.name === "Marco Riccio" ? "🕵️" : "👩"}</div>
                        : <span style={{ fontSize: 32, opacity: .3 }}>👤</span>
                      }
                    </div>
                    <div style={{ display: "flex", gap: 4, flexDirection: "column" }}>
                      <button className="btn" style={{ fontSize: 11, width: "100%", textAlign: "center" }}>📤 Carica file</button>
                      <button className={char.status === "missing" ? "btn-primary" : "btn"} style={{ fontSize: 11, width: "100%", textAlign: "center" }}>🔄 {char.status === "missing" ? "Genera con AI" : "Rigenera con AI"}</button>
                      <button className="btn" style={{ fontSize: 11, width: "100%", textAlign: "center" }}>👁 Vedi prompt</button>
                    </div>
                  </div>

                  {/* Description + variants */}
                  <div style={{ flex: 1 }}>
                    <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 6 }}>Descrizione visiva</label>
                    <textarea style={{ width: "100%", background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "10px 12px", color: "#E2E8F0", fontSize: 13, minHeight: 80 }} defaultValue={char.desc} />
                    <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 6, marginBottom: "1rem" }}>
                      <button className="btn-primary" style={{ fontSize: 11 }}>💾 Salva descrizione</button>
                    </div>

                    {/* Cost preview if missing */}
                    {char.status === "missing" && (
                      <div style={{ background: "rgba(245,158,11,.08)", border: "1px solid rgba(245,158,11,.2)", borderRadius: 6, padding: "8px 12px", marginBottom: "1rem", fontSize: 12, color: "#F59E0B" }}>
                        ✨ Generare una reference costa <strong>1 credito</strong>. Saldo: 142.
                      </div>
                    )}

                    {/* Additional references */}
                    <details style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 6, overflow: "hidden" }}>
                      <summary style={{ padding: "8px 12px", cursor: "pointer", fontSize: 13, fontWeight: 500, color: "#94A3B8", listStyle: "none", display: "flex", justifyContent: "space-between" }}>
                        <span>📚 Reference aggiuntive ({char.variants}/7)</span><span>▸</span>
                      </summary>
                      <div style={{ padding: "12px", borderTop: "1px solid #1E2436" }}>
                        <div style={{ fontSize: 12, color: "#64748B", marginBottom: 10 }}>Varianti per garantire coerenza da diverse angolazioni e pose.</div>
                        {char.status === "ok" && (
                          <button className="btn-amber" style={{ marginBottom: 10, fontSize: 11 }}>✨ Genera {7 - char.variants} varianti mancanti</button>
                        )}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
                          {["Profilo", "3/4", "Full body", "Sorriso", "Azione", "Espressione"].map((tipo, i) => (
                            <div key={tipo} style={{ background: "#0D1017", border: "1px solid #1E2436", borderRadius: 4, padding: "8px", textAlign: "center" }}>
                              <div style={{ fontSize: 10, color: "#475569", marginBottom: 4 }}>Slot {i + 2}</div>
                              <div style={{ height: 40, background: i < char.variants ? "linear-gradient(135deg,#1E2436,#2D3748)" : "#0D1017", borderRadius: 3, marginBottom: 4, display: "flex", alignItems: "center", justifyContent: "center" }}>
                                {i < char.variants ? <span style={{ fontSize: 14 }}>✓</span> : <span style={{ fontSize: 10, color: "#334155" }}>—</span>}
                              </div>
                              <div style={{ fontSize: 10, color: "#64748B" }}>{tipo}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Add character form */}
        <div style={{ background: "#161B26", border: "1px dashed #2D3748", borderRadius: 8, padding: "1rem 1.25rem", marginTop: "0.5rem" }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: "#64748B", marginBottom: 10 }}>+ Aggiungi personaggio</div>
          <div style={{ display: "flex", gap: 10 }}>
            <input type="text" placeholder="Nome personaggio" style={{ flex: 1, background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 12px", color: "#E2E8F0", fontSize: 13 }} />
            <button className="btn-primary" style={{ fontSize: 12 }}>Aggiungi</button>
          </div>
        </div>
      </div>
    </div>
  );
}
