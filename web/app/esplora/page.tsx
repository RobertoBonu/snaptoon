"use client";

import { useEffect, useState } from "react";
import { SiteShell, MediaFrame } from "@/components/site";
import { apiFetch, type EsploraSectionsOut, type EsploraSection } from "@/lib/api";

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

function PersonaggiGrid({ sec }: { sec: EsploraSection }) {
  const meta = SECTION_META.personaggi;
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(auto-fill, minmax(${meta.minCol}, 1fr))`, gap: meta.gap }}>
      {sec.items.map((p) => (
        <div key={p.id} className="product-card">
          <MediaFrame src={p.image_url || ""} label={p.title} aspect={sec.aspect} rounded={0} />
          <div style={{ padding: "16px" }}>
            <div style={{ fontSize: "15px", fontWeight: 700, color: "#F1F5F9" }}>{p.title}</div>
            <div style={{ fontSize: "13px", color: "#94A3B8", marginTop: "4px" }}>{p.caption}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function CardGrid({ sec }: { sec: EsploraSection }) {
  const meta = SECTION_META[sec.key] ?? SECTION_META.copertine;
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(auto-fill, minmax(${meta.minCol}, 1fr))`, gap: meta.gap }}>
      {sec.items.map((c) => (
        <div key={c.id}>
          <div className="lift" style={{ borderRadius: 14, overflow: "hidden", border: "1px solid #1E2436" }}>
            <MediaFrame src={c.image_url || ""} label={c.title} aspect={sec.aspect} rounded={0} />
          </div>
          <p style={{ fontSize: "13px", color: "#94A3B8", marginTop: "10px" }}>{c.caption}</p>
        </div>
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
            return sec ? <CardGrid sec={sec} /> : null;
          })()}
        </div>
      </section>

      {/* Tavole */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "60px", background: "#0A0E17", borderTop: "1px solid #1E2436", borderBottom: "1px solid #1E2436" }}>
        <div className="lp-container">
          <SectionHead title={SECTION_META.tavole.heading} subtitle={SECTION_META.tavole.subtitle} />
          {(() => {
            const sec = bySection("tavole");
            return sec ? <CardGrid sec={sec} /> : null;
          })()}
        </div>
      </section>

      {/* Personaggi */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "60px" }}>
        <div className="lp-container">
          <SectionHead title={SECTION_META.personaggi.heading} subtitle={SECTION_META.personaggi.subtitle} />
          {(() => {
            const sec = bySection("personaggi");
            return sec ? <PersonaggiGrid sec={sec} /> : null;
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
