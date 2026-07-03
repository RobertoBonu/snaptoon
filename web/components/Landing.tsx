"use client";

import { ArrowRight, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { SiteShell, MediaFrame } from "@/components/site";
import { apiFetch, type CreaImagesOut } from "@/lib/api";

// Firma discreta sotto ogni illustrazione (guide del sito).
function BeaDanteSignature() {
  return (
    <div
      style={{
        marginTop: 10,
        fontSize: 12,
        color: "#64748B",
        letterSpacing: "0.06em",
        textAlign: "center",
        fontStyle: "italic",
      }}
    >
      con Bea &amp; Dante — le tue guide
    </div>
  );
}

export default function Landing() {
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

  const src = (slot: string, fallback: string) =>
    overrides[slot] || fallback;

  return (
    <SiteShell active="/">
      <HeroSection src={src} />
      <AutoriSection src={src} />
      <KidsSection src={src} />
      <EsploraSection src={src} />
      <BookshopSection src={src} />
      <FinalCtaSection src={src} />
    </SiteShell>
  );
}

// ============================================================
// Hero — presenta il duo: fumetti Pro + libretti KIDS
// ============================================================

function HeroSection({
  src,
}: {
  src: (slot: string, fallback: string) => string;
}) {
  return (
    <section
      className="section"
      style={{
        position: "relative",
        overflow: "hidden",
        paddingTop: "120px",
        paddingBottom: "80px",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "-20%",
          left: "50%",
          transform: "translateX(-50%)",
          width: "80%",
          height: "80%",
          background:
            "radial-gradient(circle, rgba(245, 158, 11, 0.08) 0%, rgba(13, 16, 23, 0) 70%)",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "20%",
          right: "-10%",
          width: "40%",
          height: "60%",
          background:
            "radial-gradient(circle, rgba(124, 58, 237, 0.05) 0%, rgba(13, 16, 23, 0) 70%)",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />

      <div
        className="lp-container"
        style={{ position: "relative", zIndex: 1 }}
      >
        <div
          style={{
            textAlign: "center",
            maxWidth: "820px",
            margin: "0 auto 48px auto",
          }}
        >
          <div
            className="animate-fade-in"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              background: "rgba(245, 158, 11, 0.1)",
              border: "1px solid rgba(245, 158, 11, 0.2)",
              padding: "6px 12px",
              borderRadius: "100px",
              color: "#F59E0B",
              fontSize: "13px",
              fontWeight: 600,
              marginBottom: "24px",
            }}
          >
            <Sparkles size={14} />
            <span>Uno studio creativo. Due modi di raccontare.</span>
          </div>

          <h1
            className="animate-fade-in"
            style={{
              fontSize: "clamp(3rem, 5vw, 4.5rem)",
              fontWeight: 800,
              color: "#F1F5F9",
              lineHeight: 1.05,
              letterSpacing: "-0.03em",
              marginBottom: "24px",
              animationDelay: "0.1s",
            }}
          >
            Dall&apos;idea al fumetto,
            <br />
            in uno <span style={{ color: "#F59E0B" }}>snap.</span>
          </h1>

          <p
            className="animate-fade-in"
            style={{
              fontSize: "1.125rem",
              color: "#94A3B8",
              lineHeight: 1.6,
              marginBottom: "40px",
              animationDelay: "0.2s",
              maxWidth: "680px",
              margin: "0 auto 40px auto",
            }}
          >
            SnapToon ha due anime: la <strong>modalità Autori</strong> per
            scrittori e illustratori professionisti, e la{" "}
            <strong>modalità KIDS</strong> per bambini, genitori e
            insegnanti. Bea &amp; Dante ti guidano in entrambe.
          </p>

          <div
            className="animate-fade-in"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "16px",
              flexWrap: "wrap",
              animationDelay: "0.3s",
            }}
          >
            <a
              href="/crea"
              className="btn btn-secondary"
              style={{ padding: "14px 28px", fontSize: "15px" }}
            >
              📖 Modalità Autori
            </a>
            <a
              href="/kids"
              className="btn btn-primary"
              style={{ padding: "14px 28px", fontSize: "15px" }}
            >
              ⭐ Modalità KIDS <ArrowRight size={18} />
            </a>
          </div>
        </div>

        {/* Illustrazione hero: Bea + Dante che presentano i due prodotti */}
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          <MediaFrame
            src={src("home-hero", "/images/home/hero.png")}
            label="Bea & Dante — le due anime di SnapToon"
            aspect="16 / 9"
            rounded={20}
          />
          <BeaDanteSignature />
        </div>
      </div>
    </section>
  );
}

// ============================================================
// Autori — flow Pro
// ============================================================

function AutoriSection({
  src,
}: {
  src: (slot: string, fallback: string) => string;
}) {
  return (
    <section
      className="section"
      style={{
        background: "#0A0E17",
        borderTop: "1px solid #1E2436",
        borderBottom: "1px solid #1E2436",
      }}
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
          <span className="eyebrow">📖 Per gli Autori</span>
          <h2
            style={{
              fontSize: "clamp(2rem, 3.5vw, 2.75rem)",
              fontWeight: 800,
              color: "#F1F5F9",
              letterSpacing: "-0.02em",
              lineHeight: 1.1,
              margin: "20px 0",
            }}
          >
            Dalla scintilla alla stampa tipografica.
          </h2>
          <p
            style={{
              fontSize: "1.0625rem",
              color: "#94A3B8",
              lineHeight: 1.7,
              marginBottom: "24px",
            }}
          >
            Un sistema completo per fumetti e graphic novel professionali:
            scrittura di sceneggiatura, <strong>96 stili visivi</strong>,
            controllo fine su ogni singola vignetta, gabbia di ogni pagina,
            balloon, inquadrature e mood. Export PDF stampabile o file per
            Adobe InDesign.
          </p>
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: "0 0 32px 0",
              display: "grid",
              gap: "8px",
            }}
          >
            {[
              "Sceneggiatura assistita con Dante — modifica ogni riga",
              "96 stili: noir, franco-belga, manga, watercolor, e altri",
              "Controllo pixel-perfect di gabbia, balloon e SFX",
              "Personaggi coerenti in ogni tavola",
              "Export PDF stampabile + IDML per Adobe InDesign",
            ].map((line) => (
              <li
                key={line}
                style={{
                  fontSize: "14px",
                  color: "#CBD5E1",
                  display: "flex",
                  gap: "8px",
                  alignItems: "flex-start",
                }}
              >
                <span style={{ color: "#F59E0B", marginTop: "2px" }}>✓</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
          <a
            href="/crea"
            className="btn btn-primary"
            style={{ padding: "14px 28px", fontSize: "15px" }}
          >
            Scopri Autori <ArrowRight size={18} />
          </a>
        </div>
        <div>
          <MediaFrame
            src={src("home-autori", "/images/home/autori.png")}
            label="Dante & Bea — la scrittura professionale"
            aspect="4 / 3"
            rounded={16}
          />
          <BeaDanteSignature />
        </div>
      </div>
    </section>
  );
}

// ============================================================
// KIDS — flow semplice
// ============================================================

function KidsSection({
  src,
}: {
  src: (slot: string, fallback: string) => string;
}) {
  return (
    <section
      className="section"
      style={{
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* alone caldo per differenziare dalla section Autori */}
      <div
        style={{
          position: "absolute",
          top: "-20%",
          left: "20%",
          width: "60%",
          height: "80%",
          background:
            "radial-gradient(circle, rgba(245,158,11,0.08) 0%, rgba(13,16,23,0) 70%)",
          zIndex: 0,
          pointerEvents: "none",
        }}
      />
      <div
        className="lp-container"
        style={{
          position: "relative",
          zIndex: 1,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "48px",
          alignItems: "center",
        }}
      >
        <div style={{ order: 2 }}>
          <MediaFrame
            src={src("home-kids", "/images/home/kids.png")}
            label="Bea — divertente ed educativo"
            aspect="4 / 3"
            rounded={16}
          />
          <BeaDanteSignature />
        </div>
        <div style={{ order: 1 }}>
          <span className="eyebrow">⭐ Per Bambini, Genitori, Insegnanti</span>
          <h2
            style={{
              fontSize: "clamp(2rem, 3.5vw, 2.75rem)",
              fontWeight: 800,
              color: "#F1F5F9",
              letterSpacing: "-0.02em",
              lineHeight: 1.1,
              margin: "20px 0",
            }}
          >
            Il fumetto sei TU. In 5 minuti.
          </h2>
          <p
            style={{
              fontSize: "1.0625rem",
              color: "#94A3B8",
              lineHeight: 1.7,
              marginBottom: "24px",
            }}
          >
            Un sistema <strong>divertente ed educativo</strong> per creare
            libretti illustrati in pochi minuti. Wizard semplificato in 6
            step: nessuna competenza tecnica richiesta. Perfetto per
            laboratori scolastici, regali di compleanno, o per sorprendere
            i propri figli.
          </p>
          <ul
            style={{
              listStyle: "none",
              padding: 0,
              margin: "0 0 32px 0",
              display: "grid",
              gap: "8px",
            }}
          >
            {[
              "13 stili colorati: chibi, supereroi, pixar, fiaba, acquerello",
              "Il tuo bambino può essere il protagonista (foto → disegno)",
              "Storia scritta insieme a Dante in 20 secondi",
              "Copertina in stile fumetto vero, con VOL. #01 e SFX!",
              "PDF stampabile pronto per il regalo",
            ].map((line) => (
              <li
                key={line}
                style={{
                  fontSize: "14px",
                  color: "#CBD5E1",
                  display: "flex",
                  gap: "8px",
                  alignItems: "flex-start",
                }}
              >
                <span style={{ color: "#F59E0B", marginTop: "2px" }}>✓</span>
                <span>{line}</span>
              </li>
            ))}
          </ul>
          <a
            href="/kids"
            className="btn btn-primary"
            style={{ padding: "14px 28px", fontSize: "15px" }}
          >
            Scopri KIDS <ArrowRight size={18} />
          </a>
        </div>
      </div>
    </section>
  );
}

// ============================================================
// Esplora — community
// ============================================================

function EsploraSection({
  src,
}: {
  src: (slot: string, fallback: string) => string;
}) {
  return (
    <section
      className="section"
      style={{
        background: "#0A0E17",
        borderTop: "1px solid #1E2436",
        borderBottom: "1px solid #1E2436",
      }}
    >
      <div
        className="lp-container"
        style={{ textAlign: "center", maxWidth: "980px", margin: "0 auto" }}
      >
        <span className="eyebrow">🌐 Community</span>
        <h2
          style={{
            fontSize: "clamp(1.75rem, 3vw, 2.5rem)",
            fontWeight: 800,
            color: "#F1F5F9",
            letterSpacing: "-0.02em",
            lineHeight: 1.1,
            margin: "20px 0",
          }}
        >
          Guarda le creazioni della community.
        </h2>
        <p
          style={{
            fontSize: "1.0625rem",
            color: "#94A3B8",
            lineHeight: 1.6,
            maxWidth: "680px",
            margin: "0 auto 32px auto",
          }}
        >
          Copertine, tavole e personaggi condivisi da autori e famiglie di
          tutta Italia. Un&apos;anteprima di quello che potrai creare tu.
        </p>
        <div style={{ maxWidth: "820px", margin: "0 auto 32px auto" }}>
          <MediaFrame
            src={src("home-esplora", "/images/home/esplora.png")}
            label="Bea & Dante presentano la community"
            aspect="16 / 9"
            rounded={16}
          />
          <BeaDanteSignature />
        </div>
        <a
          href="/esplora"
          className="btn btn-secondary"
          style={{ padding: "12px 24px", fontSize: "14px" }}
        >
          Vai a Esplora <ArrowRight size={16} />
        </a>
      </div>
    </section>
  );
}

// ============================================================
// Bookshop — marketplace
// ============================================================

function BookshopSection({
  src,
}: {
  src: (slot: string, fallback: string) => string;
}) {
  return (
    <section className="section">
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
          <MediaFrame
            src={src("home-bookshop", "/images/home/bookshop.png")}
            label="Dante — il tuo posto in libreria"
            aspect="4 / 3"
            rounded={16}
          />
          <BeaDanteSignature />
        </div>
        <div>
          <span className="eyebrow">📚 BookShop</span>
          <h2
            style={{
              fontSize: "clamp(1.75rem, 3vw, 2.5rem)",
              fontWeight: 800,
              color: "#F1F5F9",
              letterSpacing: "-0.02em",
              lineHeight: 1.1,
              margin: "20px 0",
            }}
          >
            Il tuo fumetto in libreria.
          </h2>
          <p
            style={{
              fontSize: "1.0625rem",
              color: "#94A3B8",
              lineHeight: 1.7,
              marginBottom: "16px",
            }}
          >
            Pubblica i tuoi fumetti nel BookShop di SnapToon: scegli tu se
            renderli <strong>gratuiti</strong> o metterli in{" "}
            <strong>vendita</strong>. Altri autori e famiglie potranno
            scoprirli, leggerli, sostenerli.
          </p>
          <p
            style={{
              fontSize: "14px",
              color: "#F59E0B",
              fontStyle: "italic",
              marginBottom: "24px",
            }}
          >
            🚀 Funzionalità in arrivo — prenota il tuo posto.
          </p>
          <a
            href="/bookshop"
            className="btn btn-secondary"
            style={{ padding: "12px 24px", fontSize: "14px" }}
          >
            Scopri BookShop <ArrowRight size={16} />
          </a>
        </div>
      </div>
    </section>
  );
}

// ============================================================
// CTA finale — piani + prova gratis
// ============================================================

function FinalCtaSection({
  src,
}: {
  src: (slot: string, fallback: string) => string;
}) {
  return (
    <section
      className="section"
      style={{
        background:
          "linear-gradient(180deg, rgba(245,158,11,0.06) 0%, rgba(13,16,23,0) 100%)",
        borderTop: "1px solid rgba(245,158,11,0.2)",
      }}
    >
      <div
        className="lp-container"
        style={{ textAlign: "center", maxWidth: "820px", margin: "0 auto" }}
      >
        <div style={{ maxWidth: "540px", margin: "0 auto 32px auto" }}>
          <MediaFrame
            src={src("home-cta", "/images/home/cta.png")}
            label="Bea & Dante — Iniziamo?"
            aspect="4 / 3"
            rounded={16}
          />
          <BeaDanteSignature />
        </div>
        <h2
          style={{
            fontSize: "clamp(1.75rem, 3vw, 2.75rem)",
            fontWeight: 800,
            color: "#F1F5F9",
            letterSpacing: "-0.02em",
            lineHeight: 1.1,
            margin: "16px 0",
          }}
        >
          Pronto a raccontare la tua storia?
        </h2>
        <p
          style={{
            fontSize: "1.0625rem",
            color: "#94A3B8",
            lineHeight: 1.6,
            marginBottom: "32px",
            maxWidth: "560px",
            margin: "0 auto 32px auto",
          }}
        >
          Provala gratis. 30 crediti di prova, nessuna carta richiesta.
          Passa a un piano quando vuoi.
        </p>
        <div
          style={{
            display: "flex",
            gap: "16px",
            justifyContent: "center",
            flexWrap: "wrap",
          }}
        >
          <a
            href="/login"
            className="btn btn-primary"
            style={{ padding: "14px 28px", fontSize: "15px" }}
          >
            Inizia gratis <ArrowRight size={18} />
          </a>
          <a
            href="/abbonamenti"
            className="btn btn-secondary"
            style={{ padding: "14px 28px", fontSize: "15px" }}
          >
            Vedi tutti i piani
          </a>
        </div>
      </div>
    </section>
  );
}
