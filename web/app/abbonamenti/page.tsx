"use client";

import { useState } from "react";
import { SiteShell } from "@/components/site";

interface Feature { text: string; ok: boolean }
interface Plan {
  id: string;
  emoji: string;
  name: string;
  price: string;
  tagline: string;
  popular?: boolean;
  features: Feature[];
  cta: string;
  href: string;
  free?: boolean;
}

const PLANS: Plan[] = [
  {
    id: "free_to_play", emoji: "🎁", name: "Free-To-Play", price: "GRATIS",
    tagline: "Prova SnapToon, senza carta di credito",
    free: true,
    features: [
      { text: "1 libretto Striscia (1 tavola)", ok: true },
      { text: "1 figurina collezionabile", ok: true },
      { text: "1 cover standalone", ok: true },
      { text: "Qualità Media", ok: true },
      { text: "Libretti Brevi / Lunghi", ok: false },
      { text: "Modalità Pro", ok: false },
      { text: "BookShop", ok: false },
    ],
    cta: "Registrati gratis →",
    href: "/register?plan=free_to_play",
  },
  {
    id: "base", emoji: "🎨", name: "Base", price: "€19", tagline: "Per autori indie e hobbisti", popular: true,
    features: [
      { text: "200 crediti/mese", ok: true },
      { text: "5 progetti", ok: true },
      { text: "Modalità Pro completa", ok: true },
      { text: "Modalità KIDS inclusa", ok: true },
      { text: "98 stili visivi", ok: true },
      { text: "Qualità Low + Medium", ok: true },
      { text: "Export PDF stampabile", ok: true },
      { text: "Qualità High", ok: false },
      { text: "BookShop", ok: false },
    ],
    cta: "Scegli Base →",
    href: "/register?plan=base",
  },
  {
    id: "premium", emoji: "🚀", name: "Premium", price: "€49", tagline: "Per autori prolifici",
    features: [
      { text: "600 crediti/mese", ok: true },
      { text: "Progetti illimitati", ok: true },
      { text: "Tutto di Base, più:", ok: true },
      { text: "Qualità High (4 cr/immagine)", ok: true },
      { text: "Reference image avanzate", ok: true },
      { text: "Stili custom su richiesta", ok: true },
      { text: "Supporto prioritario", ok: true },
      { text: "BookShop", ok: false },
    ],
    cta: "Scegli Premium →",
    href: "/register?plan=premium",
  },
];

const TABLE: { feature: string; values: string[] }[] = [
  { feature: "Crediti/mese", values: ["1 striscia + 1 fig. + 1 cover", "200", "600"] },
  { feature: "Progetti", values: ["1", "5", "Illimitati"] },
  { feature: "Modalità KIDS Striscia", values: ["✅", "✅", "✅"] },
  { feature: "Modalità KIDS Breve/Lungo", values: ["❌", "✅", "✅"] },
  { feature: "Modalità Pro", values: ["❌", "✅", "✅"] },
  { feature: "Stili", values: ["6 base", "98", "98 + custom"] },
  { feature: "Qualità Low", values: ["—", "✅", "✅"] },
  { feature: "Qualità Medium", values: ["✅", "✅", "✅"] },
  { feature: "Qualità High", values: ["❌", "❌", "✅"] },
  { feature: "Export PDF", values: ["✅", "✅", "✅"] },
  { feature: "Supporto", values: ["Community", "Email", "Prioritario"] },
];

const FAQ: { q: string; a: string }[] = [
  { q: "Cos'è un credito?", a: "Un'immagine generata dall'AI a qualità Medium. Le qualità Low e High hanno consumi diversi (vedi tabella)." },
  { q: "Cos'è il piano Free-To-Play?", a: "È il piano gratuito di ingresso: puoi creare 1 libretto striscia (1 tavola), 1 figurina e 1 cover per capire come funziona SnapToon. Nessuna carta di credito richiesta." },
  { q: "Cosa succede se finisco i crediti?", a: "Puoi acquistare pacchetti extra senza cambiare piano. Oppure aspetti il rinnovo mensile." },
  { q: "Posso passare da un piano all'altro?", a: "Sì, in qualsiasi momento. Il cambio è immediato e pro-rated." },
  { q: "Posso disdire?", a: "Sì, in qualsiasi momento. Resti attivo fino a fine periodo già pagato." },
  { q: "I crediti scadono?", a: "I crediti del piano scadono col rinnovo mensile. I pacchetti extra restano per 12 mesi." },
  { q: "Le opere create sono mie?", a: "Sì, al 100%. SnapToon non rivendica diritti su quello che generi." },
];

export default function AbbonamentiPage() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  return (
    <SiteShell active="/abbonamenti">
      {/* Hero */}
      <section className="section" style={{ paddingTop: "100px", paddingBottom: "32px", textAlign: "center" }}>
        <div className="lp-container">
          <h1 style={{ fontSize: "clamp(1.75rem, 6vw, 3.75rem)", fontWeight: 800, color: "#F1F5F9", lineHeight: 1.1, letterSpacing: "-0.03em", marginBottom: "20px" }}>Scegli il piano giusto per te</h1>
          <p style={{ fontSize: "1.125rem", color: "#94A3B8", lineHeight: 1.6, maxWidth: "720px", margin: "0 auto" }}>
            Inizia gratis con Free-To-Play. Un credito = un&apos;immagine generata dall&apos;AI (qualità Medium). Gli abbonamenti si rinnovano mensilmente e puoi disdire quando vuoi.
          </p>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", background: "#161B26", border: "1px solid #2D3748", borderRadius: "100px", padding: "4px", marginTop: "28px" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, padding: "8px 18px", borderRadius: "100px", background: "#F59E0B", color: "#0D1017" }}>Mensile</span>
            <span style={{ fontSize: "13px", fontWeight: 600, padding: "8px 18px", color: "#64748B" }}>Annuale −20% · presto</span>
          </div>
        </div>
      </section>

      {/* Piani */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "60px" }}>
        <div className="lp-container">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px", alignItems: "stretch" }}>
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                id={plan.id}
                className="lift"
                style={{
                  position: "relative", display: "flex", flexDirection: "column",
                  background: "#161B26",
                  border: plan.popular ? "1px solid #F59E0B" : plan.free ? "1px solid #22C55E" : "1px solid #1E2436",
                  borderRadius: "18px", padding: "28px",
                  boxShadow: plan.popular ? "0 0 0 1px rgba(245,158,11,0.2), 0 12px 32px rgba(245,158,11,0.08)" : plan.free ? "0 0 0 1px rgba(34,197,94,0.2)" : "none",
                }}
              >
                {plan.popular && (
                  <span style={{ position: "absolute", top: "-12px", left: "50%", transform: "translateX(-50%)", background: "#F59E0B", color: "#0D1017", fontSize: "11px", fontWeight: 700, padding: "4px 12px", borderRadius: "100px", whiteSpace: "nowrap" }}>⭐ Più popolare</span>
                )}
                {plan.free && (
                  <span style={{ position: "absolute", top: "-12px", left: "50%", transform: "translateX(-50%)", background: "#22C55E", color: "#0D1017", fontSize: "11px", fontWeight: 700, padding: "4px 12px", borderRadius: "100px", whiteSpace: "nowrap" }}>🎁 Prova gratuita</span>
                )}
                <div style={{ fontSize: "24px" }}>{plan.emoji}</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#F1F5F9", marginTop: "8px" }}>{plan.name}</div>
                <div style={{ fontSize: "13px", color: "#94A3B8", marginBottom: "16px", minHeight: "34px" }}>{plan.tagline}</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "4px", marginBottom: "20px" }}>
                  <span style={{ fontSize: "2rem", fontWeight: 800, color: "#F1F5F9" }}>{plan.price}</span>
                  {!plan.free && <span style={{ fontSize: "13px", color: "#64748B" }}>/mese</span>}
                </div>
                <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px 0", display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
                  {plan.features.map((f) => (
                    <li key={f.text} style={{ display: "flex", alignItems: "flex-start", gap: "8px", fontSize: "13.5px", color: f.ok ? "#CBD5E1" : "#64748B" }}>
                      <span>{f.ok ? "✅" : "❌"}</span>
                      <span>{f.text}</span>
                    </li>
                  ))}
                </ul>
                <a href={plan.href} className={`btn ${plan.popular || plan.free ? "btn-primary" : "btn-secondary"}`} style={{ padding: "12px 18px", width: "100%" }}>{plan.cta}</a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Tabella comparativa */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "60px", background: "#0A0E17", borderTop: "1px solid #1E2436", borderBottom: "1px solid #1E2436" }}>
        <div className="lp-container">
          <h2 style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontWeight: 700, color: "#F1F5F9", marginBottom: "28px", textAlign: "center" }}>Confronto dettagliato</h2>
          <div style={{ overflowX: "auto", border: "1px solid #1E2436", borderRadius: "16px" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "640px", fontSize: "13.5px" }}>
              <thead>
                <tr style={{ background: "#161B26" }}>
                  <th style={{ textAlign: "left", padding: "14px 18px", color: "#94A3B8", fontWeight: 600 }}>Feature</th>
                  {PLANS.map((p) => (
                    <th key={p.id} style={{ textAlign: "center", padding: "14px 18px", color: p.popular ? "#F59E0B" : p.free ? "#22C55E" : "#F1F5F9", fontWeight: 700 }}>{p.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {TABLE.map((row, i) => (
                  <tr key={row.feature} style={{ borderTop: "1px solid #1E2436", background: i % 2 ? "rgba(255,255,255,0.015)" : "transparent" }}>
                    <td style={{ padding: "12px 18px", color: "#CBD5E1" }}>{row.feature}</td>
                    {row.values.map((v, j) => (
                      <td key={j} style={{ padding: "12px 18px", textAlign: "center", color: "#E2E8F0" }}>{v}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA Editori (sostituisce il piano Editore) */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "60px" }}>
        <div className="lp-container" style={{ maxWidth: "820px" }}>
          <div style={{ background: "linear-gradient(135deg,#1E2436 0%,#161B26 100%)", border: "1px solid #2D3748", borderRadius: "20px", padding: "48px 40px", textAlign: "center" }}>
            <div style={{ fontSize: "40px", marginBottom: "16px" }}>📚</div>
            <h2 style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "12px" }}>Sei un editore?</h2>
            <p style={{ fontSize: "15px", color: "#94A3B8", lineHeight: 1.7, maxWidth: "640px", margin: "0 auto 24px" }}>
              Case editrici, collettivi, studi creativi: se hai un progetto continuativo, ti costruiamo una convenzione su misura — volumi di crediti dedicati, branding personalizzato, account multi-utente, export IDML tipografico, supporto diretto.
            </p>
            <a href="mailto:info@snaptoon.art?subject=Convenzione%20editore%20SnapToon" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>
              Mettiamoci in contatto →
            </a>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "40px" }}>
        <div className="lp-container" style={{ maxWidth: "820px" }}>
          <h2 style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontWeight: 700, color: "#F1F5F9", marginBottom: "28px", textAlign: "center" }}>Domande frequenti</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {FAQ.map((item, i) => {
              const open = openFaq === i;
              return (
                <div key={item.q} style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: "12px", overflow: "hidden" }}>
                  <button
                    onClick={() => setOpenFaq(open ? null : i)}
                    style={{ width: "100%", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", padding: "18px 20px", background: "transparent", border: "none", cursor: "pointer", textAlign: "left", color: "#F1F5F9", fontSize: "15px", fontWeight: 600 }}
                  >
                    {item.q}
                    <span style={{ color: "#F59E0B", fontSize: "20px", lineHeight: 1, transform: open ? "rotate(45deg)" : "none", transition: "transform 0.2s" }}>+</span>
                  </button>
                  {open && <div style={{ padding: "0 20px 18px 20px", color: "#94A3B8", fontSize: "14px", lineHeight: 1.6 }}>{item.a}</div>}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA finale */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "100px" }}>
        <div className="lp-container" style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "20px" }}>Hai altri dubbi?</h2>
          <a href="mailto:info@snaptoon.art" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>Scrivici →</a>
        </div>
      </section>
    </SiteShell>
  );
}
