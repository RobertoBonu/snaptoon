"use client";

import { ReactNode } from "react";

/** Voci del menu pubblico — collegate alle pagine reali. */
export const NAV: { label: string; href: string }[] = [
  { label: "Esplora", href: "/esplora" },
  { label: "Autori", href: "/crea" },
  { label: "Kids", href: "/kids" },
  { label: "BookShop", href: "/bookshop" },
  { label: "Abbonamenti", href: "/abbonamenti" },
];

/** Stili globali condivisi (stesso design system della landing). */
export function SiteStyles() {
  return (
    <style>{`
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
      * { box-sizing: border-box; }

      .text-primary { color: #F1F5F9; }
      .text-secondary { color: #94A3B8; }
      .text-tertiary { color: #64748B; }
      .text-amber { color: #F59E0B; }

      .btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; font-size: 14px; font-weight: 600; padding: 10px 20px; border-radius: 8px; cursor: pointer; transition: all 0.2s ease; border: none; text-decoration: none; }
      .btn-primary { background: #F59E0B; color: #0D1017; }
      .btn-primary:hover { background: #FBBF24; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2); }
      .btn-secondary { background: transparent; border: 1px solid #2D3748; color: #E2E8F0; }
      .btn-secondary:hover { background: #161B26; border-color: #475569; }
      .btn-ghost { background: transparent; color: #94A3B8; padding: 8px 16px; }
      .btn-ghost:hover { color: #F1F5F9; background: rgba(255,255,255,0.05); }

      @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
      .animate-fade-in { animation: fadeIn 0.8s ease forwards; }

      .lp-container { max-width: 1280px; margin: 0 auto; padding: 0 24px; }
      .section { padding: 100px 0; }

      .product-card { background: #161B26; border: 1px solid #1E2436; border-radius: 16px; overflow: hidden; transition: all 0.3s ease; display: flex; flex-direction: column; }
      .product-card:hover { border-color: #2D3748; transform: translateY(-4px); box-shadow: 0 12px 32px rgba(0,0,0,0.4); }

      .node-card { background: #161B26; border: 1px solid #2D3748; border-radius: 12px; padding: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 10; position: relative; width: 280px; }
      .node-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; border-bottom: 1px solid #1E2436; padding-bottom: 12px; }
      .node-port { width: 10px; height: 10px; background: #0D1017; border: 2px solid #64748B; border-radius: 50%; position: absolute; top: 50%; transform: translateY(-50%); }
      .node-port.in { left: -6px; }
      .node-port.out { right: -6px; border-color: #F59E0B; }
      .node-port.out.active { background: #F59E0B; box-shadow: 0 0 8px #F59E0B; }

      /* Generic helpers for content pages */
      .eyebrow { display: inline-flex; align-items: center; gap: 8px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); padding: 6px 12px; border-radius: 100px; color: #F59E0B; font-size: 13px; font-weight: 600; }
      .lift { transition: all 0.3s ease; }
      .lift:hover { transform: translateY(-4px); border-color: #2D3748; box-shadow: 0 12px 32px rgba(0,0,0,0.4); }
      .link-amber { color: #94A3B8; text-decoration: none; transition: color 0.2s; }
      .link-amber:hover { color: #F59E0B; }

      .md-flex { display: none; }
      @media (min-width: 768px) { .md-flex { display: flex !important; } }

      .footer-grid { display: grid; grid-template-columns: 1fr; gap: 40px; }
      @media (min-width: 640px) { .footer-grid { grid-template-columns: 1fr 1fr; } }
      @media (min-width: 960px) { .footer-grid { grid-template-columns: 2fr 1fr 1fr 1fr; gap: 64px; } }
    `}</style>
  );
}

/** Logo SnapToon con pallino viola. */
function Logo() {
  return (
    <a href="/" style={{ display: "flex", alignItems: "center", textDecoration: "none" }}>
      <span style={{ fontSize: "1.5rem", fontWeight: 800, color: "#F59E0B", letterSpacing: "-0.02em" }}>SnapToon</span>
      <span style={{ display: "inline-block", width: 8, height: 8, background: "#7C3AED", borderRadius: "50%", marginLeft: 4, marginBottom: 6 }} />
    </a>
  );
}

/** Header sticky con menu collegato alle 4 pagine pubbliche. */
export function SiteHeader({ active }: { active?: string }) {
  return (
    <header style={{ position: "sticky", top: 0, zIndex: 100, background: "rgba(13, 16, 23, 0.85)", backdropFilter: "blur(12px)", borderBottom: "1px solid #1E2436" }}>
      <div className="lp-container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: "72px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "48px" }}>
          <Logo />
          <nav style={{ alignItems: "center", gap: "8px" }} className="md-flex">
            {NAV.map((item) => {
              const isActive = active === item.href;
              return (
                <a
                  key={item.href}
                  href={item.href}
                  style={{ fontSize: "14px", fontWeight: 500, color: isActive ? "#F1F5F9" : "#94A3B8", padding: "8px 16px", borderRadius: "6px", cursor: "pointer", transition: "color 0.2s", textDecoration: "none", background: isActive ? "rgba(255,255,255,0.05)" : "transparent" }}
                  onMouseOver={(e) => (e.currentTarget.style.color = "#F1F5F9")}
                  onMouseOut={(e) => (e.currentTarget.style.color = isActive ? "#F1F5F9" : "#94A3B8")}
                >
                  {item.label}
                </a>
              );
            })}
          </nav>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <a href="/login" className="btn btn-secondary" style={{ padding: "8px 16px" }}>Accedi</a>
          <a href="/login" className="btn btn-primary" style={{ padding: "8px 16px" }}>Prova SnapToon</a>
        </div>
      </div>
    </header>
  );
}

/** Footer condiviso. */
export function SiteFooter() {
  const cols: { title: string; links: { label: string; href: string }[] }[] = [
    {
      title: "Prodotto",
      links: [
        { label: "Esplora", href: "/esplora" },
        { label: "Autori", href: "/crea" },
        { label: "Kids", href: "/kids" },
        { label: "BookShop", href: "/bookshop" },
        { label: "Abbonamenti", href: "/abbonamenti" },
      ],
    },
    {
      title: "Risorse",
      links: [
        { label: "Documentazione", href: "#" },
        { label: "Tutorial", href: "#" },
        { label: "Community", href: "#" },
        { label: "Blog", href: "#" },
      ],
    },
    {
      title: "Azienda & Legale",
      links: [
        { label: "Chi Siamo", href: "#" },
        { label: "Contatti", href: "mailto:info@snaptoon.art" },
        { label: "Privacy Policy", href: "#" },
        { label: "Termini di Servizio", href: "#" },
      ],
    },
  ];

  return (
    <footer style={{ background: "#0A0E17", borderTop: "1px solid #1E2436", paddingTop: "80px", paddingBottom: "40px" }}>
      <div className="lp-container">
        <div className="footer-grid" style={{ marginBottom: "64px" }}>
          <div>
            <div style={{ marginBottom: "16px" }}><Logo /></div>
            <p style={{ fontSize: "14px", color: "#64748B", maxWidth: "300px", lineHeight: 1.6 }}>
              L&apos;AI studio per creatori di fumetti. Trasforma le tue storie in tavole illustrate professionali con il pieno controllo artistico.
            </p>
          </div>
          {cols.map((col) => (
            <div key={col.title}>
              <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#F1F5F9", marginBottom: "20px" }}>{col.title}</h4>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "12px" }}>
                {col.links.map((link) => (
                  <li key={link.label}><a href={link.href} className="link-amber" style={{ fontSize: "14px" }}>{link.label}</a></li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div style={{ borderTop: "1px solid #1E2436", paddingTop: "32px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ fontSize: "13px", color: "#64748B" }}>© SnapToon | New Star System SRL © 2026.</div>
          <div style={{ fontSize: "13px", color: "#64748B" }}>Attitudine umana - Passione italiana.</div>
        </div>
      </div>
    </footer>
  );
}

/** Wrapper di pagina: sfondo, font, stili, header e footer. */
export function SiteShell({ children, active }: { children: ReactNode; active?: string }) {
  return (
    <div style={{ backgroundColor: "#0D1017", minHeight: "100vh", fontFamily: "'Inter', sans-serif", color: "#E2E8F0", overflowX: "hidden" }}>
      <SiteStyles />
      <SiteHeader active={active} />
      <main>{children}</main>
      <SiteFooter />
    </div>
  );
}

/**
 * Cornice immagine con placeholder elegante.
 * Mostra un segnaposto (gradiente + etichetta); se l'immagine reale esiste in
 * `web/public/images/...` la copre automaticamente. onError nasconde l'img mancante.
 */
export function MediaFrame({
  src,
  alt,
  label,
  aspect = "4 / 3",
  rounded = 12,
  accent = "#F59E0B",
}: {
  src: string;
  alt?: string;
  label?: string;
  aspect?: string;
  rounded?: number;
  accent?: string;
}) {
  return (
    <div style={{ position: "relative", aspectRatio: aspect, borderRadius: rounded, overflow: "hidden", background: "linear-gradient(135deg, #161B26 0%, #0D1017 100%)", border: "1px solid #1E2436" }}>
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 10, padding: 16, textAlign: "center" }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: "rgba(245,158,11,0.10)", border: `1px solid ${accent}40`, display: "flex", alignItems: "center", justifyContent: "center", color: accent, fontSize: 20 }}>▦</div>
        {label && <span style={{ fontSize: 12, color: "#64748B", lineHeight: 1.4, maxWidth: 220 }}>{label}</span>}
      </div>
      {src ? (
        // key={src}: rimonta un <img> pulito ad ogni cambio di src. Senza questo,
        // il fallback statico (404) imposta display:none imperativo che PERSISTE
        // anche quando src passa all'URL immagine reale — l'immagine caricava (200)
        // ma restava invisibile. Race visibile solo in produzione (rete più lenta).
        <img
          key={src}
          src={src}
          alt={alt || ""}
          style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
      ) : null}
    </div>
  );
}
