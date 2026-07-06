"use client";

import Link from "next/link";
import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [emailNotVerified, setEmailNotVerified] = useState(false);
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setEmailNotVerified(false);
    setResent(false);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        // 403 = email non verificata → mostra opzione "rimanda mail"
        if (res.status === 403) {
          setEmailNotVerified(true);
        }
        const msg =
          typeof data.detail === "string"
            ? data.detail
            : data.detail?.message || "Credenziali non valide";
        setError(msg);
        setLoading(false);
        return;
      }
      window.location.href = "/app";
    } catch {
      setError("Errore di connessione. Riprova.");
      setLoading(false);
    }
  }

  async function resendVerification() {
    if (!email) return;
    setResending(true);
    try {
      await fetch("/api/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      setResent(true);
    } catch {
      /* silenzioso — la risposta è comunque sempre 200 lato server */
    } finally {
      setResending(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <Link href="/" className="block text-center mb-8 group">
          <div className="text-5xl mb-2 select-none">📚</div>
          <h1 className="text-3xl font-bold text-[var(--color-accent)] group-hover:text-[var(--color-accent-hover)] transition-colors">
            SnapToon
          </h1>
        </Link>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 bg-[var(--color-bg-elev)] p-8 rounded-xl border border-[var(--color-border)]"
        >
          <h2 className="text-xl font-semibold mb-2">Accedi</h2>

          <div>
            <label
              htmlFor="email"
              className="block text-sm text-[var(--color-fg-muted)] mb-1.5"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm text-[var(--color-fg-muted)] mb-1.5"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            />
          </div>

          {error && (
            <div className="text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 text-red-400">
              <p>{error}</p>
              {emailNotVerified && (
                <div className="mt-2 pt-2 border-t border-red-900/50">
                  {resent ? (
                    <p className="text-green-400">
                      ✅ Se il tuo indirizzo esiste, ti abbiamo mandato una nuova email.
                    </p>
                  ) : (
                    <button
                      type="button"
                      onClick={resendVerification}
                      disabled={resending || !email}
                      className="text-[var(--color-accent)] underline hover:text-[var(--color-accent-hover)] disabled:opacity-40"
                    >
                      {resending ? "Invio in corso..." : "→ Rimandami l'email di verifica"}
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold py-2.5 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Accesso in corso..." : "Accedi"}
          </button>
        </form>

        <p className="text-center text-sm text-[var(--color-fg-muted)] mt-6">
          Non hai un account?{" "}
          <Link href="/register" className="text-[var(--color-accent)] hover:underline">
            Registrati gratis
          </Link>
        </p>
        <p className="text-center mt-3">
          <Link
            href="/"
            className="text-[var(--color-fg-muted)] text-sm hover:text-[var(--color-fg)] transition-colors"
          >
            ← Torna alla home
          </Link>
        </p>
      </div>
    </main>
  );
}
