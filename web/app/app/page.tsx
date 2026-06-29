"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, type Project, type ProjectList } from "@/lib/api";

const LENGTH_LABELS: Record<string, string> = {
  striscia: "Striscia (1 pagina)",
  breve: "Breve (2-5 pagine)",
  medio: "Medio (6-12 pagine)",
  lungo: "Lungo (13+ pagine)",
};

export default function DashboardPage() {
  const [data, setData] = useState<ProjectList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newLength, setNewLength] = useState("medio");
  const [creating, setCreating] = useState(false);

  async function load() {
    try {
      setError(null);
      const res = await apiFetch<ProjectList>("/api/projects");
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const p = await apiFetch<Project>("/api/projects", {
        method: "POST",
        body: JSON.stringify({ title: newTitle, length: newLength }),
      });
      window.location.href = `/app/projects/${p.slug}`;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setCreating(false);
    }
  }

  async function handleDelete(slug: string, title: string) {
    if (!confirm(`Eliminare il progetto "${title}"?`)) return;
    try {
      await apiFetch(`/api/projects/${slug}`, { method: "DELETE" });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  }

  if (data === null && !error) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">I miei progetti</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            {data?.current_count ?? 0}
            {data && data.max_projects > 0 ? ` / ${data.max_projects}` : ""}{" "}
            progetti
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg transition-colors"
        >
          + Nuovo progetto
        </button>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6"
        >
          <h3 className="font-semibold mb-4 text-lg">Nuovo progetto</h3>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Titolo del progetto"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              required
              autoFocus
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)]"
            />
            <select
              value={newLength}
              onChange={(e) => setNewLength(e.target.value)}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-[var(--color-fg)]"
            >
              {Object.entries(LENGTH_LABELS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
            <div className="flex gap-2 pt-1">
              <button
                type="submit"
                disabled={creating || !newTitle.trim()}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded transition-colors disabled:opacity-50"
              >
                {creating ? "Creo..." : "Crea"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreate(false);
                  setNewTitle("");
                }}
                className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-5 py-2 transition-colors"
              >
                Annulla
              </button>
            </div>
          </div>
        </form>
      )}

      {data && data.projects.length === 0 ? (
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <div className="text-5xl mb-4 opacity-30">📚</div>
          <p className="text-[var(--color-fg-muted)] mb-4">
            Non hai ancora progetti.
          </p>
          {!showCreate && (
            <button
              onClick={() => setShowCreate(true)}
              className="text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] font-medium"
            >
              Crea il tuo primo progetto →
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.projects.map((p) => (
            <div
              key={p.id}
              className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 hover:border-[var(--color-accent)]/50 transition-colors group"
            >
              <h3 className="font-semibold text-lg mb-1 truncate">{p.title}</h3>
              <p className="text-xs text-[var(--color-fg-muted)] mb-5">
                {LENGTH_LABELS[p.length_target]?.split(" ")[0] ||
                  p.length_target}{" "}
                · {new Date(p.created_at).toLocaleDateString("it-IT")}
              </p>
              <div className="flex gap-2">
                <Link
                  href={`/app/projects/${p.slug}`}
                  className="flex-1 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] text-center font-medium py-2 rounded transition-colors"
                >
                  Apri
                </Link>
                <button
                  onClick={() => handleDelete(p.slug, p.title)}
                  className="px-3 py-2 text-[var(--color-fg-muted)] hover:text-red-400 hover:bg-red-950/30 rounded transition-colors"
                  title="Elimina"
                  aria-label={`Elimina ${p.title}`}
                >
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
