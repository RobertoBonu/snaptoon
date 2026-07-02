"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, type KidsProject } from "@/lib/api";

// Mapping style → colore badge (uno per ogni stile KIDS)
const STYLE_BADGE: Record<string, { emoji: string; color: string; label: string }> = {
  bold_toddler_graphic: { emoji: "🎨", color: "#F59E0B", label: "Flat" },
  illumination_cartoon_style: { emoji: "🎭", color: "#8B5CF6", label: "3D" },
  japanese_preschool_anime: { emoji: "🌸", color: "#EC4899", label: "Manga" },
  chibi_kawaii_emotions: { emoji: "🥰", color: "#F472B6", label: "Chibi" },
  cartoon_superhero_kids: { emoji: "🦸", color: "#3B82F6", label: "Supereroi" },
  enchanted_fairytale_princess: { emoji: "👑", color: "#A78BFA", label: "Fiaba" },
};

export default function KidsDashboardPage() {
  const [projects, setProjects] = useState<KidsProject[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const data = await apiFetch<{ projects: KidsProject[] }>(
        "/api/kids/projects"
      );
      setProjects(data.projects);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Eliminare il libretto "${name}"?`)) return;
    try {
      await apiFetch(`/api/kids/projects/${id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  }

  if (projects === null && !error) {
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
          <h1 className="text-3xl font-bold mb-1">⭐ I miei libretti</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            {projects?.length ?? 0} libretti
          </p>
        </div>
        <Link
          href="/app/kids/new"
          className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg transition-colors"
        >
          + Nuovo libretto
        </Link>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {projects && projects.length === 0 ? (
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <div className="text-5xl mb-4 opacity-30">📕</div>
          <p className="text-[var(--color-fg-muted)] mb-4">
            Non hai ancora libretti.
          </p>
          <Link
            href="/app/kids/new"
            className="text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] font-medium"
          >
            Crea il tuo primo libretto →
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects?.map((p) => {
            const badge = STYLE_BADGE[p.style_id ?? ""] ?? {
              emoji: "📕",
              color: "#F59E0B",
              label: "Kids",
            };
            return (
              <div
                key={p.id}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden group hover:border-[var(--color-accent)]/50 transition-colors"
              >
                {/* Cover placeholder (Sett. 4 → cover reale dall'AI) */}
                <div
                  className="aspect-[2/3] flex flex-col items-center justify-center gap-3"
                  style={{
                    background: `linear-gradient(135deg, ${badge.color}22 0%, #161B26 100%)`,
                    borderBottom: `1px solid ${badge.color}40`,
                  }}
                >
                  <div className="text-6xl">📕</div>
                  <div
                    className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider"
                    style={{ background: badge.color, color: "#0D1017" }}
                  >
                    {badge.emoji} {badge.label}
                  </div>
                </div>

                <div className="p-4">
                  <h3 className="font-semibold truncate mb-1">{p.name}</h3>
                  <p className="text-xs text-[var(--color-fg-muted)] mb-3">
                    {new Date(p.created_at).toLocaleDateString("it-IT")}
                  </p>
                  <div className="flex gap-2">
                    <Link
                      href={`/app/kids/${p.id}`}
                      className="flex-1 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] text-center text-sm font-medium py-2 rounded transition-colors"
                    >
                      Apri
                    </Link>
                    <button
                      onClick={() => handleDelete(p.id, p.name)}
                      className="px-3 py-2 text-[var(--color-fg-muted)] hover:text-red-400 hover:bg-red-950/30 rounded transition-colors text-sm"
                      title="Elimina"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
