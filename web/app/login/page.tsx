"use client";

import Link from "next/link";
import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Credenziali non valide");
        setLoading(false);
        return;
      }
      // Redirect a dashboard
      window.location.href = "/app";
    } catch {
      setError("Errore di connessione. Riprova.");
      setLoading(false);
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
            <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold py-2.5 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Accesso in corso..." : "Accedi"}
          </button>
        </form>

        <p className="text-center mt-6">
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
