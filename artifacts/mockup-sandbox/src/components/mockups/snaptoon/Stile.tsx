import { useState } from "react";

const NAV = [
  { icon: "📝", label: "Testo" },
  { icon: "🎨", label: "Stile", active: true },
  { icon: "👥", label: "Personaggi" },
  { icon: "🖼", label: "Genera" },
  { icon: "📐", label: "Impagina" },
];

const CATEGORIES = ["I miei stili", "Fumetto", "Illustrazione", "Fotografia", "Cinema", "Kids", "Fot. d'autore"];

const PRESETS = [
  { id: 1, name: "Heavy Ink Noir", cat: "Fumetto", desc: "Deep ambient black inks, heavy chiaroscuro, dramatic shadows. Urban crime aesthetic." },
  { id: 2, name: "Silver Age Comics", cat: "Fumetto", desc: "Bold outlines, flat CMYK halftone dots, vibrant primary palette, retro superhero energy." },
  { id: 3, name: "Ligne Claire", cat: "Fumetto", desc: "Clean uniform line weight, bright flat fills, zero shadows. Hergé-inspired European tradition." },
  { id: 4, name: "Manga Shonen", cat: "Fumetto", desc: "High contrast B&W, speed lines, expressive distortion, screen tones, kinetic energy." },
  { id: 5, name: "Horror Woodcut", cat: "Fumetto", desc: "Rough cross-hatching, aged texture, cold desaturated palette, scratched relief look." },
  { id: 6, name: "Pop Art", cat: "Fumetto", desc: "Lichtenstein-style Ben-Day dots, thick black outlines, saturated primary colors." },
];

const CUSTOM_FIELDS = [
  { label: "Nome", value: "Heavy Ink Noir — Custom" },
  { label: "Descrizione", value: "Versione personalizzata con ombre più morbide e palette leggermente calda.", multiline: true },
  { label: "Technique", value: "digital inking, traditional pen simulation" },
  { label: "Aesthetic", value: "noir, chiaroscuro, urban crime" },
  { label: "Palette", value: "deep blacks, cold whites, amber accents" },
  { label: "Lighting", value: "ambient darkness, single-source dramatic light" },
  { label: "Line work", value: "heavy outlines, variable brush weight, cross-hatching" },
  { label: "Negative prompt", value: "color, bright backgrounds, soft gradients, watercolor" },
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
          <div style={{ fontWeight: 700, color: "#E2E8F0", marginBottom: 6 }}>142 / 200</div>
          <div style={{ height: 3, background: "#1E2436", borderRadius: 4 }}><div style={{ width: "71%", height: "100%", background: "#10B981", borderRadius: 4 }} /></div>
        </div>
      </div>
    </div>
  );
}

const TABS = ["Selezione", "Sfoglia libreria", "Personalizza", "Aspetto pagina", "Anteprima prompt"];

export function Stile() {
  const [tab, setTab] = useState("Sfoglia libreria");
  const [cat, setCat] = useState("Fumetto");
  const [activeStyle, setActiveStyle] = useState(1);

  const filtered = PRESETS.filter(p => p.cat === cat);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        textarea:focus,input:focus { outline:none;border-color:#F59E0B !important; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:12px;font-weight:500;padding:5px 11px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .tab-btn { padding:8px 14px;border:none;background:transparent;color:#64748B;font-size:13px;font-weight:500;cursor:pointer;border-bottom:2px solid transparent;font-family:'Inter',sans-serif;white-space:nowrap; }
        .tab-btn.active { color:#F59E0B;border-bottom-color:#F59E0B; }
        .cat-chip { padding:5px 12px;border-radius:20px;font-size:12px;font-weight:500;cursor:pointer;border:1px solid #2D3748;background:transparent;color:#64748B;font-family:'Inter',sans-serif; }
        .cat-chip.active { background:#F59E0B;border-color:#F59E0B;color:#0D1017; }
      `}</style>

      <Sidebar />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Header */}
        <div style={{ padding: "1.5rem 2rem 0", borderBottom: "1px solid #1E2436" }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0 0 .25rem", letterSpacing: "-0.02em" }}>Stile visivo</h1>
          <p style={{ fontSize: 13, color: "#64748B", margin: "0 0 1rem" }}>Progetto: La notte del riccio</p>
          <div style={{ display: "flex", gap: 0, overflowX: "auto" }}>
            {TABS.map(t => (
              <button key={t} className={`tab-btn${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>{t}</button>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, padding: "1.5rem 2rem", overflowY: "auto" }}>

          {/* TAB 1 — Selezione */}
          {tab === "Selezione" && (
            <div style={{ maxWidth: 700 }}>
              <div style={{ background: "#161B26", border: "2px solid #F59E0B", borderRadius: 10, padding: "1.5rem", display: "flex", gap: "1.5rem" }}>
                <div style={{ width: 130, aspectRatio: "2/3", background: "linear-gradient(135deg,#1a1a2e,#0d1b2a)", borderRadius: 6, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 36 }}>🖤</div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, fontSize: 20, color: "#F1F5F9" }}>Heavy Ink Noir</span>
                    <span style={{ background: "rgba(245,158,11,.15)", color: "#F59E0B", fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 4 }}>ATTIVO</span>
                  </div>
                  <span style={{ fontSize: 12, color: "#7C3AED", fontWeight: 600, background: "rgba(124,58,237,.12)", padding: "2px 10px", borderRadius: 4 }}>Fumetto</span>
                  <p style={{ fontSize: 13, color: "#94A3B8", lineHeight: 1.65, margin: "12px 0" }}>Deep ambient black inks, heavy chiaroscuro, dramatic shadows. Urban crime aesthetic with mid-century European noir influence. No color, no gradients.</p>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="btn" onClick={() => setTab("Sfoglia libreria")}>Sfoglia libreria</button>
                    <button className="btn" onClick={() => setTab("Personalizza")}>✏️ Personalizza</button>
                  </div>
                </div>
              </div>
              <div style={{ marginTop: "1rem", padding: "0.75rem 1rem", background: "rgba(245,158,11,.06)", border: "1px solid rgba(245,158,11,.15)", borderRadius: 6, fontSize: 12, color: "#94A3B8" }}>
                ⚠️ Le vignette già generate restano. Per applicare il nuovo stile, rigenerale su <strong style={{ color: "#F59E0B" }}>🖼 Genera</strong>.
              </div>
            </div>
          )}

          {/* TAB 2 — Sfoglia libreria */}
          {tab === "Sfoglia libreria" && (
            <>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: "1.25rem" }}>
                {CATEGORIES.map(c => (
                  <button key={c} className={`cat-chip${c === cat ? " active" : ""}`} onClick={() => setCat(c)}>{c}</button>
                ))}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem" }}>
                {(filtered.length > 0 ? filtered : PRESETS.slice(0, 2)).map(p => (
                  <div key={p.id} style={{ background: "#161B26", border: `1px solid ${p.id === activeStyle ? "#F59E0B" : "#1E2436"}`, borderRadius: 8, overflow: "hidden", cursor: "pointer" }}
                    onClick={() => setActiveStyle(p.id)}>
                    <div style={{ aspectRatio: "16/9", background: `linear-gradient(135deg,#${p.id % 2 === 0 ? "1e3a2f" : "1a1a2e"},#${p.id % 3 === 0 ? "2a1f1f" : "0d1b2a"})`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28 }}>
                      {["🖤","🦸","🔵","⚡","💀","🟡"][p.id - 1]}
                    </div>
                    <div style={{ padding: "0.75rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, fontSize: 14, color: "#F1F5F9" }}>{p.name}</span>
                        {p.id === activeStyle && <span style={{ fontSize: 9, fontWeight: 700, background: "rgba(245,158,11,.2)", color: "#F59E0B", padding: "2px 6px", borderRadius: 3 }}>ATTIVO</span>}
                      </div>
                      <p style={{ fontSize: 12, color: "#64748B", lineHeight: 1.5, margin: "0 0 10px", overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>{p.desc}</p>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button className="btn" style={{ flex: 1, fontSize: 11 }}>👁 Anteprima</button>
                        <button className="btn-primary" style={{ flex: 1, fontSize: 11 }}>✨ Applica</button>
                      </div>
                    </div>
                  </div>
                ))}
                {cat !== "Fumetto" && filtered.length === 0 && (
                  <div style={{ gridColumn: "1/-1", textAlign: "center", padding: "3rem", color: "#475569" }}>
                    <div style={{ fontSize: 40, marginBottom: 12 }}>🎨</div>
                    <div style={{ fontSize: 14, fontWeight: 500 }}>Nessuno stile in questa categoria.</div>
                    {cat === "I miei stili" && <div style={{ fontSize: 12, marginTop: 6, color: "#334155" }}>Duplica un preset libreria e personalizzalo per crearne uno tuo.</div>}
                  </div>
                )}
              </div>
            </>
          )}

          {/* TAB 3 — Personalizza */}
          {tab === "Personalizza" && (
            <div style={{ maxWidth: 680 }}>
              <div style={{ background: "rgba(124,58,237,.08)", border: "1px solid rgba(124,58,237,.2)", borderRadius: 6, padding: "10px 14px", marginBottom: "1.25rem", fontSize: 13, color: "#A78BFA" }}>
                Stai modificando una copia personalizzata di <strong>Heavy Ink Noir</strong>. Le modifiche si applicano solo al tuo progetto.
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 6, padding: "0.75rem 1rem" }}>
                  <div style={{ fontSize: 11, color: "#475569", marginBottom: 2, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".06em" }}>ID stile</div>
                  <div style={{ fontFamily: "monospace", fontSize: 12, color: "#64748B" }}>style_custom_8f3a2c1d</div>
                </div>
                {CUSTOM_FIELDS.map(f => (
                  <div key={f.label}>
                    <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "#94A3B8", textTransform: "uppercase", letterSpacing: ".06em", marginBottom: 5 }}>{f.label}</label>
                    {f.multiline
                      ? <textarea defaultValue={f.value} style={{ width: "100%", background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "9px 12px", color: "#E2E8F0", fontSize: 13, minHeight: 64 }} />
                      : <input defaultValue={f.value} style={{ width: "100%", background: "#161B26", border: "1px solid #2D3748", borderRadius: 6, padding: "9px 12px", color: "#E2E8F0", fontSize: 13 }} />
                    }
                  </div>
                ))}
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: "1.25rem" }}>
                <button className="btn">Annulla modifiche</button>
                <button className="btn-primary">💾 Salva personalizzazioni</button>
              </div>
            </div>
          )}

          {/* TAB 4 — Aspetto pagina */}
          {tab === "Aspetto pagina" && (
            <div style={{ maxWidth: 640 }}>
              {[
                {
                  label: "Sfondo pagina", fields: [
                    { name: "Colore sfondo", type: "color", value: "#FFFFFF" },
                  ]
                },
                {
                  label: "Balloon (parlato)", fields: [
                    { name: "Font", type: "select", options: ["Bangers", "Comic Sans MS", "Inter"] },
                    { name: "Dimensione testo", type: "number", value: "14" },
                    { name: "Colore testo", type: "color", value: "#000000" },
                    { name: "Colore contorno", type: "color", value: "#000000" },
                    { name: "Fondo FUMETTO", type: "color", value: "#FFFFFF" },
                    { name: "Fondo PENSIERO", type: "color", value: "#F0F4FF" },
                  ]
                },
                {
                  label: "Didascalie", fields: [
                    { name: "Font", type: "select", options: ["Inter", "Bangers", "Courier New"] },
                    { name: "Dimensione testo", type: "number", value: "12" },
                    { name: "Colore testo", type: "color", value: "#FFFFFF" },
                    { name: "Colore fondo", type: "color", value: "#000000" },
                  ]
                },
                {
                  label: "Effetti sonori (SFX)", fields: [
                    { name: "Font", type: "select", options: ["Bangers", "Impact", "Arial Black"] },
                    { name: "Dimensione testo", type: "number", value: "32" },
                    { name: "Colore testo", type: "color", value: "#FFD700" },
                    { name: "Colore contorno", type: "color", value: "#000000" },
                  ]
                },
              ].map(section => (
                <details key={section.label} open style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: 8, marginBottom: "0.65rem", overflow: "hidden" }}>
                  <summary style={{ padding: "0.85rem 1.25rem", cursor: "pointer", fontSize: 14, fontWeight: 600, color: "#CBD5E1", listStyle: "none", display: "flex", justifyContent: "space-between", userSelect: "none" }}>
                    <span>{section.label}</span><span style={{ color: "#475569" }}>▴</span>
                  </summary>
                  <div style={{ padding: "0 1.25rem 1rem", display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.65rem" }}>
                    {section.fields.map(field => (
                      <div key={field.name}>
                        <label style={{ display: "block", fontSize: 11, fontWeight: 500, color: "#64748B", marginBottom: 4 }}>{field.name}</label>
                        {field.type === "color" && (
                          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                            <input type="color" defaultValue={field.value} style={{ width: 36, height: 32, border: "1px solid #2D3748", borderRadius: 4, background: "transparent", cursor: "pointer", padding: 2 }} />
                            <input defaultValue={field.value} style={{ flex: 1, background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "6px 10px", color: "#E2E8F0", fontSize: 12, fontFamily: "monospace" }} />
                          </div>
                        )}
                        {field.type === "select" && (
                          <select style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "7px 10px", color: "#E2E8F0", fontSize: 13 }}>
                            {field.options?.map(o => <option key={o}>{o}</option>)}
                          </select>
                        )}
                        {field.type === "number" && (
                          <input type="number" defaultValue={field.value} style={{ width: "100%", background: "#0D1017", border: "1px solid #2D3748", borderRadius: 6, padding: "7px 10px", color: "#E2E8F0", fontSize: 13 }} />
                        )}
                      </div>
                    ))}
                    {/* Mini preview */}
                    {section.label === "Balloon (parlato)" && (
                      <div style={{ gridColumn: "1/-1", background: "#0D1017", border: "1px solid #1E2436", borderRadius: 6, padding: "0.75rem", textAlign: "center" }}>
                        <span style={{ fontSize: 11, color: "#475569", display: "block", marginBottom: 6 }}>Anteprima</span>
                        <span style={{ background: "#FFFFFF", color: "#000000", border: "2px solid #000000", borderRadius: 20, padding: "6px 14px", fontSize: 14, fontWeight: 500 }}>Anteprima testo balloon</span>
                      </div>
                    )}
                  </div>
                </details>
              ))}
              <button className="btn" style={{ marginTop: "0.5rem" }}>↩️ Ripristina aspetto predefinito</button>
            </div>
          )}

          {/* TAB 5 — Anteprima prompt */}
          {tab === "Anteprima prompt" && (
            <div style={{ maxWidth: 720 }}>
              <p style={{ fontSize: 13, color: "#64748B", marginBottom: "1rem" }}>
                Ecco come verrà costruito il prompt di una vignetta tipo del tuo progetto:
              </p>
              <div style={{ background: "#0A0E17", border: "1px solid #1E2436", borderRadius: 8, overflow: "hidden", marginBottom: "1rem" }}>
                <div style={{ padding: "0.5rem 1rem", background: "#161B26", borderBottom: "1px solid #1E2436", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 11, color: "#475569", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".06em" }}>Prompt generato</span>
                  <button className="btn" style={{ fontSize: 11, padding: "3px 9px" }}>📋 Copia</button>
                </div>
                <pre style={{ margin: 0, padding: "1.25rem", fontSize: 12, color: "#94A3B8", lineHeight: 1.7, overflowX: "auto", whiteSpace: "pre-wrap" }}>{`Style: Heavy Ink Noir. Technique: digital inking, traditional pen simulation. Aesthetic: noir, chiaroscuro, urban crime. Palette: deep blacks, cold whites, amber accents. Lighting: ambient darkness, single-source dramatic light. Line work: heavy outlines, variable brush weight, cross-hatching.

Scene: Marco si affaccia dalla finestra del vecchio palazzo. Piove forte. 
Cast: Marco Riccio (uomo sui 40, barba grigia incolta, giacca di pelle marrone consumata).
Format: landscape panel, medium shot.
Camera angle: slight low angle.
Emotional tone: tense, melancholic.

[REFERENCE: Marco_Riccio_reference.png]

Negative prompt: color, bright backgrounds, soft gradients, watercolor, text, speech bubbles, asterisks, quotes.`}</pre>
              </div>
              <p style={{ fontSize: 12, color: "#475569", fontStyle: "italic" }}>
                Questo è solo a scopo di verifica. Non si salva nulla.
              </p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
