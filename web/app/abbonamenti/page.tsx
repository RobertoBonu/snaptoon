"use client";

import { useState } from "react";
import { SiteShell } from "@/components/site";

interface Feature { text: string; ok: boolean }
interface Plan {
  id: string;
  registerKey: string;
  emoji: string;
  name: string;
  price: string;
  tagline: string;
  popular?: boolean;
  free?: boolean;
  features: Feature[];
  welcomeBonus?: string;
  cta: string;
}

const PLANS: Plan[] = [
  {
    id: "free_to_play",
    registerKey: "free_to_play",
    emoji: "🎁",
    name: "Free-To-Play",
    price: "GRATIS",
    tagline: "Prova SnapToon, senza carta di credito",
    free: true,
    features: [
      { text: "1 striscia KIDS (1 tavola)", ok: true },
      { text: "1 figurina collezionabile", ok: true },
      { text: "1 cover standalone", ok: true },
      { text: "Qualità Media", ok: true },
      { text: "Libretti Brevi / Lunghi", ok: false },
      { text: "Progetti Pro", ok: false },
      { text: "BookShop", ok: false },
    ],
    cta: "Registrati gratis →",
  },
  {
    id: "kids_plan",
    registerKey: "kids_plan",
    emoji: "🌟",
    name: "KIDS",
    price: "€6,99",
    tagline: "Per famiglie, insegnanti, biblioteche",
    features: [
      { text: "1 libretto KIDS/mese (breve o lungo)", ok: true },
      { text: "2 cover/mese", ok: true },
      { text: "2 figurine/mese", ok: true },
      { text: "Qualità Media", ok: true },
      { text: "Modalità KIDS guidata", ok: true },
      { text: "Export PDF stampabile", ok: true },
      { text: "Progetti Pro", ok: false },
      { text: "Qualità High", ok: false },
    ],
    welcomeBonus: "🎉 1° mese: +5 cover e +5 figurine gratis!",
    cta: "Scegli KIDS →",
  },
  {
    id: "base",
    registerKey: "base",
    emoji: "🚀",
    name: "PRO",
    price: "€19",
    tagline: "Per autori, hobbisti, professionisti",
    popular: true,
    features: [
      { text: "1 progetto Pro/mese", ok: true },
      { text: "3 cover/mese", ok: true },
      { text: "3 figurine/mese", ok: true },
      { text: "Qualità Medium o High", ok: true },
      { text: "BookShop community", ok: true },
      { text: "Editor impaginazione libera", ok: true },
      { text: "Export PDF stampabile", ok: true },
      { text: "Libretti KIDS", ok: false },
    ],
    welcomeBonus: "🎉 1° mese: +10 cover e +10 figurine gratis!",
    cta: "Scegli PRO →",
  },
];

const TABLE: { feature: string; values: string[] }[] = [
  { feature: "Libretti KIDS", values: ["❌ (solo striscia)", "1/mese", "❌"] },
  { feature: "Striscia KIDS (1 tavola)", values: ["1 tantum", "inclusa", "❌"] },
  { feature: "Progetti Pro (fumetto)", values: ["❌", "❌", "1/mese"] },
  { feature: "Cover standalone", values: ["1 tantum", "2/mese", "3/mese"] },
  { feature: "Figurine collezionabili", values: ["1 tantum", "2/mese", "3/mese"] },
  { feature: "Qualità Medium", values: ["✅", "✅", "✅"] },
  { feature: "Qualità High", values: ["❌", "❌", "✅"] },
  { feature: "Export PDF", values: ["✅", "✅", "✅"] },
  { feature: "BookShop pubblicazione", values: ["❌", "✅", "✅"] },
  { feature: "Editor impaginazione libera", values: ["❌", "❌", "✅"] },
  { feature: "Welcome bonus 1° mese", values: ["—", "+5 cover +5 fig", "+10 cover +10 fig"] },
];

const EXTRA_TABLE: { feature: string; kids: string; pro: string }[] = [
  { feature: "+1 libretto KIDS", kids: "€4,99", pro: "—" },
  { feature: "+1 progetto Pro Medium", kids: "—", pro: "€7,99" },
  { feature: "+1 progetto Pro High", kids: "—", pro: "€14,99" },
  { feature: "+1 cover Medium", kids: "€1,49", pro: "€1,49" },
  { feature: "5 cover Medium", kids: "€4,99", pro: "€4,99" },
  { feature: "+1 cover High", kids: "—", pro: "€3,99" },
  { feature: "5 cover High", kids: "—", pro: "€12,00" },
  { feature: "+1 figurina Medium", kids: "€1,29", pro: "€1,29" },
  { feature: "5 figurine Medium", kids: "€4,49", pro: "€4,49" },
  { feature: "+1 figurina High", kids: "—", pro: "€2,99" },
  { feature: "5 figurine High", kids: "—", pro: "€10,00" },
];

const FAQ: { q: string; a: string }[] = [
  { q: "Come funzionano le quote mensili?", a: "Ogni piano include un certo numero di libretti/progetti/cover/figurine al mese. Le quote non usate si resettano al rinnovo. Se ne servono di più, aggiungi Pacchetti Extra a unità singola." },
  { q: "Cos'è il Welcome Bonus?", a: "Solo al PRIMO mese di attivazione del piano ricevi quote extra gratis: KIDS +5 cover e +5 figurine, PRO +10 cover e +10 figurine. Le quote extra non scadono." },
  { q: "Cos'è un Pacchetto Extra?", a: "Sono acquisti una-tantum di quote aggiuntive (+1 libretto €4,99, +1 progetto Pro Medium €7,99, ecc.). Le quote extra NON scadono e vengono usate quando finiscono quelle del piano." },
  { q: "Cos'è la differenza Medium vs High?", a: "Medium è la qualità standard (immagini di alta qualità già molto buone). High è la qualità massima OpenAI (dettagli più fini, testi più nitidi) ma costa di più: da qui i pacchetti separati Medium e High per cover e figurine." },
  { q: "Il piano PRO include libretti KIDS?", a: "No. PRO è dedicato al workflow Pro (fumetto/webtoon/graphic novel con editor libero). Se vuoi anche libretti KIDS, aggiungi il piano KIDS o compra +1 libretto KIDS come extra." },
  { q: "Cos'è il piano Free-To-Play?", a: "Il piano gratuito di ingresso: 1 striscia KIDS, 1 figurina e 1 cover per capire come funziona SnapToon. Nessuna carta di credito." },
  { q: "Posso passare da un piano all'altro?", a: "Sì, in qualsiasi momento. Il cambio è immediato. Il welcome bonus si applica solo al primo attivamento di ciascun piano a pagamento." },
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
            Inizia gratis. Passa a KIDS o PRO quando vuoi. Il primo mese ricevi un welcome bonus di cover e figurine extra gratis.
          </p>
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
                {plan.welcomeBonus && (
                  <div style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.3)", borderRadius: "8px", padding: "8px 10px", marginBottom: "16px", fontSize: "12px", color: "#86EFAC", fontWeight: 600 }}>
                    {plan.welcomeBonus}
                  </div>
                )}
                <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px 0", display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
                  {plan.features.map((f) => (
                    <li key={f.text} style={{ display: "flex", alignItems: "flex-start", gap: "8px", fontSize: "13.5px", color: f.ok ? "#CBD5E1" : "#64748B" }}>
                      <span>{f.ok ? "✅" : "❌"}</span>
                      <span>{f.text}</span>
                    </li>
                  ))}
                </ul>
                <a href={`/register?plan=${plan.registerKey}`} className={`btn ${plan.popular || plan.free ? "btn-primary" : "btn-secondary"}`} style={{ padding: "12px 18px", width: "100%" }}>{plan.cta}</a>
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

      {/* Pacchetti Extra V03 */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "40px" }}>
        <div className="lp-container">
          <div style={{ textAlign: "center", marginBottom: "32px" }}>
            <h2 style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontWeight: 700, color: "#F1F5F9", marginBottom: "12px" }}>Pacchetti Extra a unità singola</h2>
            <p style={{ color: "#94A3B8", maxWidth: "640px", margin: "0 auto" }}>
              Finite le quote del mese? Aggiungi solo quello che ti serve. Le quote extra non scadono.
            </p>
          </div>
          <div style={{ overflowX: "auto", border: "1px solid #1E2436", borderRadius: "16px", maxWidth: "820px", margin: "0 auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13.5px" }}>
              <thead>
                <tr style={{ background: "#161B26" }}>
                  <th style={{ textAlign: "left", padding: "14px 18px", color: "#94A3B8", fontWeight: 600 }}>Pacchetto</th>
                  <th style={{ textAlign: "center", padding: "14px 18px", color: "#22C55E", fontWeight: 700 }}>KIDS</th>
                  <th style={{ textAlign: "center", padding: "14px 18px", color: "#F59E0B", fontWeight: 700 }}>PRO</th>
                </tr>
              </thead>
              <tbody>
                {EXTRA_TABLE.map((row, i) => (
                  <tr key={row.feature} style={{ borderTop: "1px solid #1E2436", background: i % 2 ? "rgba(255,255,255,0.015)" : "transparent" }}>
                    <td style={{ padding: "12px 18px", color: "#CBD5E1" }}>{row.feature}</td>
                    <td style={{ padding: "12px 18px", textAlign: "center", color: "#E2E8F0" }}>{row.kids}</td>
                    <td style={{ padding: "12px 18px", textAlign: "center", color: "#E2E8F0" }}>{row.pro}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ textAlign: "center", marginTop: "20px", color: "#64748B", fontSize: "13px" }}>
            Gestisci le tue quote e acquisti da <a href="/app/pacchetti" style={{ color: "#F59E0B" }}>/app/pacchetti</a> (dopo login).
          </p>
        </div>
      </section>

      {/* CTA Editori */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "60px" }}>
        <div className="lp-container" style={{ maxWidth: "820px" }}>
          <div style={{ background: "linear-gradient(135deg,#1E2436 0%,#161B26 100%)", border: "1px solid #2D3748", borderRadius: "20px", padding: "48px 40px", textAlign: "center" }}>
            <div style={{ fontSize: "40px", marginBottom: "16px" }}>📚</div>
            <h2 style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "12px" }}>Sei un editore?</h2>
            <p style={{ fontSize: "15px", color: "#94A3B8", lineHeight: 1.7, maxWidth: "640px", margin: "0 auto 24px" }}>
              Case editrici, collettivi, studi creativi: ti costruiamo una convenzione su misura — volumi dedicati, branding personalizzato, account multi-utente, export IDML tipografico, supporto diretto.
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

      <section className="section" style={{ paddingTop: "20px", paddingBottom: "100px" }}>
        <div className="lp-container" style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "20px" }}>Hai altri dubbi?</h2>
          <a href="mailto:info@snaptoon.art" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>Scrivici →</a>
        </div>
      </section>
    </SiteShell>
  );
}
