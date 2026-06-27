import { useState } from "react";

const STEPS = [
  {
    emoji: "✍️",
    title: "Dal testo al fumetto",
    desc: "Carica il tuo racconto, copione o soggetto. SnapToon lo legge e genera automaticamente la sceneggiatura, divisa in pagine e vignette.",
  },
  {
    emoji: "🎨",
    title: "Stile e personaggi",
    desc: "Scegli fra 98 preset visivi — da Heavy Ink Noir a Kids Pastel. Poi crea le reference dei personaggi: un'immagine per ognuno per garantire coerenza.",
  },
  {
    emoji: "🖼",
    title: "Genera e impagina",
    desc: "Genera ogni vignetta con un clic. Scegli la gabbia, posiziona i balloon e esporta il fumetto finito in PDF pronto per la stampa.",
  },
];

export function Onboarding() {
  const [step, setStep] = useState(0);
  const s = STEPS[step];

  return (
    <div style={{ minHeight: "100vh", background: "#0D1017", fontFamily: "'Inter',sans-serif", color: "#E2E8F0", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        .btn { border:1px solid #2D3748;background:transparent;color:#CBD5E1;font-size:14px;font-weight:500;padding:10px 22px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn:hover { background:#1E2436; }
        .btn-primary { background:#F59E0B;border:none;color:#0D1017;font-size:14px;font-weight:600;padding:10px 22px;border-radius:6px;cursor:pointer;font-family:'Inter',sans-serif; }
        .btn-primary:hover { background:#FBBF24; }
        .btn:disabled { opacity:.35;cursor:default; }
      `}</style>

      {/* Background overlay */}
      <div style={{ position: "fixed", inset: 0, background: "rgba(13,16,23,.7)", backdropFilter: "blur(2px)" }} />

      {/* Card */}
      <div style={{ position: "relative", width: 600, background: "#161B26", border: "1px solid #2D3748", borderRadius: 16, padding: "2.5rem 2.5rem 2rem", boxShadow: "0 32px 80px rgba(0,0,0,.7)" }}>
        {/* Step dots */}
        <div style={{ display: "flex", gap: 8, justifyContent: "center", marginBottom: "2rem" }}>
          {STEPS.map((_, i) => (
            <div key={i} style={{ width: i === step ? 24 : 8, height: 8, borderRadius: 4, background: i === step ? "#F59E0B" : "#2D3748", transition: "width .2s, background .2s" }} />
          ))}
        </div>

        {/* Step counter */}
        <div style={{ textAlign: "center", fontSize: 11, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: "1.25rem" }}>
          Passo {step + 1} di {STEPS.length}
        </div>

        {/* Illustration */}
        <div style={{ height: 140, background: "#0D1017", border: "1px solid #1E2436", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "1.5rem" }}>
          <span style={{ fontSize: 72, filter: "drop-shadow(0 4px 24px rgba(245,158,11,.3))" }}>{s.emoji}</span>
        </div>

        {/* Content */}
        <h2 style={{ fontSize: "1.4rem", fontWeight: 700, color: "#F1F5F9", textAlign: "center", margin: "0 0 .75rem", letterSpacing: "-0.02em" }}>{s.title}</h2>
        <p style={{ fontSize: 15, color: "#94A3B8", textAlign: "center", lineHeight: 1.65, margin: "0 0 2rem" }}>{s.desc}</p>

        {/* Buttons */}
        <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
          <button className="btn" disabled={step === 0} onClick={() => setStep(s => s - 1)}>← Indietro</button>
          {step < STEPS.length - 1
            ? <button className="btn-primary" onClick={() => setStep(s => s + 1)}>Continua →</button>
            : <button className="btn-primary">🚀 Inizia con un progetto demo</button>
          }
        </div>

        {/* Skip */}
        <div style={{ textAlign: "center", marginTop: "1.25rem" }}>
          <span style={{ fontSize: 12, color: "#475569", cursor: "pointer", textDecoration: "underline" }}>Salta tutorial</span>
        </div>
      </div>
    </div>
  );
}
