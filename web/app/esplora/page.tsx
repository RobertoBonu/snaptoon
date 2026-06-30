"use client";

import { SiteShell, MediaFrame } from "@/components/site";

const COPERTINE = [
  { label: "Cover · Avventura per bambini", caption: "Avventura per bambini · Stile Flat", img: "/images/esplora/cover-1.png" },
  { label: "Cover · Manga shonen", caption: "Manga shonen · Stile Tokyo-Mecha", img: "/images/esplora/cover-2.png" },
  { label: "Cover · Romance", caption: "Romance · Stile Acquerello", img: "/images/esplora/cover-3.png" },
  { label: "Cover · Sci-fi", caption: "Sci-fi · Stile Cyber-Neon", img: "/images/esplora/cover-4.png" },
  { label: "Cover · Horror", caption: "Horror · Stile Noir", img: "/images/esplora/cover-5.png" },
  { label: "Cover · Fantasy", caption: "Fantasy · Stile Inchiostro", img: "/images/esplora/cover-6.png" },
];

const TAVOLE = [
  { label: "Tavola · Splash + 2x2", caption: "Splash + 2x2 · Stile Noir", img: "/images/esplora/tavola-1.png" },
  { label: "Tavola · Griglia 1+2", caption: "Griglia 1+2 · Stile Disney", img: "/images/esplora/tavola-2.png" },
  { label: "Tavola · Fila singola", caption: "Fila singola · Stile Manga", img: "/images/esplora/tavola-3.png" },
  { label: "Tavola · Mosaico 3x3", caption: "Mosaico 3x3 · Stile Acquerello", img: "/images/esplora/tavola-4.png" },
];

const PERSONAGGI = [
  { name: "Mia", desc: "Eroina ribelle, 17 anni", img: "/images/esplora/char-1.png" },
  { name: "Kael", desc: "Mercenario cibernetico", img: "/images/esplora/char-2.png" },
  { name: "Nonna Rosa", desc: "Custode dei segreti", img: "/images/esplora/char-3.png" },
  { name: "Dr. Vex", desc: "Antagonista geniale", img: "/images/esplora/char-4.png" },
  { name: "Bun", desc: "Robot da compagnia", img: "/images/esplora/char-5.png" },
  { name: "Aria", desc: "Pilota stellare", img: "/images/esplora/char-6.png" },
  { name: "Otto", desc: "Detective stanco", img: "/images/esplora/char-7.png" },
  { name: "Lumi", desc: "Spirito del bosco", img: "/images/esplora/char-8.png" },
];

function SectionHead({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div style={{ marginBottom: "40px", maxWidth: "720px" }}>
      <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.02em", marginBottom: "12px" }}>{title}</h2>
      <p style={{ fontSize: "1.0625rem", color: "#94A3B8", lineHeight: 1.6 }}>{subtitle}</p>
    </div>
  );
}

export default function EsploraPage() {
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
          <SectionHead title="📕 Copertine" subtitle="Dalla scintilla narrativa alla cover finita, con titolo già integrato nell'illustrazione." />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "24px" }}>
            {COPERTINE.map((c) => (
              <div key={c.label}>
                <div className="lift" style={{ borderRadius: 14, overflow: "hidden", border: "1px solid #1E2436" }}>
                  <MediaFrame src={c.img} label={c.label} aspect="3 / 4" rounded={0} />
                </div>
                <p style={{ fontSize: "13px", color: "#94A3B8", marginTop: "10px" }}>{c.caption}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tavole */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "60px", background: "#0A0E17", borderTop: "1px solid #1E2436", borderBottom: "1px solid #1E2436" }}>
        <div className="lp-container">
          <SectionHead title="🖼 Tavole" subtitle="Vignette con balloon, scene, inquadrature e mood scelti da te. SnapToon impagina tutto." />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(440px, 1fr))", gap: "24px" }}>
            {TAVOLE.map((t) => (
              <div key={t.label}>
                <div className="lift" style={{ borderRadius: 14, overflow: "hidden", border: "1px solid #1E2436" }}>
                  <MediaFrame src={t.img} label={t.label} aspect="4 / 3" rounded={0} />
                </div>
                <p style={{ fontSize: "13px", color: "#94A3B8", marginTop: "10px" }}>{t.caption}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Personaggi */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "60px" }}>
        <div className="lp-container">
          <SectionHead title="👥 Personaggi" subtitle="Reference image coerenti in ogni vignetta. Lo stesso volto, lo stesso costume, da pagina 1 a pagina 100." />
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "20px" }}>
            {PERSONAGGI.map((p) => (
              <div key={p.name} className="product-card">
                <MediaFrame src={p.img} label={p.name} aspect="1 / 1" rounded={0} />
                <div style={{ padding: "16px" }}>
                  <div style={{ fontSize: "15px", fontWeight: 700, color: "#F1F5F9" }}>{p.name}</div>
                  <div style={{ fontSize: "13px", color: "#94A3B8", marginTop: "4px" }}>{p.desc}</div>
                </div>
              </div>
            ))}
          </div>
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
