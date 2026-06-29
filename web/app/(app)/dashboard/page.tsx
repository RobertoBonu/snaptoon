/**
 * Dashboard "I miei progetti".
 *
 * Pagina autenticata (verrà protetta da middleware Next.js nei prossimi
 * commit). Per ora: skeleton con check auth lato client.
 *
 * Fase 2 della migrazione: connessione a /api/projects, grid, CRUD.
 */
"use client";

import { useEffect, useState } from "react";

interface User {
  id: string;
  email: string;
  role: string;
  is_admin: boolean;
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/auth/me", { credentials: "include" })
      .then((r) => {
        if (!r.ok) {
          window.location.href = "/login";
          return null;
        }
        return r.json();
      })
      .then((data) => {
        if (data) setUser(data);
        setLoading(false);
      })
      .catch(() => {
        window.location.href = "/login";
      });
  }, []);

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    window.location.href = "/";
  }

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-8">
      <header className="flex justify-between items-center mb-12">
        <h1 className="text-3xl font-bold text-[var(--color-accent)]">
          📚 SnapToon
        </h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-[var(--color-fg-muted)]">
            {user?.email}
          </span>
          <button
            onClick={handleLogout}
            className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors"
          >
            Esci
          </button>
        </div>
      </header>

      <h2 className="text-2xl font-bold mb-2">I miei progetti</h2>
      <p className="text-[var(--color-fg-muted)] mb-8">
        Benvenuto, <span className="text-[var(--color-fg)]">{user?.email}</span>.
        Ruolo: <span className="text-[var(--color-accent)]">{user?.role}</span>.
      </p>

      <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
        <p className="text-[var(--color-fg-muted)] mb-2">
          Dashboard progetti in costruzione.
        </p>
        <p className="text-sm text-[var(--color-fg-muted)] opacity-60">
          Fase 2 della migrazione — arriva nella prossima settimana.
        </p>
      </div>
    </main>
  );
}
