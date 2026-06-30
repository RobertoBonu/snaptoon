import { useState } from "react";
import { NavIcon } from "./_NavIcons";

const NAV = [
  { icon: "📝", label: "Testo", active: true },
  { icon: "🎨", label: "Stile" },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera" },
  { icon: "📐", label: "Impagina" },
];

const PAGES = [
  {
    n: 1, panels: [
      { n: 1, desc: "Marco si affaccia dalla finestra del vecchio palazzo. Piove forte.", dialoghi: [{ tipo: "DIDASCALIA", testo: "Milano, 1987. Notte fonda." }] },
      { n: 2, desc: "Luisa lo osserva dall'ombra del portico. Tiene in mano una lettera bagnata.", dialoghi: [{ tipo: "FUMETTO", speaker: "Luisa", testo: "So tutto, Marco." }] },
      { n: 3, desc: "I due si fronteggiano sul pianerottolo. Luce fioca.", dialoghi: [{ tipo: "FUMETTO", speaker: "Marco", testo: "Non è come pensi." }, { tipo: "PENSIERO", speaker: "Marco", testo: "Deve aver trovato le lettere." }] },
    ]
  },
  {
    n: 2, panels: [
      { n: 1, desc: "Marco apre la porta. Il suo volto cambia espressione.", dialoghi: [] },
      { n: 2, desc: "Interno dell'appartamento. Disordine totale. Cassetti aperti.", dialoghi: [{ tipo: "SFX", testo: "CRASH!" }] },
    ]
  },
];

function Sidebar({ compact }: { compact?: boolean }) {
  return (
    <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
        <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
          SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} />
        </span>
      </div>
      <div style={{ padding: "0.75rem 1rem 0.5rem" }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>Progetto</div>
        <div style={{ background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "8px 10px", fontSize: 13, color: "#CBD5E1", display: "flex", justifyContent: "space-between" }}>
          <span>La notte del riccio</span><span style={{ color: "#475569" }}>▾</span>
        </div>
      </div>
      <div style={{ height: 1, background: "#1E2436", margin: "0.5rem 0" }} />
      <div style={{ fontSize: 10, fontWeight: 600, color: "#334155", textTransform: "uppercase", letterSpacing: ".08em", padding: "0.25rem 1.25rem" }}>Navigazione</div>
      {NAV.map(n => (
        <div key={n.label} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 20px", borderRadius: 6, margin: "2px 8px", fontSize: 14, fontWeight: 500, color: n.active ? "#F59E0B" : "#64748B", background: n.active ? "#1A2035" : "transparent", borderLeft: n.active ? "3px solid #F59E0B" : "3px solid transparent", cursor: "pointer" }}>
          <NavIcon label={n.label} active={(n as { active?: boolean }).active} /><span>{n.label}</span>
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
      </div>
    </div>
  );
}

export function Testo() {
  const [tab, setTab] = useState<"sorgente" | "sceneggiatura">("sceneggiatura");
  const [openPages, setOpenPages] = useState<number[]>([1]);

  function togglePage(n: number) {
    setOpenPages(p => p.includes(n) ? p.filter(x => x !== n) : [...p, n]);
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        textarea { resize: vertical; font-family: 'Inter',sans-serif; }
        textarea:focus,input:focus { outline: none; border-color:#F59E0B !important; box-shadow:0 0 0 3px rgba(245,158,11,.1) !important; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 11px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .tab-btn { padding:8px 16px;border:none;background:transparent;color:#64748B;font-size:14px;font-weight:500;cursor:pointer;border-bottom:2px solid transparent;font-family:'Inter',sans-serif; }
        .tab-btn.active { color:#F59E0B;border-bottom-color:#F59E0B; }
        .tipo-badge { font-size:10px;font-weight:700;padding:2px 6px;border-radius:3px;text-transform:uppercase;letter-spacing:.06em; }
      `}</style>

      <Sidebar />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Header */}
        <div style={{ padding: "1.5rem 2rem 0", borderBottom: "1px solid #1E2436" }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", letterSpacing: "-0.02em" }}>Testo</h1>
          <p style={{ fontSize: 13, color: "#64748B", margin: "0 0 1rem" }}>Progetto: La notte del riccio</p>
          <div style={{ display: "flex", gap: 0, borderBottom: "1px solid #1E2436", marginBottom: -1 }}>
            <button className={`tab-btn${tab === "sorgente" ? " active" : ""}`} onClick={() => setTab("sorgente")}>Sorgente</button>
            <button className={`tab-btn${tab === "sceneggiatura" ? " active" : ""}`} onClick={() => setTab("sceneggiatura")}>Sceneggiatura</button>
          </div>
        </div>

        <div style={{ flex: 1, padding: "1.5rem 2rem", overflowY: "auto" }}>
          {tab === "sorgente" ? (
            <div style={{ maxWidth: 720 }}>
              <div style={{ marginBottom: "1.5rem" }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Carica file testo (.txt)</label>
                <div style={{ border: "2px dashed #2D3748", borderRadius: 8, padding: "2rem", textAlign: "center", color: "#475569", fontSize: 14 }}>
                  📄 Trascina un file .txt qui, oppure clicca per selezionarlo
                </div>
              </div>
              <div style={{ marginBottom: "1.5rem" }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>…oppure incolla il testo</label>
                <textarea style={{ width: "100%", background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "12px", color: "#E2E8F0", fontSize: 14, minHeight: 200 }} placeholder="Incolla qui il tuo testo sorgente..." />
              </div>
              <div style={{ background: "#0A0E17", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#CBD5E1", marginBottom: 4 }}>Costo operazione</div>
                <div style={{ fontSize: 13, color: "#94A3B8" }}>Adattamento sceneggiatura: <strong style={{ color: "#F59E0B" }}>5 crediti</strong> · Saldo attuale: 142</div>
              </div>
              <button className="btn-primary" style={{ width: "100%", padding: "10px", fontSize: 14 }}>✨ Adatta a sceneggiatura</button>
            </div>
          ) : (
            <div style={{ maxWidth: 860 }}>
              {/* Logline */}
              <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Logline</div>
                <textarea style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "10px 12px", color: "#E2E8F0", fontSize: 14, minHeight: 56 }} defaultValue="Un detective stanco ritrova la sua ex in una notte di pioggia torrenziale, portando alla luce un passato che credeva sepolto." />
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
                  <button className="btn-primary" style={{ fontSize: 11 }}>💾 Salva logline</button>
                </div>
              </div>

              {/* Characters section */}
              <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem 1.25rem", marginBottom: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: ".06em" }}>Personaggi</div>
                  <button className="btn" style={{ fontSize: 11 }}>+ Aggiungi personaggio</button>
                </div>
                {["Marco Riccio", "Luisa Ferretti"].map(name => (
                  <details key={name} style={{ background: "#0D1017", border: "1px solid #1E2436", borderRadius: 6, marginBottom: 6 }}>
                    <summary style={{ padding: "10px 12px", cursor: "pointer", fontSize: 14, fontWeight: 500, color: "#CBD5E1", listStyle: "none", display: "flex", justifyContent: "space-between" }}>
                      <span>👤 {name}</span><span style={{ color: "#475569" }}>▸</span>
                    </summary>
                    <div style={{ padding: "10px 12px", borderTop: "1px solid #1E2436" }}>
                      <textarea style={{ width: "100%", background: "#161B26", border: "1px solid #2D3748", borderRadius: 4, padding: "8px 10px", color: "#E2E8F0", fontSize: 13, minHeight: 60 }} defaultValue={name === "Marco Riccio" ? "Uomo sui 40, barba grigia, giacca di pelle marrone. Occhi stanchi ma acuti." : "Donna 35 anni, capelli corti neri, impermeabile rosso scuro."} />
                      <div style={{ display: "flex", gap: 6, marginTop: 8, justifyContent: "flex-end" }}>
                        <button className="btn" style={{ fontSize: 11 }}>🗑 Elimina</button>
                        <button className="btn-primary" style={{ fontSize: 11 }}>💾 Salva</button>
                      </div>
                    </div>
                  </details>
                ))}
              </div>

              {/* Pages */}
              {PAGES.map(page => (
                <div key={page.n} style={{ marginBottom: "0.75rem" }}>
                  <div onClick={() => togglePage(page.n)} style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: openPages.includes(page.n) ? "8px 8px 0 0" : 8, padding: "0.75rem 1.25rem", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 600, fontSize: 14, color: "#CBD5E1" }}>📖 Pagina {page.n} — {page.panels.length} vignette</span>
                    <span style={{ color: "#475569" }}>{openPages.includes(page.n) ? "▴" : "▾"}</span>
                  </div>
                  {openPages.includes(page.n) && (
                    <div style={{ background: "#0D1017", border: "1px solid #1E2436", borderTop: "none", borderRadius: "0 0 8px 8px", padding: "0.75rem 1rem" }}>
                      {page.panels.map(panel => (
                        <div key={panel.n} style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 6, padding: "0.75rem 1rem", marginBottom: "0.5rem" }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: "#475569", marginBottom: 6, textTransform: "uppercase", letterSpacing: ".06em" }}>Vignetta {panel.n}</div>
                          <textarea style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 4, padding: "8px", color: "#E2E8F0", fontSize: 13, minHeight: 56 }} defaultValue={panel.desc} />
                          {panel.dialoghi.length > 0 && (
                            <div style={{ marginTop: 8 }}>
                              <div style={{ fontSize: 11, fontWeight: 600, color: "#475569", marginBottom: 6 }}>Dialoghi ({panel.dialoghi.length})</div>
                              {panel.dialoghi.map((d, i) => (
                                <div key={i} style={{ display: "flex", gap: 8, alignItems: "center", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 4, padding: "6px 8px", marginBottom: 4 }}>
                                  <span className="tipo-badge" style={{ background: d.tipo === "FUMETTO" ? "rgba(124,58,237,.2)" : d.tipo === "PENSIERO" ? "rgba(59,130,246,.2)" : d.tipo === "DIDASCALIA" ? "rgba(16,185,129,.2)" : "rgba(245,158,11,.2)", color: d.tipo === "FUMETTO" ? "#A78BFA" : d.tipo === "PENSIERO" ? "#60A5FA" : d.tipo === "DIDASCALIA" ? "#34D399" : "#F59E0B" }}>{d.tipo}</span>
                                  {(d as any).speaker && <span style={{ fontSize: 12, color: "#64748B" }}>{(d as any).speaker}:</span>}
                                  <span style={{ fontSize: 13, color: "#CBD5E1", flex: 1 }}>{d.testo}</span>
                                  <button className="btn" style={{ padding: "2px 7px", fontSize: 11 }}>🗑</button>
                                </div>
                              ))}
                            </div>
                          )}
                          <button className="btn" style={{ fontSize: 11, marginTop: 6 }}>+ Aggiungi dialogo</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
