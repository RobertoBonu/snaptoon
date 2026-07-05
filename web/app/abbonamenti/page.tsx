"use client";

import { useState } from "react";
import { SiteShell } from "@/components/site";

interface Feature { text: string; ok: boolean }
interface Plan {
  id: string;
  registerKey: string;  // valore per query ?plan= su /register
  emoji: string;
  name: string;
  price: string;
  tagline: string;
  popular?: boolean;
  free?: boolean;
  features: Feature[];
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
      { text: "5 cover/mese", ok: true },
      { text: "5 figurine/mese", ok: true },
      { text: "Qualità Media", ok: true },
      { text: "Modalità KIDS guidata", ok: true },
      { text: "Export PDF stampabile", ok: true },
      { text: "Progetti Pro", ok: false },
      { text: "Qualità High", ok: false },
    ],
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
      { text: "5 progetti Pro/mese", ok: true },
      { text: "1 libretto KIDS/mese", ok: true },
      { text: "5 cover/mese", ok: true },
      { text: "5 figurine/mese", ok: true },
      { text: "Qualità Bassa + Media + Alta", ok: true },
      { text: "Reference image avanzate", ok: true },
      { text: "Export PDF stampabile", ok: true },
      { text: "Supporto prioritario", ok: true },
    ],
    cta: "Scegli PRO →",
  },
];

const TABLE: { feature: string; values: string[] }[] = [
  { feature: "Libretti KIDS (breve/lungo)", values: ["❌", "1/mese", "1/mese"] },
  { feature: "Striscia KIDS (1 tavola)", values: ["1 una tantum", "inclusa", "inclusa"] },
  { feature: "Progetti Pro (fumetto)", values: ["❌", "❌", "5/mese"] },
  { feature: "Cover standalone", values: ["1 una tantum", "5/mese", "5/mese"] },
  { feature: "Figurine collezionabili", values: ["1 una tantum", "5/mese", "5/mese"] },
  { feature: "Qualità Low + Medium", values: ["Solo Medium", "Solo Medium", "✅"] },
  { feature: "Qualità High (4× costo)", values: ["❌", "❌", "✅"] },
  { feature: "Export PDF", values: ["✅", "✅", "✅"] },
  { feature: "BookShop pubblicazione", values: ["❌", "✅", "✅"] },
  { feature: "Supporto", values: ["Community", "Email", "Prioritario"] },
];

const FAQ: { q: string; a: string }[] = [
  { q: "Come funzionano le quote mensili?", a: "Ogni piano include un certo numero di libretti/cover/figurine/progetti al mese. Le quote non usate si resettano al rinnovo. Se ne servono di più, acquisti Pacchetti Extra che si sommano." },
  { q: "Cos'è un Pacchetto Extra?", a: "Sono acquisti una-tantum di quote aggiuntive (es. 5 libretti KIDS a €18). Le quote extra NON scadono e vengono usate quando finiscono quelle del piano. Vedi tutti i pacchetti nella pagina /pacchetti dopo aver fatto login." },
  { q: "Cos'è il piano Free-To-Play?", a: "Il piano gratuito di ingresso: 1 striscia KIDS, 1 figurina e 1 cover per capire come funziona SnapToon. Nessuna carta di credito." },
  { q: "Posso passare da un piano all'altro?", a: "Sì, in qualsiasi momento. Il cambio è immediato e le nuove quote vengono applicate al rinnovo successivo." },
  { q: "Posso disdire?", a: "Sì, in qualsiasi momento. Resti attivo fino a fine periodo già pagato." },
  { q: "Le opere create sono mie?", a: "Sì, al 100%. SnapToon non rivendica diritti su quello che generi." },
  { q: "Posso stampare o esportare in ePub/Kindle?", a: "Sì, come Servizi Extra a pagamento (stampa fisica da €19/copia, export ePub/Kindle €9,99/formato, export IDML tipografico €19,99). Vedi /pacchetti dopo il login." },
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
            Inizia gratis con Free-To-Play. Poi passa a KIDS o PRO — quote mensili chiare + pacchetti extra all&apos;occorrenza. Nessuna sorpresa.
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

      {/* Pacchetti Extra promo */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "40px" }}>
        <div className="lp-container">
          <div style={{ textAlign: "center", marginBottom: "32px" }}>
            <h2 style={{ fontSize: "clamp(1.5rem, 2.5vw, 2rem)", fontWeight: 700, color: "#F1F5F9", marginBottom: "12px" }}>Ti serve di più? Pacchetti extra</h2>
            <p style={{ color: "#94A3B8", maxWidth: "640px", margin: "0 auto" }}>
              Se finisci le quote mensili, aggiungi solo quello che ti serve senza cambiare piano. Più ne prendi, meno costano.
            </p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px" }}>
            {[
              { emoji: "📕", name: "Libretti KIDS extra", from: "da €4,99", scale: "10 libretti = €32 (€3,20/cad)" },
              { emoji: "📗", name: "Progetti Pro extra", from: "da €9,99", scale: "10 progetti = €60 (€6,00/cad)" },
              { emoji: "🖼️", name: "Cover extra", from: "da €5,99 x3", scale: "10 cover = €16 (€1,60/cad)" },
              { emoji: "🎴", name: "Figurine extra", from: "da €4,99 x3", scale: "10 figurine = €12 (€1,20/cad)" },
              { emoji: "🖨️", name: "Stampa fisica", from: "da €19/copia", scale: "50 copie = €329 (€6,58/cad)" },
              { emoji: "📤", name: "Export ePub / Kindle / IDML", from: "da €9,99", scale: "Bundle Pro tutti i formati = €29,99" },
            ].map((p) => (
              <div key={p.name} style={{ background: "#161B26", border: "1px solid #1E2436", borderRadius: "14px", padding: "20px" }}>
                <div style={{ fontSize: "22px", marginBottom: "8px" }}>{p.emoji}</div>
                <div style={{ fontWeight: 700, color: "#F1F5F9", marginBottom: "4px" }}>{p.name}</div>
                <div style={{ fontSize: "13px", color: "#F59E0B", marginBottom: "6px" }}>{p.from}</div>
                <div style={{ fontSize: "12px", color: "#64748B" }}>{p.scale}</div>
              </div>
            ))}
          </div>
          <div style={{ textAlign: "center", marginTop: "24px" }}>
            <a href="/app/pacchetti" style={{ color: "#F59E0B", fontSize: "14px", fontWeight: 600 }}>Vedi listino completo (dopo login) →</a>
          </div>
        </div>
      </section>

      {/* CTA Editori */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "60px" }}>
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

      <section className="section" style={{ paddingTop: "20px", paddingBottom: "100px" }}>
        <div className="lp-container" style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "20px" }}>Hai altri dubbi?</h2>
          <a href="mailto:info@snaptoon.art" className="btn btn-primary" style={{ padding: "14px 28px", fontSize: "15px" }}>Scrivici →</a>
        </div>
      </section>
    </SiteShell>
  );
}
