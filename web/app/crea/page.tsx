"use client";

import { useEffect, useState } from "react";
import { SiteShell, MediaFrame } from "@/components/site";
import { apiFetch, type CreaImagesOut } from "@/lib/api";

const STEPS = [
  {
    slot: "step-testo",
    heading: "1. 📝 Testo — Scrivi la scintilla",
    body: "Incolla un soggetto, un racconto breve o anche solo un'idea di poche righe. Claude la trasforma in sceneggiatura strutturata: logline, personaggi, pagine, vignette, dialoghi. Tu approvi o rigeneri con un suggerimento.",
    highlight: "Costa 5 crediti per generazione + rigenerazioni con feedback",
    img: "/images/crea/step-testo.png",
    label: "Pagina /testo · script generato",
  },
  {
    slot: "step-stile",
    heading: "2. 🎨 Stile — Scegli il look",
    body: "98 stili visivi pronti: dal flat illustrato per bambini al noir cinematografico, dal manga giapponese al fumetto franco-belga. Filtra per categoria, scegli e procedi.",
    highlight: "Lo stile è applicato automaticamente a tutte le vignette del progetto",
    img: "/images/crea/step-stile.png",
    label: "Griglia stili",
  },
  {
    slot: "step-personaggi",
    heading: "3. 👥 Personaggi — Il tuo cast",
    body: "Crea i personaggi della storia con nome e descrizione visiva. SnapToon genera una reference image AI per ognuno e la riutilizza in ogni vignetta successiva. Il volto di Mia rimane Mia, sempre.",
    highlight: "1 credito per reference. Rigenera quanto vuoi finché non sei soddisfatto",
    img: "/images/crea/step-personaggi.png",
    label: "Card personaggio · reference image",
  },
  {
    slot: "step-genera",
    heading: "4. 🖼 Genera — Componi le vignette",
    body: "Per ogni vignetta decidi inquadratura (dal close-up al campo lungo), angolo (dal cinematic basso al volo d'uccello), mood (dall'azione drammatica al lirico) e formato (quadrato, verticale o panoramico). I balloon sono disegnati direttamente nell'immagine dall'AI, leggibili e coerenti con lo stile.",
    highlight: "1 credito a vignetta (qualità Medium). Quality High disponibile su Premium",
    img: "/images/crea/step-genera.png",
    label: "Pagina /genera · scene selector",
  },
  {
    slot: "step-impagina",
    heading: "5. 📐 Impagina — La pagina finita",
    body: "Scegli la griglia per ogni pagina: splash, 2x2, 1+2, fila singola. Le vignette si dispongono automaticamente. Esporta in PDF stampabile.",
    highlight: "Esportazione PDF inclusa in tutti i piani",
    img: "/images/crea/step-impagina.png",
    label: "Pagina completa renderizzata",
  },
];

export default function CreaPage() {
  // Override immagini gestite dall'admin: slot → URL. Se assente si usa il
  // default statico definito qui sotto (SSR-safe: parte dai default).
  const [overrides, setOverrides] = useState<Record<string, string>>({});

  useEffect(() => {
    apiFetch<CreaImagesOut>("/api/crea/images", { cache: "no-store" })
      .then((d) => {
        const map: Record<string, string> = {};
        for (const it of d.images) {
          if (it.image_url) map[it.slot] = it.image_url;
        }
        setOverrides(map);
      })
      .catch(() => {
        /* fallback ai default statici */
      });
  }, []);

  const srcFor = (slot: string, fallback: string) => overrides[slot] || fallback;

  return (
    <SiteShell active="/crea">
      {/* Hero */}
      <section className="section" style={{ paddingTop: "100px", paddingBottom: "60px" }}>
        <div className="lp-container" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "48px", alignItems: "center" }}>
          <div>
            <span className="eyebrow">Workflow Pro</span>
            <h1 style={{ fontSize: "clamp(2.25rem, 4vw, 3.25rem)", fontWeight: 800, color: "#F1F5F9", lineHeight: 1.1, letterSpacing: "-0.03em", margin: "20px 0" }}>
              5 passi. Dal foglio bianco al fumetto stampabile.
            </h1>
            <p style={{ fontSize: "1.125rem", color: "#94A3B8", lineHeight: 1.6, marginBottom: "32px" }}>
              SnapToon ti accompagna passo passo. Tu scrivi l&apos;idea, l&apos;AI fa il resto — sempre sotto il tuo controllo.
            </p>
            <a href="/login" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>Inizia gratis →</a>
          </div>
          <MediaFrame src={srcFor("dashboard", "/images/crea/dashboard.png")} label="Dashboard · I miei progetti" aspect="4 / 3" rounded={16} />
        </div>
      </section>

      {/* Steps */}
      <section style={{ paddingBottom: "40px" }}>
        <div className="lp-container" style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
          {STEPS.map((step, i) => {
            const reverse = i % 2 === 1;
            return (
              <div key={step.heading} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "40px", alignItems: "center", background: "#0A0E17", border: "1px solid #1E2436", borderRadius: "20px", padding: "40px" }}>
                <div style={{ order: reverse ? 2 : 1 }}>
                  <h2 style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em", marginBottom: "16px" }}>{step.heading}</h2>
                  <p style={{ fontSize: "1.0625rem", color: "#94A3B8", lineHeight: 1.7, marginBottom: "20px" }}>{step.body}</p>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.2)", color: "#F59E0B", fontSize: "13px", fontWeight: 600, padding: "8px 14px", borderRadius: "8px" }}>
                    💡 {step.highlight}
                  </div>
                </div>
                <div style={{ order: reverse ? 1 : 2 }}>
                  <MediaFrame src={srcFor(step.slot, step.img)} label={step.label} aspect="4 / 3" rounded={14} />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Callout KIDS */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "60px" }}>
        <div className="lp-container">
          <div style={{ background: "linear-gradient(135deg, rgba(245,158,11,0.12) 0%, rgba(124,58,237,0.08) 100%)", border: "1px solid rgba(245,158,11,0.3)", borderRadius: "20px", padding: "40px" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#F1F5F9", marginBottom: "12px" }}>Vuoi creare un libretto per bambini? Prova la modalità ⭐ KIDS</h2>
            <p style={{ fontSize: "1.0625rem", color: "#CBD5E1", lineHeight: 1.7, marginBottom: "24px", maxWidth: "760px" }}>
              Wizard semplificato in 6 step. Template pre-fissati. Storia, copertina e illustrazioni generate in 3 minuti. Perfetto per genitori, insegnanti, biblioteche.
            </p>
            <a href="/esplora" className="btn btn-secondary" style={{ padding: "12px 22px" }}>Scopri KIDS →</a>
          </div>
        </div>
      </section>

      {/* CTA finale */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "100px" }}>
        <div className="lp-container" style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.5rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "24px" }}>Bastano 5 minuti per la tua prima tavola.</h2>
          <a href="/login" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>Inizia gratis →</a>
        </div>
      </section>
    </SiteShell>
  );
}
