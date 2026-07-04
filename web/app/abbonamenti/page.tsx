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
}

const PLANS: Plan[] = [
  {
    id: "kids", emoji: "🌟", name: "Kids", price: "€4,99", tagline: "Per genitori, insegnanti, biblioteche",
    features: [
      { text: "100 crediti/mese", ok: true },
      { text: "5 libretti", ok: true },
      { text: "Modalità KIDS guidata", ok: true },
      { text: "Qualità Medium", ok: true },
      { text: "Export PDF stampabile", ok: true },
      { text: "3 stili dedicati ai bambini", ok: true },
      { text: "Modalità Pro", ok: false },
      { text: "Bookshop", ok: false },
    ],
    cta: "Inizia con Kids →",
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
      { text: "Bookshop", ok: false },
    ],
    cta: "Inizia con Base →",
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
      { text: "Bookshop", ok: false },
    ],
    cta: "Vai Premium →",
  },
  {
    id: "editore", emoji: "📚", name: "Editore", price: "€99", tagline: "Per case editrici e collettivi",
    features: [
      { text: "1000 crediti/mese", ok: true },
      { text: "Progetti illimitati", ok: true },
      { text: "Tutto di Premium, più:", ok: true },
      { text: "Bookshop: vendi senza commissioni", ok: true },
      { text: "Account multi-utente (fino a 5)", ok: true },
      { text: "Report vendite e analytics", ok: true },
      { text: "Branding personalizzato", ok: true },
      { text: "Account manager dedicato", ok: true },
    ],
    cta: "Diventa editore →",
  },
];

const TABLE: { feature: string; values: string[] }[] = [
  { feature: "Crediti/mese", values: ["100", "200", "600", "1000"] },
  { feature: "Progetti", values: ["5", "5", "Illimitati", "Illimitati"] },
  { feature: "Modalità KIDS", values: ["✅", "✅", "✅", "✅"] },
  { feature: "Modalità Pro", values: ["❌", "✅", "✅", "✅"] },
  { feature: "Stili", values: ["3", "98", "98 + custom", "98 + custom"] },
  { feature: "Qualità Low", values: ["—", "✅", "✅", "✅"] },
  { feature: "Qualità Medium", values: ["✅", "✅", "✅", "✅"] },
  { feature: "Qualità High", values: ["❌", "❌", "✅", "✅"] },
  { feature: "Export PDF", values: ["✅", "✅", "✅", "✅"] },
  { feature: "Bookshop venditore", values: ["❌", "❌", "❌", "✅"] },
  { feature: "Account multi-utente", values: ["❌", "❌", "❌", "5"] },
  { feature: "Supporto", values: ["Email", "Email", "Prioritario", "Manager dedicato"] },
];

const FAQ: { q: string; a: string }[] = [
  { q: "Cos'è un credito?", a: "Un'immagine generata dall'AI a qualità Medium. Le qualità Low e High hanno consumi diversi (vedi tabella)." },
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
            Un credito = un&apos;immagine generata dall&apos;AI (qualità Medium). Niente sorprese: gli abbonamenti si rinnovano mensilmente e puoi disdire quando vuoi.
          </p>
          {/* Toggle Mensile / Annuale (MVP: solo Mensile) */}
          <div style={{ display: "inline-flex", alignItems: "center", gap: "4px", background: "#161B26", border: "1px solid #2D3748", borderRadius: "100px", padding: "4px", marginTop: "28px" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, padding: "8px 18px", borderRadius: "100px", background: "#F59E0B", color: "#0D1017" }}>Mensile</span>
            <span style={{ fontSize: "13px", fontWeight: 600, padding: "8px 18px", color: "#64748B" }}>Annuale −20% · presto</span>
          </div>
        </div>
      </section>

      {/* Piani */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "60px" }}>
        <div className="lp-container">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "24px", alignItems: "stretch" }}>
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                id={plan.id}
                className="lift"
                style={{
                  position: "relative", display: "flex", flexDirection: "column",
                  background: "#161B26",
                  border: plan.popular ? "1px solid #F59E0B" : "1px solid #1E2436",
                  borderRadius: "18px", padding: "28px",
                  boxShadow: plan.popular ? "0 0 0 1px rgba(245,158,11,0.2), 0 12px 32px rgba(245,158,11,0.08)" : "none",
                }}
              >
                {plan.popular && (
                  <span style={{ position: "absolute", top: "-12px", left: "50%", transform: "translateX(-50%)", background: "#F59E0B", color: "#0D1017", fontSize: "11px", fontWeight: 700, padding: "4px 12px", borderRadius: "100px", whiteSpace: "nowrap" }}>⭐ Più popolare</span>
                )}
                <div style={{ fontSize: "24px" }}>{plan.emoji}</div>
                <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#F1F5F9", marginTop: "8px" }}>{plan.name}</div>
                <div style={{ fontSize: "13px", color: "#94A3B8", marginBottom: "16px", minHeight: "34px" }}>{plan.tagline}</div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "4px", marginBottom: "20px" }}>
                  <span style={{ fontSize: "2rem", fontWeight: 800, color: "#F1F5F9" }}>{plan.price}</span>
                  <span style={{ fontSize: "13px", color: "#64748B" }}>/mese</span>
                </div>
                <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px 0", display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
                  {plan.features.map((f) => (
                    <li key={f.text} style={{ display: "flex", alignItems: "flex-start", gap: "8px", fontSize: "13.5px", color: f.ok ? "#CBD5E1" : "#64748B" }}>
                      <span>{f.ok ? "✅" : "❌"}</span>
                      <span>{f.text}</span>
                    </li>
                  ))}
                </ul>
                <a href={`mailto:info@snaptoon.art?subject=${encodeURIComponent(`Attivazione piano ${plan.name}`)}`} className={`btn ${plan.popular ? "btn-primary" : "btn-secondary"}`} style={{ padding: "12px 18px", width: "100%" }}>{plan.cta}</a>
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
                    <th key={p.id} style={{ textAlign: "center", padding: "14px 18px", color: p.popular ? "#F59E0B" : "#F1F5F9", fontWeight: 700 }}>{p.name}</th>
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

      {/* FAQ */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "40px" }}>
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
          <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "20px" }}>Hai dubbi? Contattaci.</h2>
          <a href="mailto:info@snaptoon.art" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>Scrivici →</a>
        </div>
      </section>
    </SiteShell>
  );
}
