"use client";

import PageLoader from "@/components/PageLoader";

import { use, useEffect, useMemo, useState } from "react";
import { apiFetch, type Project, type Style, type StyleList } from "@/lib/api";

export default function StilePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [project, setProject] = useState<Project | null>(null);
  const [data, setData] = useState<StyleList | null>(null);
  const [category, setCategory] = useState<string>("");
  const [query, setQuery] = useState<string>("");
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      // Carica project per sapere lo style_id attuale
      const projects = await apiFetch<{ projects: Project[] }>(
        "/api/projects"
      );
      const p = projects.projects.find((x) => x.slug === slug);
      if (!p) {
        setError("Progetto non trovato");
        return;
      }
      setProject(p);

      const url = category
        ? `/api/styles?category=${encodeURIComponent(category)}`
        : "/api/styles";
      const styles = await apiFetch<StyleList>(url);
      setData(styles);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, [category]);

  async function selectStyle(styleId: string) {
    setSaving(styleId);
    setError(null);
    try {
      await apiFetch(`/api/styles/projects/${slug}/style`, {
        method: "PATCH",
        body: JSON.stringify({ style_id: styleId }),
      });
      setProject((prev) => (prev ? { ...prev, style_id: styleId } : null));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(null);
    }
  }

  const filtered = useMemo(() => {
    if (!data) return [];
    if (!query.trim()) return data.styles;
    const q = query.toLowerCase();
    return data.styles.filter(
      (s) =>
        s.label.toLowerCase().includes(q) ||
        s.expansion.toLowerCase().includes(q)
    );
  }, [data, query]);

  if (data === null && !error) {
    return <PageLoader message="Carico gli stili..." />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">🎨 Stile</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-6">
        Scegli lo stile visivo del fumetto. Verrà applicato a personaggi e
        vignette.
      </p>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {/* Filtri */}
      <div className="flex flex-wrap gap-2 mb-6">
        <input
          type="text"
          placeholder="🔍 Cerca stile..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 min-w-[200px] px-3 py-2 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded text-sm focus:outline-none focus:border-[var(--color-accent)]"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="px-3 py-2 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded text-sm focus:outline-none focus:border-[var(--color-accent)]"
        >
          <option value="">Tutte le categorie</option>
          {data?.categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {project?.style_id && (
        <p className="text-sm text-[var(--color-fg-muted)] mb-3">
          Stile attuale:{" "}
          <span className="text-[var(--color-accent)] font-medium">
            {data?.styles.find((s) => s.id === project.style_id)?.label ||
              project.style_id}
          </span>
        </p>
      )}

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((s) => {
          const selected = project?.style_id === s.id;
          return (
            <button
              key={s.id}
              onClick={() => selectStyle(s.id)}
              disabled={saving === s.id}
              className={`text-left p-4 rounded-xl border transition-all ${
                selected
                  ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5"
                  : "border-[var(--color-border)] bg-[var(--color-bg-elev)] hover:border-[var(--color-accent)]/50"
              } ${saving === s.id ? "opacity-50" : ""}`}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="font-medium">{s.label}</div>
                {selected && (
                  <span className="text-xs text-[var(--color-accent)]">✓</span>
                )}
              </div>
              <div className="text-xs text-[var(--color-fg-muted)] mb-2 uppercase tracking-wider">
                {s.category}
              </div>
              <p className="text-xs text-[var(--color-fg-muted)] line-clamp-3">
                {s.expansion.slice(0, 200)}
                {s.expansion.length > 200 ? "..." : ""}
              </p>
            </button>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-[var(--color-fg-muted)] py-8">
          Nessuno stile corrisponde alla ricerca.
        </p>
      )}
    </div>
  );
}
