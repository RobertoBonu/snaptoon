"use client";

import { useEffect, useState } from "react";
import { SiteShell } from "@/components/site";
import { apiFetch, type EsploraSectionsOut, type EsploraSection, type EsploraAsset } from "@/lib/api";

// Altezza fissa per tutte le immagini di Esplora: la base si sviluppa in
// proporzione (verticali strette, orizzontali larghe), immagine sempre 100%.
const ESPLORA_H = 360;

const SECTION_META: Record<string, { heading: string; subtitle: string; minCol: string; gap: string }> = {
  copertine: {
    heading: "📕 Copertine",
    subtitle: "Dalla scintilla narrativa alla cover finita, con titolo già integrato nell'illustrazione.",
    minCol: "300px",
    gap: "24px",
  },
  tavole: {
    heading: "🖼 Tavole",
    subtitle: "Vignette con balloon, scene, inquadrature e mood scelti da te. SnapToon impagina tutto.",
    minCol: "440px",
    gap: "24px",
  },
  personaggi: {
    heading: "👥 Personaggi",
    subtitle: "Reference image coerenti in ogni vignetta. Lo stesso volto, lo stesso costume, da pagina 1 a pagina 100.",
    minCol: "220px",
    gap: "20px",
  },
};

function SectionHead({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div style={{ marginBottom: "40px", maxWidth: "720px" }}>
      <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em", marginBottom: "12px" }}>{title}</h2>
      <p style={{ fontSize: "1.0625rem", color: "#94A3B8", lineHeight: 1.6 }}>{subtitle}</p>
    </div>
  );
}

function Lightbox({ src, alt, onClose }: { src: string; alt: string; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background: "rgba(3, 6, 12, 0.9)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        cursor: "zoom-out",
        animation: "esploraFade 0.15s ease-out",
      }}
    >
      <button
        onClick={onClose}
        aria-label="Chiudi"
        style={{
          position: "absolute",
          top: 20,
          right: 24,
          width: 44,
          height: 44,
          borderRadius: 999,
          border: "1px solid rgba(255,255,255,0.18)",
          background: "rgba(15,20,32,0.7)",
          color: "#F1F5F9",
          fontSize: 22,
          lineHeight: 1,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        ✕
      </button>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: "min(96vw, 1400px)",
          maxHeight: "92vh",
          width: "auto",
          height: "auto",
          objectFit: "contain",
          borderRadius: 14,
          boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
          cursor: "default",
        }}
      />
      <style>{`@keyframes esploraFade{from{opacity:0}to{opacity:1}}`}</style>
    </div>
  );
}

function EsploraCard({ item, aspect }: { item: EsploraAsset; aspect: string }) {
  // Larghezza stimata dall'aspect della sezione finché l'immagine non è caricata;
  // poi misurata dalle dimensioni naturali per mantenere l'altezza fissa uniforme.
  const [aw, ah] = aspect.split("/").map((s) => parseFloat(s.trim()));
  const estWidth = ah ? Math.round(ESPLORA_H * (aw / ah)) : ESPLORA_H;
  const [width, setWidth] = useState<number>(estWidth);
  const [ok, setOk] = useState(true);
  const [zoom, setZoom] = useState(false);

  const hasMeta =
    Boolean(item.asset_type || item.title || item.caption || item.author_name || item.author_role);

  const showImage = Boolean(item.image_url && ok);

  return (
    <div
      className="lift"
      style={{
        width,
        maxWidth: "100%",
        background: "#0F1420",
        border: "1px solid #1E2436",
        borderRadius: 20,
        padding: 12,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {showImage ? (
        <div
          onClick={() => setZoom(true)}
          style={{ position: "relative", cursor: "zoom-in", borderRadius: 12, overflow: "hidden" }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={item.image_url as string}
            alt={item.title || ""}
            onLoad={(e) => {
              const el = e.currentTarget;
              if (el.naturalHeight > 0) {
                setWidth(Math.round(ESPLORA_H * (el.naturalWidth / el.naturalHeight)));
              }
            }}
            onError={() => setOk(false)}
            style={{ height: ESPLORA_H, width: "100%", display: "block", objectFit: "cover", borderRadius: 12 }}
          />
          <span
            aria-hidden
            style={{
              position: "absolute",
              bottom: 10,
              right: 10,
              width: 34,
              height: 34,
              borderRadius: 999,
              background: "rgba(3,6,12,0.6)",
              border: "1px solid rgba(255,255,255,0.18)",
              color: "#F1F5F9",
              fontSize: 15,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            🔍
          </span>
        </div>
      ) : (
        <div
          style={{
            height: ESPLORA_H,
            width: "100%",
            borderRadius: 12,
            background: "linear-gradient(135deg, #161B26 0%, #0D1017 100%)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
            padding: 16,
            textAlign: "center",
          }}
        >
          <div style={{ width: 44, height: 44, borderRadius: 12, background: "rgba(245,158,11,0.10)", border: "1px solid #F59E0B40", display: "flex", alignItems: "center", justifyContent: "center", color: "#F59E0B", fontSize: 20 }}>▦</div>
          {item.title && <span style={{ fontSize: 12, color: "#64748B", lineHeight: 1.4, maxWidth: 220 }}>{item.title}</span>}
        </div>
      )}

      {hasMeta && (
        <div style={{ padding: "14px 6px 6px" }}>
          {item.asset_type && (
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.12em", textTransform: "uppercase", color: "#64748B", marginBottom: 8 }}>
              {item.asset_type}
            </div>
          )}
          {item.title && (
            <div style={{ fontSize: 17, fontWeight: 700, color: "#F1F5F9", lineHeight: 1.25, overflowWrap: "break-word" }}>
              {item.title}
            </div>
          )}
          {item.caption && (
            <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 6, lineHeight: 1.5 }}>{item.caption}</p>
          )}
          {(item.author_name || item.author_role) && (
            <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 10, marginTop: 12 }}>
              {item.author_name && <span style={{ fontSize: 14, color: "#94A3B8" }}>{item.author_name}</span>}
              {item.author_role && (
                <span style={{ fontSize: 12, fontWeight: 600, color: "#A78BFA", border: "1px solid rgba(139,92,246,0.5)", borderRadius: 999, padding: "2px 10px" }}>
                  {item.author_role}
                </span>
              )}
            </div>
          )}
        </div>
      )}
      {zoom && showImage && (
        <Lightbox src={item.image_url as string} alt={item.title || ""} onClose={() => setZoom(false)} />
      )}
    </div>
  );
}

function UniformGallery({ sec }: { sec: EsploraSection }) {
  const meta = SECTION_META[sec.key] ?? SECTION_META.copertine;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-start", gap: meta.gap }}>
      {sec.items.map((c) => (
        <EsploraCard key={c.id} item={c} aspect={sec.aspect} />
      ))}
    </div>
  );
}

export default function EsploraPage() {
  const [sections, setSections] = useState<EsploraSection[] | null>(null);

  useEffect(() => {
    apiFetch<EsploraSectionsOut>("/api/esplora/assets")
      .then((d) => setSections(d.sections))
      .catch(() => setSections([]));
  }, []);

  const bySection = (key: string) => sections?.find((s) => s.key === key);

  return (
    <SiteShell active="/esplora">
      {/* Hero */}
      <section className="section" style={{ paddingTop: "100px", paddingBottom: "60px", textAlign: "center" }}>
        <div className="lp-container">
          <h1 style={{ fontSize: "clamp(2.5rem, 5vw, 4rem)", fontWeight: 800, color: "#F1F5F9", lineHeight: 1.1, letterSpacing: "-0.03em", marginBottom: "20px", maxWidth: "820px", margin: "0 auto 20px auto" }}>
            Dai un&apos;occhiata a cosa si può creare
          </h1>
          <p style={{ fontSize: "1.125rem", color: "#94A3B8", lineHeight: 1.6, maxWidth: "680px", margin: "0 auto" }}>
            Copertine, tavole e personaggi nati da poche parole. Tutti generati dai nostri autori con l&apos;AI di SnapToon, in pochi minuti.
          </p>
        </div>
      </section>

      {/* Copertine */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "60px" }}>
        <div className="lp-container">
          <SectionHead title={SECTION_META.copertine.heading} subtitle={SECTION_META.copertine.subtitle} />
          {(() => {
            const sec = bySection("copertine");
            return sec ? <UniformGallery sec={sec} /> : null;
          })()}
        </div>
      </section>

      {/* Tavole */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "60px", background: "#0A0E17", borderTop: "1px solid #1E2436", borderBottom: "1px solid #1E2436" }}>
        <div className="lp-container">
          <SectionHead title={SECTION_META.tavole.heading} subtitle={SECTION_META.tavole.subtitle} />
          {(() => {
            const sec = bySection("tavole");
            return sec ? <UniformGallery sec={sec} /> : null;
          })()}
        </div>
      </section>

      {/* Personaggi */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "60px" }}>
        <div className="lp-container">
          <SectionHead title={SECTION_META.personaggi.heading} subtitle={SECTION_META.personaggi.subtitle} />
          {(() => {
            const sec = bySection("personaggi");
            return sec ? <UniformGallery sec={sec} /> : null;
          })()}
        </div>
      </section>

      {/* CTA finale */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "100px" }}>
        <div className="lp-container">
          <div style={{ textAlign: "center", background: "linear-gradient(180deg, rgba(245,158,11,0.08) 0%, rgba(13,16,23,0) 100%)", border: "1px solid #1E2436", borderTopColor: "rgba(245,158,11,0.3)", borderRadius: "24px", padding: "64px 24px" }}>
            <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.5rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "24px" }}>Pronto a creare il tuo?</h2>
            <a href="/login" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>Inizia gratis →</a>
          </div>
        </div>
      </section>
    </SiteShell>
  );
}
