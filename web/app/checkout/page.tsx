"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";

const PLAN_INFO: Record<string, { label: string; price: string; welcome: string }> = {
  free_to_play: { label: "Free-To-Play", price: "GRATIS", welcome: "" },
  kids_plan: { label: "KIDS", price: "€6,99/mese", welcome: "🎉 Welcome bonus 1° mese: +5 cover +5 figurine gratis" },
  base: { label: "PRO", price: "€19/mese", welcome: "🎉 Welcome bonus 1° mese: +10 cover +10 figurine gratis" },
  premium: { label: "PRO (Premium legacy)", price: "€49/mese", welcome: "" },
};

function CheckoutInner() {
  const params = useSearchParams();
  const plan = params?.get("plan") || "base";
  const email = params?.get("email") || "";
  const info = PLAN_INFO[plan] || PLAN_INFO.base;

  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleMockCheckout() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/subscription/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          plan,
          mock_stripe_token: "mock_" + Math.random().toString(36).slice(2),
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        setError(d.detail || "Errore durante il checkout");
        return;
      }
      setDone(true);
    } catch {
      setError("Errore di connessione. Riprova.");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <main className="min-h-screen flex items-center justify-center p-8">
        <div className="max-w-md text-center">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-3xl font-bold mb-3">Pagamento ricevuto (mock)</h1>
          <p className="text-[var(--color-fg-muted)] mb-6">
            Ti abbiamo inviato una email di conferma. Il piano{" "}
            <b>{info.label}</b> sarà attivo dopo l&apos;approvazione admin
            (di solito entro poche ore).
          </p>
          <Link
            href="/app"
            className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-3 rounded-lg"
          >
            Vai alla dashboard
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="max-w-md w-full">
        <Link href="/" className="block text-center mb-8">
          <div className="text-4xl mb-1">📚</div>
          <h1 className="text-2xl font-bold text-[var(--color-accent)]">SnapToon</h1>
        </Link>

        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-2xl p-6">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-4 mb-4">
            <div>
              <div className="text-lg font-bold">Checkout</div>
              <div className="text-xs text-[var(--color-fg-muted)]">
                Piano: <b>{info.label}</b>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-[var(--color-accent)]">
                {info.price}
              </div>
            </div>
          </div>

          <div className="text-sm space-y-3 mb-6">
            <div className="flex justify-between">
              <span className="text-[var(--color-fg-muted)]">Email</span>
              <span>{email || "—"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-fg-muted)]">Metodo pagamento</span>
              <span>Stripe (mock)</span>
            </div>
          </div>

          {info.welcome && (
            <div className="bg-green-950/30 border border-green-900/50 rounded p-3 mb-4 text-sm text-green-400 font-medium">
              {info.welcome}
            </div>
          )}

          {error && (
            <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
              {error}
            </p>
          )}

          <div className="bg-yellow-950/30 border border-yellow-900/50 rounded p-3 mb-4 text-xs">
            ⚠️ <b>Mock:</b> Nessun addebito reale. In produzione qui apparirà
            il form Stripe con carta di credito. La richiesta verrà comunque
            registrata e sottoposta ad approvazione admin.
          </div>

          <button
            onClick={handleMockCheckout}
            disabled={loading}
            className="w-full bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-bold py-3 rounded-lg disabled:opacity-50"
          >
            {loading ? "Elaboro..." : `Paga ${info.price} (mock)`}
          </button>

          <p className="text-xs text-[var(--color-fg-muted)] text-center mt-4">
            Puoi disdire in qualsiasi momento.
          </p>
        </div>
      </div>
    </main>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Caricamento...</div>}>
      <CheckoutInner />
    </Suspense>
  );
}
