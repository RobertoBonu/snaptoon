"use client";

import Link from "next/link";
import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";

const PLANS: {
  key: "free_to_play" | "kids_plan" | "base";
  label: string;
  price: string;
  tagline: string;
  features: string[];
  cta: string;
  highlight?: boolean;
}[] = [
  {
    key: "free_to_play",
    label: "Free-To-Play",
    price: "GRATIS",
    tagline: "Prova SnapToon senza carta di credito",
    features: [
      "1 striscia KIDS (1 tavola)",
      "1 figurina collezionabile",
      "1 cover standalone",
      "Qualità Media",
    ],
    cta: "Registrati gratis",
    highlight: true,
  },
  {
    key: "kids_plan",
    label: "KIDS",
    price: "€6,99/mese",
    tagline: "Per famiglie, insegnanti, biblioteche",
    features: [
      "1 libretto KIDS/mese",
      "2 cover/mese + 2 figurine/mese",
      "Qualità Media",
      "🎉 1° mese: +5 cover +5 figurine gratis",
    ],
    cta: "Scegli KIDS",
  },
  {
    key: "base",
    label: "PRO",
    price: "€19/mese",
    tagline: "Per autori indie e professionisti",
    features: [
      "1 progetto Pro/mese",
      "3 cover/mese + 3 figurine/mese",
      "Qualità Medium o High",
      "BookShop + editor libero",
      "🎉 1° mese: +10 cover +10 figurine gratis",
    ],
    cta: "Scegli PRO",
  },
];

function RegisterInner() {
  const params = useSearchParams();
  const initialPlan = (params?.get("plan") as "free_to_play" | "kids_plan" | "base") || "free_to_play";

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [plan, setPlan] = useState<"free_to_play" | "kids_plan" | "base">(initialPlan);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pseudonym, setPseudonym] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<{ email: string; planLabel: string } | null>(null);

  const selectedPlan = PLANS.find((p) => p.key === plan) || PLANS[0];

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      // Se piano a pagamento: passa da /checkout mock; se free_to_play: registrazione diretta
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, plan, pseudonym }),
        credentials: "include",
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        // Estrai il vero messaggio d'errore, non importa che forma abbia
        let msg = `Errore ${res.status} durante la registrazione.`;
        if (typeof data?.detail === "string") {
          msg = data.detail;
        } else if (data?.detail?.message) {
          msg = data.detail.message;
        } else if (Array.isArray(data?.detail) && data.detail.length > 0) {
          // Pydantic validation errors: mostra il primo
          const first = data.detail[0];
          msg = first?.msg || `Campo non valido: ${JSON.stringify(first?.loc || [])}`;
        } else if (data?.detail) {
          msg = JSON.stringify(data.detail);
        }
        setError(msg);
        return;
      }
      // Per piani a pagamento redirect a checkout mock
      if (plan !== "free_to_play") {
        window.location.href = `/checkout?plan=${plan}&email=${encodeURIComponent(email)}`;
        return;
      }
      setSuccess({ email: data.email, planLabel: selectedPlan.label });
    } catch {
      setError("Errore di connessione. Riprova.");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <main className="min-h-screen flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md text-center">
          <div className="text-6xl mb-4">✉️</div>
          <h1 className="text-3xl font-bold mb-4">Registrazione ricevuta!</h1>
          <p className="text-[var(--color-fg-muted)] mb-6">
            Ti abbiamo inviato una email di conferma a{" "}
            <b className="text-[var(--color-fg)]">{success.email}</b>.
            <br />
            Ti manderemo un&apos;altra email quando il tuo piano{" "}
            <b>{success.planLabel}</b> sarà attivo (di solito entro poche
            ore).
          </p>
          <Link
            href="/login"
            className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-3 rounded-lg"
          >
            Vai al login
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-4xl">
        <Link href="/" className="block text-center mb-8 group">
          <div className="text-5xl mb-2 select-none">📚</div>
          <h1 className="text-3xl font-bold text-[var(--color-accent)]">
            SnapToon
          </h1>
        </Link>

        {/* Step indicator */}
        <div className="flex gap-2 mb-8 max-w-md mx-auto">
          {([1, 2, 3] as const).map((n) => (
            <div
              key={n}
              className={`flex-1 h-1.5 rounded-full ${
                step >= n ? "bg-[var(--color-accent)]" : "bg-[var(--color-border)]"
              }`}
            />
          ))}
        </div>

        {error && (
          <p className="max-w-md mx-auto text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-6">
            {error}
          </p>
        )}

        {/* STEP 1: Scelta piano */}
        {step === 1 && (
          <>
            <h2 className="text-2xl font-bold text-center mb-6">
              Scegli il tuo piano
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              {PLANS.map((p) => (
                <button
                  key={p.key}
                  onClick={() => setPlan(p.key)}
                  className={`text-left p-5 rounded-xl border-2 transition-all ${
                    plan === p.key
                      ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5"
                      : "border-[var(--color-border)] bg-[var(--color-bg-elev)] hover:border-[var(--color-accent)]/50"
                  } ${p.highlight ? "ring-1 ring-[var(--color-accent)]/30" : ""}`}
                >
                  {p.highlight && (
                    <span className="inline-block text-xs bg-[var(--color-accent)] text-[var(--color-bg)] px-2 py-0.5 rounded mb-2 font-bold">
                      CONSIGLIATO PER INIZIARE
                    </span>
                  )}
                  <div className="font-bold text-lg">{p.label}</div>
                  <div className="text-2xl font-bold text-[var(--color-accent)] my-2">
                    {p.price}
                  </div>
                  <div className="text-xs text-[var(--color-fg-muted)] mb-3">
                    {p.tagline}
                  </div>
                  <ul className="text-xs space-y-1">
                    {p.features.map((f) => (
                      <li key={f}>✓ {f}</li>
                    ))}
                  </ul>
                </button>
              ))}
            </div>
            <div className="flex justify-center">
              <button
                onClick={() => setStep(2)}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-8 py-3 rounded-lg"
              >
                Continua con {selectedPlan.label} →
              </button>
            </div>
          </>
        )}

        {/* STEP 2: Dati account */}
        {step === 2 && (
          <div className="max-w-md mx-auto">
            <h2 className="text-2xl font-bold text-center mb-6">
              I tuoi dati
            </h2>
            <div className="space-y-4 bg-[var(--color-bg-elev)] p-6 rounded-xl border border-[var(--color-border)]">
              <div>
                <label className="block text-sm font-medium mb-1">Email *</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Password * <span className="text-[var(--color-fg-muted)]">(min 8 caratteri)</span>
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  minLength={8}
                  required
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Nome autore / pseudonimo <span className="text-[var(--color-fg-muted)]">(opzionale)</span>
                </label>
                <input
                  type="text"
                  value={pseudonym}
                  onChange={(e) => setPseudonym(e.target.value)}
                  maxLength={80}
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
                />
              </div>
            </div>
            <div className="flex justify-between mt-6">
              <button
                onClick={() => setStep(1)}
                className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              >
                ← Cambia piano
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!email.trim() || password.length < 8}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2 rounded-lg disabled:opacity-40"
              >
                Continua →
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Conferma */}
        {step === 3 && (
          <div className="max-w-md mx-auto">
            <h2 className="text-2xl font-bold text-center mb-6">Conferma</h2>
            <div className="bg-[var(--color-bg-elev)] p-6 rounded-xl border border-[var(--color-border)] space-y-3 mb-6 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--color-fg-muted)]">Piano</span>
                <span className="font-semibold">
                  {selectedPlan.label} — {selectedPlan.price}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--color-fg-muted)]">Email</span>
                <span>{email}</span>
              </div>
              {pseudonym && (
                <div className="flex justify-between">
                  <span className="text-[var(--color-fg-muted)]">Nome</span>
                  <span>{pseudonym}</span>
                </div>
              )}
            </div>
            {plan !== "free_to_play" && (
              <p className="text-xs text-[var(--color-fg-muted)] mb-4">
                Al passo successivo verrai indirizzato al checkout Stripe
                (per ora mock). Nessun addebito reale.
              </p>
            )}
            <div className="flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              >
                ← Indietro
              </button>
              <button
                onClick={submit}
                disabled={loading}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2 rounded-lg disabled:opacity-40"
              >
                {loading
                  ? "Registrazione..."
                  : plan === "free_to_play"
                  ? "Registrati gratis"
                  : "Vai al checkout"}
              </button>
            </div>
          </div>
        )}

        <p className="text-center text-sm text-[var(--color-fg-muted)] mt-6">
          Hai già un account?{" "}
          <Link href="/login" className="text-[var(--color-accent)] hover:underline">
            Fai login
          </Link>
        </p>
      </div>
    </main>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Caricamento...</div>}>
      <RegisterInner />
    </Suspense>
  );
}
