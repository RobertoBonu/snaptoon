"use client";

import { useEffect, useState } from "react";
import { SiteShell, MediaFrame } from "@/components/site";
import { apiFetch, type CreaImagesOut } from "@/lib/api";

// 6 sezioni con testi pensati per bambini + genitori. Stessa struttura visiva
// della pagina /crea (Autori), ma con toni giocosi e focus sul flusso KIDS.
//
// Le immagini di default (img) sono percorsi statici sotto /public/images/kids.
// L'admin potrà in futuro sovrascriverle tramite l'endpoint /api/kids-showcase
// (usa lo stesso pattern di /api/crea/images); finché non esiste, si vedono
// solo i placeholder di MediaFrame quando il file statico manca.
const KIDS_STEPS = [
  {
    slot: "kids-step-1",
    heading: "1. 🎨 Il tuo stile",
    body: "Prima cosa: scegli come sarà disegnato il tuo libretto. Chibi tenerissimi, super eroi coraggiosi, principesse fatate, cartoni 3D stile Pixar, acquerelli magici, oppure il tuo scarabocchio più bello. 13 stili tra cui scegliere. Ogni libretto poi pesca a caso uno dei 6 ritmi di impaginazione — nessun libretto sarà mai uguale a un altro.",
    highlight: "Ogni libretto è unico. Come te.",
    img: "/images/kids/step-1-stile.png",
    label: "Scelta stile + ritmo",
  },
  {
    slot: "kids-step-2",
    heading: "2. 📖 La scintilla",
    body: (
      <>
        Racconta la tua scintilla: &quot;Un bambino trova un drago timido nel
        giardino&quot;, oppure &quot;La nonna insegna al gatto a fare le
        crêpes&quot;. <strong>Bea</strong>, la nostra Autrice-illustratrice,
        la trasforma in una storia vera con titolo, sceneggiatura, dialoghi
        e un finale a sorpresa che fa ridere. Poi la puoi rileggere,
        cambiare, riscrivere — è tutta tua.
      </>
    ),
    highlight: "Anche tu diventi un vero scrittore. In 20 secondi.",
    img: "/images/kids/step-2-storia.png",
    label: "Titolo + storia",
  },
  {
    slot: "kids-step-3",
    heading: "3. 👤 I personaggi",
    body: "Il protagonista sei tu, o tuo figlio, o la nonna, o il gatto Milu. Carica una foto vera del soggetto — la cancelliamo subito dopo averla usata per generare il ritratto AI, quindi la foto originale non resta da nessuna parte. Oppure descrivilo a parole. In più, ogni personaggio finisce nel tuo archivio \"I miei personaggi\": la nonna la riusi anche nel libretto successivo, non serve rifarla ogni volta.",
    highlight: "Privacy prima di tutto. E archivio riusabile per sempre.",
    img: "/images/kids/step-3-personaggi.png",
    label: "Personaggi + reference",
  },
  {
    slot: "kids-step-4",
    heading: "4. 📕 La copertina",
    body: "La copertina fa il libretto. Titolo grande, autore, e — cosa più bella — i badge tipo vera copertina di fumetto: il numero del volume in alto a sinistra, il logo SNAP TOON in alto a destra, un effetto sonoro POW! o MAGIC! in basso a sinistra scelto in base alla tua storia. Genera, non ti piace? Rigenera. Nessun limite di tentativi.",
    highlight: "Sembra un vero fumetto Marvel. Ma è tuo.",
    img: "/images/kids/step-4-copertina.png",
    label: "Copertina con badge",
  },
  {
    slot: "kids-step-5",
    heading: "5. 🖼 Le vignette",
    body: "Ora la magia. L'AI disegna ogni vignetta — i personaggi restano identici da inizio a fine, i dialoghi vanno nei balloon, l'azione si muove tra le pagine. Una vignetta non ti piace? Passi il mouse sopra e appare il bottone \"🔄 Rigenera\": un click e ne ottieni una nuova. Vale 1 credito. Puoi farlo tutte le volte che vuoi.",
    highlight: "Se non ti piace, rifallo. È come cambiare libretto senza cambiare libretto.",
    img: "/images/kids/step-5-vignette.png",
    label: "Griglia vignette",
  },
  {
    slot: "kids-step-6",
    heading: "6. 📐 Il libretto è pronto",
    body: "Ultima magia: PDF pronto per la stampa. Copertina, tavole interne, quarta di copertina in stile fumetto vero con la miniatura della cover, autore e copyright. Scaricalo, portalo dal cartolibraio, regalalo alla nonna. E se il libretto è venuto bene? Condividilo con la community: un moderatore lo approva e finisce nella pagina Esplora, così altri bimbi possono vederlo.",
    highlight: "PDF stampabile in un click. Community pronta ad applaudire.",
    img: "/images/kids/step-6-pdf.png",
    label: "PDF + community",
  },
];

export default function KidsShowcasePage() {
  // Come per /crea: consenti override immagini dall'admin. L'endpoint
  // /api/crea/images restituisce SIA gli slot Autori sia i "kids-*"
  // (gestiti in /app/admin/crea con sezione dedicata). Se un slot non è
  // ancora stato caricato, ricade sul path statico sotto /public/images/kids.
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
        /* fallback statici */
      });
  }, []);

  const srcFor = (slot: string, fallback: string) =>
    overrides[slot] || fallback;

  return (
    <SiteShell active="/kids">
      {/* Hero */}
      <section
        className="section"
        style={{ paddingTop: "100px", paddingBottom: "60px" }}
      >
        <div
          className="lp-container"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
            gap: "48px",
            alignItems: "center",
          }}
        >
          <div>
            <span className="eyebrow">Per genitori, insegnanti e bambini</span>
            <h1
              style={{
                fontSize: "clamp(2.25rem, 4vw, 3.25rem)",
                fontWeight: 800,
                color: "#F1F5F9",
                lineHeight: 1.1,
                letterSpacing: "-0.03em",
                margin: "20px 0",
              }}
            >
              Il fumetto sei TU. In 5 minuti.
            </h1>
            <p
              style={{
                fontSize: "1.125rem",
                color: "#94A3B8",
                lineHeight: 1.6,
                marginBottom: "32px",
              }}
            >
              SnapToon KIDS trasforma un&apos;idea di 10 parole nel libretto
              illustrato dei sogni. Nessuna competenza tecnica: il wizard fa
              tutto in 6 passaggi. Perfetto per sorprendere tuo figlio,
              organizzare un laboratorio in classe, o creare il regalo di
              compleanno più originale della storia.
            </p>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <a
                href="/login"
                className="btn btn-primary"
                style={{ padding: "14px 28px", fontSize: "15px" }}
              >
                Prova gratis →
              </a>
              <a
                href="/esplora"
                className="btn btn-secondary"
                style={{ padding: "14px 28px", fontSize: "15px" }}
              >
                Guarda esempi
              </a>
            </div>
          </div>
          <MediaFrame
            src={srcFor("kids-hero", "/images/kids/hero.png")}
            label="Wizard KIDS · anteprima libretto"
            aspect="4 / 3"
            rounded={16}
          />
        </div>
      </section>

      {/* Steps */}
      <section style={{ paddingBottom: "40px" }}>
        <div
          className="lp-container"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "32px",
          }}
        >
          {KIDS_STEPS.map((step, i) => {
            const reverse = i % 2 === 1;
            return (
              <div
                key={step.heading}
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(340px, 1fr))",
                  gap: "40px",
                  alignItems: "center",
                  background: "#0A0E17",
                  border: "1px solid #1E2436",
                  borderRadius: "20px",
                  padding: "40px",
                }}
              >
                <div style={{ order: reverse ? 2 : 1 }}>
                  <h2
                    style={{
                      fontSize: "clamp(1.5rem, 2.5vw, 2rem)",
                      fontWeight: 700,
                      color: "#F1F5F9",
                      letterSpacing: "-0.02em",
                      marginBottom: "16px",
                    }}
                  >
                    {step.heading}
                  </h2>
                  <p
                    style={{
                      fontSize: "1.0625rem",
                      color: "#94A3B8",
                      lineHeight: 1.7,
                      marginBottom: "20px",
                    }}
                  >
                    {step.body}
                  </p>
                  <div
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "8px",
                      background: "rgba(245,158,11,0.1)",
                      border: "1px solid rgba(245,158,11,0.2)",
                      color: "#F59E0B",
                      fontSize: "13px",
                      fontWeight: 600,
                      padding: "8px 14px",
                      borderRadius: "8px",
                    }}
                  >
                    ✨ {step.highlight}
                  </div>
                </div>
                <div style={{ order: reverse ? 1 : 2 }}>
                  <MediaFrame
                    src={srcFor(step.slot, step.img)}
                    label={step.label}
                    aspect="4 / 3"
                    rounded={14}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Callout Autori */}
      <section
        className="section"
        style={{ paddingTop: "40px", paddingBottom: "60px" }}
      >
        <div className="lp-container">
          <div
            style={{
              background:
                "linear-gradient(135deg, rgba(124,58,237,0.10) 0%, rgba(245,158,11,0.08) 100%)",
              border: "1px solid rgba(124,58,237,0.3)",
              borderRadius: "20px",
              padding: "40px",
            }}
          >
            <h2
              style={{
                fontSize: "1.5rem",
                fontWeight: 700,
                color: "#F1F5F9",
                marginBottom: "12px",
              }}
            >
              Sei uno sceneggiatore o illustratore? Scopri la modalità Autori
            </h2>
            <p
              style={{
                fontSize: "1.0625rem",
                color: "#CBD5E1",
                lineHeight: 1.7,
                marginBottom: "24px",
                maxWidth: "760px",
              }}
            >
              Progetti lunghi, controllo fine su gabbia di ogni pagina, 98
              stili visivi tra cui scegliere, dal noir al franco-belga.
              L&apos;editor completo per graphic novel professionali.
            </p>
            <a
              href="/crea"
              className="btn btn-secondary"
              style={{ padding: "12px 22px" }}
            >
              Scopri l&apos;area Autori →
            </a>
          </div>
        </div>
      </section>

      {/* CTA finale */}
      <section
        className="section"
        style={{ paddingTop: "20px", paddingBottom: "100px" }}
      >
        <div className="lp-container" style={{ textAlign: "center" }}>
          <h2
            style={{
              fontSize: "clamp(1.75rem, 3vw, 2.5rem)",
              fontWeight: 800,
              color: "#F1F5F9",
              marginBottom: "24px",
            }}
          >
            Prova a raccontare la scintilla. Il libretto arriva da solo.
          </h2>
          <a
            href="/login"
            className="btn btn-primary"
            style={{ padding: "14px 28px", fontSize: "15px" }}
          >
            Inizia gratis →
          </a>
        </div>
      </section>
    </SiteShell>
  );
}
