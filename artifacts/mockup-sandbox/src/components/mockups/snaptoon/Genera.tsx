import { useState } from "react";

const NAV = [
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile" },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera", active: true },
  { icon: "📐", label: "Impagina" },
];

const PANELS = [
  { n: 1, done: true, cast: ["Marco", "Luisa"], desc: "Marco si affaccia dalla finestra del vecchio palazzo. Piove forte. Luisa lo osserva dall'ombra del portico.", dialoghi: [{ tipo: "DIDASCALIA", testo: "Milano, 1987." }, { tipo: "FUMETTO", speaker: "Marco", testo: "Luisa..." }] },
  { n: 2, done: true, cast: ["Luisa"], desc: "Primo piano di Luisa. Sguardo deciso, mascella contratta. Tiene in mano una lettera bagnata.", dialoghi: [{ tipo: "FUMETTO", speaker: "Luisa", testo: "So tutto." }] },
  { n: 3, done: false, cast: ["Marco", "Luisa"], desc: "I due si fronteggiano sul pianerottolo. La luce fioca della lampada proietta ombre lunghe.", dialoghi: [] },
  { n: 4, done: false, cast: ["Marco"], desc: "Marco apre la porta. Il suo volto cambia espressione quando vede l'interno della stanza.", dialoghi: [{ tipo: "PENSIERO", speaker: "Marco", testo: "Deve aver trovato le lettere." }] },
];

function Sidebar() {
  return (
    <div style={{ width: 240, minWidth: 240, background: "#0A0E17", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "1.25rem 1.25rem 0.75rem", borderBottom: "1px solid #1E2436" }}>
        <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>
          SnapToon<span style={{ display: "inline-block", width: 6, height: 6, background: "#7C3AED", borderRadius: "50%", marginLeft: 3, verticalAlign: "middle", marginBottom: 4 }} />
        </span>
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

type Mode = "default" | "balloon";

export function Genera() {
  const [mode, setMode] = useState<Mode>("default");
  const [balloonPanel, setBalloonPanel] = useState<{ page: number; panel: number } | null>(null);
  const [coverOpen, setCoverOpen] = useState(false);
  const [selectedDialogo, setSelectedDialogo] = useState(0);

  if (mode === "balloon" && balloonPanel) {
    const panel = PANELS[balloonPanel.panel - 1];
    const dialoghi = panel.dialoghi.filter(d => d.tipo !== "DIDASCALIA" && d.tipo !== "SFX");
    return (
      <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
          * { box-sizing: border-box; }
          .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 10px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
          .btn:hover { background:#1E2436; }
          .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
          input[type=range] { width:100%;accent-color:#F59E0B; }
        `}</style>
        <Sidebar />
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {/* Header */}
          <div style={{ padding: "1rem 1.5rem", borderBottom: "1px solid #1E2436", display: "flex", alignItems: "center", gap: 12 }}>
            <button className="btn" onClick={() => setMode("default")}>← Indietro</button>
            <h2 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 600, color: "#F1F5F9" }}>
              🎈 Balloon — Pagina {balloonPanel.page}, Vignetta {balloonPanel.panel}
            </h2>
          </div>
          {/* Two-column layout */}
          <div style={{ flex: 1, display: "flex", gap: 0 }}>
            {/* Left — Canvas (60%) */}
            <div style={{ flex: "0 0 60%", padding: "1.5rem", borderRight: "1px solid #1E2436", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: ".06em" }}>Canvas vignetta</div>
              <div style={{ position: "relative", aspectRatio: "4/3", background: "linear-gradient(135deg,#1a1a2e,#0d1b2a)", borderRadius: 8, border: "1px solid #2D3748", overflow: "hidden" }}>
                {/* Simulated image */}
                <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 48, opacity: .4 }}>🌧️</div>
                {/* Balloon overlay */}
                {dialoghi[selectedDialogo] && (
                  <div style={{ position: "absolute", top: "20%", left: "30%", background: "#FFFFFF", border: "2px solid #000000", borderRadius: 20, padding: "8px 14px", fontSize: 12, color: "#000000", fontWeight: 500, maxWidth: 160, textAlign: "center", cursor: "move" }}>
                    {dialoghi[selectedDialogo].testo}
                    {/* Tail */}
                    <div style={{ position: "absolute", bottom: -12, left: "40%", width: 0, height: 0, borderLeft: "8px solid transparent", borderRight: "8px solid transparent", borderTop: "12px solid #000000" }} />
                  </div>
                )}
                <div style={{ position: "absolute", bottom: 8, right: 8, fontSize: 11, color: "rgba(255,255,255,.4)", fontStyle: "italic" }}>Trascina per riposizionare</div>
              </div>
              <div style={{ fontSize: 11, color: "#475569", textAlign: "center" }}>Posizione corrente: X 42% · Y 22%</div>
            </div>

            {/* Right — Controls (40%) */}
            <div style={{ flex: "0 0 40%", padding: "1.5rem", overflowY: "auto" }}>
              {/* Dialogo selector */}
              <div style={{ marginBottom: "1.25rem" }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Dialogo da modificare</div>
                {dialoghi.length === 0 && <div style={{ fontSize: 13, color: "#475569" }}>Nessun dialogo in questa vignetta.</div>}
                {dialoghi.map((d, i) => (
                  <div key={i} onClick={() => setSelectedDialogo(i)} style={{ padding: "8px 12px", background: selectedDialogo === i ? "rgba(245,158,11,.1)" : "#161B26", border: `1px solid ${selectedDialogo === i ? "#F59E0B" : "#1E2436"}`, borderRadius: 6, marginBottom: 4, cursor: "pointer", fontSize: 13 }}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: "#64748B", textTransform: "uppercase", marginBottom: 2 }}>{d.tipo}{(d as any).speaker ? ` · ${(d as any).speaker}` : ""}</div>
                    <div style={{ color: "#CBD5E1" }}>"{d.testo}"</div>
                  </div>
                ))}
              </div>

              {dialoghi.length > 0 && (
                <>
                  {/* Position */}
                  <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem", marginBottom: "0.75rem" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 10 }}>Posizione</div>
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <label style={{ fontSize: 12, color: "#94A3B8" }}>X (orizzontale)</label>
                        <span style={{ fontSize: 12, color: "#F59E0B", fontWeight: 600 }}>42%</span>
                      </div>
                      <input type="range" min={0} max={100} defaultValue={42} />
                    </div>
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <label style={{ fontSize: 12, color: "#94A3B8" }}>Y (verticale)</label>
                        <span style={{ fontSize: 12, color: "#F59E0B", fontWeight: 600 }}>22%</span>
                      </div>
                      <input type="range" min={0} max={100} defaultValue={22} />
                    </div>
                    <div style={{ display: "flex", gap: 6 }}>
                      {["⬆ Alto", "◆ Centro", "⬇ Basso"].map(p => (
                        <button key={p} className="btn" style={{ flex: 1, fontSize: 11 }}>{p}</button>
                      ))}
                    </div>
                  </div>

                  {/* Balloon shape */}
                  <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem", marginBottom: "0.75rem" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Forma del balloon</div>
                    <select style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "7px 10px", color: "#E2E8F0", fontSize: 13 }}>
                      <option>Ovale (standard)</option>
                      <option>Rettangolare</option>
                      <option>Nuvola (pensiero)</option>
                      <option>Sgranato (urlo)</option>
                      <option>Senza bordo</option>
                    </select>
                  </div>

                  {/* Tail */}
                  <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, padding: "1rem", marginBottom: "0.75rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em" }}>🎯 Tail (coda)</div>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ fontSize: 11, color: "#64748B" }}>Mostra</span>
                        <div style={{ width: 32, height: 18, background: "#F59E0B", borderRadius: 9, position: "relative", cursor: "pointer" }}>
                          <div style={{ position: "absolute", right: 2, top: 2, width: 14, height: 14, background: "#0D1017", borderRadius: 7 }} />
                        </div>
                      </div>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <label style={{ fontSize: 12, color: "#94A3B8" }}>Tail X</label>
                        <span style={{ fontSize: 12, color: "#F59E0B", fontWeight: 600 }}>48%</span>
                      </div>
                      <input type="range" min={0} max={100} defaultValue={48} />
                    </div>
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <label style={{ fontSize: 12, color: "#94A3B8" }}>Tail Y</label>
                        <span style={{ fontSize: 12, color: "#F59E0B", fontWeight: 600 }}>65%</span>
                      </div>
                      <input type="range" min={0} max={100} defaultValue={65} />
                    </div>
                    <div style={{ display: "flex", gap: 6 }}>
                      {["↖", "↗", "↙", "↘"].map(d => (
                        <button key={d} className="btn" style={{ flex: 1, fontSize: 14 }}>{d}</button>
                      ))}
                    </div>
                    <button className="btn" style={{ width: "100%", marginTop: 8, fontSize: 11 }}>↩️ Tail automatica</button>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="btn" style={{ flex: 1, fontSize: 11 }}>↩️ Auto-posizione tutti</button>
                    <button className="btn" style={{ flex: 1, fontSize: 11 }}>🧹 Reset tutti</button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // DEFAULT mode
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter', sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 10px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif;transition:background .15s; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:1px solid #F59E0B;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-primary:hover { background:#FBBF24; }
        .panel-card { background:#161B26;border:1px solid #1E2436;border-radius:8px;overflow:hidden; }
        .panel-card:hover { border-color:#2D3748; }
      `}</style>

      <Sidebar />

      <div style={{ flex: 1, padding: "2rem 2.5rem", overflowY: "auto" }}>
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", paddingBottom: "1.25rem", borderBottom: "1px solid #1E2436", marginBottom: "1.25rem" }}>
          <div>
            <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", color: "#F1F5F9", letterSpacing: "-0.02em" }}>Genera vignette</h1>
            <p style={{ fontSize: 13, color: "#64748B", margin: 0 }}>Heavy Ink Noir · Qualità Media · OpenAI gpt-image-1</p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn">🚀 Genera mancanti (2)</button>
            <button className="btn-primary">🌙 Genera TUTTO (4)</button>
          </div>
        </div>

        {/* Status bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0.65rem 1rem", background: "#0A0E17", border: "1px solid #1E2436", borderRadius: 6, marginBottom: "1rem" }}>
          <span style={{ fontWeight: 700, color: "#F59E0B", fontSize: 15 }}>2/4</span>
          <span style={{ fontSize: 13, color: "#94A3B8" }}>vignette generate</span>
          <div style={{ flex: 1, height: 4, background: "#1E2436", borderRadius: 4, overflow: "hidden" }}>
            <div style={{ width: "50%", height: "100%", background: "#F59E0B", borderRadius: 4 }} />
          </div>
        </div>

        {/* Warning */}
        <div style={{ background: "rgba(245,158,11,.08)", border: "1px solid rgba(245,158,11,.2)", borderRadius: 6, padding: "10px 14px", marginBottom: "1.25rem", fontSize: 13, color: "#F59E0B" }}>
          ⚠️ 1 personaggio senza reference. Vai su <strong>👥 Personaggi</strong> per generarla prima.
        </div>

        {/* === COPERTINA === */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, overflow: "hidden", marginBottom: "0.75rem" }}>
          <div onClick={() => setCoverOpen(v => !v)} style={{ padding: "0.85rem 1.25rem", background: "#0A0E17", borderBottom: coverOpen ? "1px solid #1E2436" : "none", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: "#CBD5E1" }}>🎨 Copertina</span>
            <span style={{ color: "#475569" }}>{coverOpen ? "▴" : "▾"}</span>
          </div>
          {coverOpen && (
            <div style={{ padding: "1.25rem" }}>
              <div style={{ display: "flex", gap: "1.5rem", marginBottom: "1.25rem" }}>
                {/* Metadata */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Metadati</div>
                  {[{ label: "Titolo", val: "La notte del riccio" }, { label: "Sottotitolo", val: "Un noir all'italiana" }, { label: "Autore", val: "R. Ferretti" }].map(f => (
                    <div key={f.label} style={{ marginBottom: 6 }}>
                      <div style={{ fontSize: 11, color: "#475569", marginBottom: 2 }}>{f.label}</div>
                      <div style={{ fontSize: 13, color: "#94A3B8" }}>{f.val} <span style={{ color: "#334155", fontSize: 11 }}>← da 📝 Testo</span></div>
                    </div>
                  ))}
                </div>
                {/* Preview columns */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Illustrazione (senza testi)</div>
                  <div style={{ aspectRatio: "2/3", background: "linear-gradient(160deg,#1a1a2e,#0d1b2a,#1a1022)", border: "1px solid #2D3748", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32 }}>🌙</div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Copertina finale (con testi)</div>
                  <div style={{ aspectRatio: "2/3", background: "linear-gradient(160deg,#1a1a2e,#0d1b2a,#1a1022)", border: "1px solid #2D3748", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 6, padding: "1rem" }}>
                    <div style={{ fontFamily: "serif", fontSize: 11, color: "#F59E0B", fontWeight: 700, textAlign: "center", textTransform: "uppercase", letterSpacing: ".1em" }}>LA NOTTE DEL RICCIO</div>
                    <div style={{ fontSize: 9, color: "#94A3B8", textAlign: "center" }}>Un noir all'italiana</div>
                    <span style={{ fontSize: 28, marginTop: 8, opacity: .6 }}>🌙</span>
                    <div style={{ fontSize: 8, color: "#475569", marginTop: "auto" }}>R. Ferretti</div>
                  </div>
                </div>
              </div>
              {/* Actions */}
              <div style={{ display: "flex", gap: 8, marginBottom: "1.25rem" }}>
                <button className="btn-primary" style={{ fontSize: 12 }}>🎨 Genera illustrazione</button>
                <button className="btn" style={{ fontSize: 12 }}>🎬 Scena copertina</button>
                <button className="btn" style={{ fontSize: 12 }}>🎨 Renderizza copertina</button>
              </div>
              {/* Text boxes */}
              <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 8 }}>Box di testo</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.65rem" }}>
                {["Titolo", "Sottotitolo", "Autore"].map(box => (
                  <div key={box} style={{ background: "#0D1017", border: "1px solid #1E2436", borderRadius: 6, padding: "0.75rem" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#64748B", marginBottom: 8, textTransform: "uppercase" }}>{box}</div>
                    {[["Font", "select"], ["Dimensione", "number"], ["Colore", "color"], ["Posizione X", "number"], ["Posizione Y", "number"]].map(([lbl, tp]) => (
                      <div key={lbl} style={{ marginBottom: 4 }}>
                        <div style={{ fontSize: 10, color: "#475569", marginBottom: 2 }}>{lbl}</div>
                        <input type={tp} style={{ width: "100%", background: "#161B26", border: "1px solid #2D3748", borderRadius: 4, padding: "4px 8px", color: "#E2E8F0", fontSize: 11 }} defaultValue={tp === "number" ? "14" : tp === "color" ? "#FFFFFF" : ""} />
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* === PAGE 1 === */}
        <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, overflow: "hidden", marginBottom: "0.75rem" }}>
          <div style={{ padding: "0.85rem 1rem", background: "#0A0E17", borderBottom: "1px solid #1E2436", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: "#CBD5E1" }}>📖 Pagina 1 — 4 vignette</span>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <span style={{ fontSize: 11, color: "#475569" }}>Gabbia: 2×2 · 4 vignette</span>
              <button className="btn" style={{ fontSize: 11 }}>💾 Salva gabbia</button>
            </div>
          </div>

          <div style={{ padding: "1rem", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.75rem" }}>
            {PANELS.map(p => (
              <div key={p.n} className="panel-card">
                <div style={{ padding: "6px 10px", background: "#0A0E17", borderBottom: "1px solid #1E2436", fontSize: 11, fontWeight: 600, color: "#64748B", textTransform: "uppercase", letterSpacing: ".05em" }}>
                  Vignetta {p.n}
                </div>
                <div style={{ aspectRatio: "4/3", background: "#0D1017", display: "flex", alignItems: "center", justifyContent: "center", borderBottom: "1px solid #1E2436", overflow: "hidden", position: "relative" }}>
                  {p.done ? (
                    <>
                      <div style={{ position: "absolute", inset: 0, background: p.n === 1 ? "linear-gradient(135deg,#1a2035,#2d1f3d)" : "linear-gradient(135deg,#1f2a1a,#2a1f1f)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <span style={{ fontSize: 24, opacity: .6 }}>{p.n === 1 ? "🌧️" : "📄"}</span>
                      </div>
                      <div style={{ position: "absolute", top: 6, right: 6, background: "rgba(16,185,129,.2)", border: "1px solid #10B981", borderRadius: 4, padding: "2px 6px", fontSize: 10, color: "#10B981", fontWeight: 600 }}>✓</div>
                    </>
                  ) : (
                    <span style={{ fontSize: 12, color: "#334155", fontStyle: "italic" }}>— non ancora —</span>
                  )}
                </div>
                <div style={{ padding: "8px 10px" }}>
                  <div style={{ fontSize: 11, color: "#64748B", lineHeight: 1.5, marginBottom: 4, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{p.desc}</div>
                  <div style={{ fontSize: 11, color: "#475569", marginBottom: 8 }}>👥 {p.cast.join(", ")}</div>
                  <div style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                    <button className={p.done ? "btn" : "btn-primary"} style={{ flex: 1, fontSize: 11 }}>{p.done ? "🔄 Rigenera" : "✨ Genera"}</button>
                    <button className="btn" style={{ padding: "5px 8px" }}>🎬</button>
                  </div>
                  <div style={{ display: "flex", gap: 4 }}>
                    <button className="btn" style={{ flex: 1, fontSize: 11 }}>👁 Prompt</button>
                    <button
                      className="btn"
                      style={{ flex: 1, fontSize: 11, opacity: p.dialoghi.filter(d => d.tipo !== "DIDASCALIA").length === 0 ? 0.4 : 1 }}
                      onClick={() => { if (p.dialoghi.length > 0) { setBalloonPanel({ page: 1, panel: p.n }); setMode("balloon"); } }}
                    >
                      🎈 Balloon{p.dialoghi.filter(d => d.tipo !== "DIDASCALIA").length > 0 ? ` (${p.dialoghi.filter(d => d.tipo !== "DIDASCALIA").length})` : ""}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <button className="btn" style={{ width: "100%", padding: "10px", textAlign: "center", borderStyle: "dashed" }}>➕ Pagina dopo</button>
      </div>
    </div>
  );
}
