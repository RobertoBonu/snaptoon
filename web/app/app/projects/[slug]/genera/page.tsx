"use client";

import { use, useEffect, useState } from "react";
import {
  apiFetch,
  type SceneOptions,
  type VignetteStatus,
  type VignettesList,
} from "@/lib/api";

export default function GeneraPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [vignettes, setVignettes] = useState<VignetteStatus[] | null>(null);
  const [opts, setOpts] = useState<SceneOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<string | null>(null);
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  async function load() {
    try {
      setError(null);
      const [vs, sc] = await Promise.all([
        apiFetch<VignettesList>(`/api/projects/${slug}/vignettes`),
        apiFetch<SceneOptions>("/api/scene-options"),
      ]);
      setVignettes(vs.vignettes);
      setOpts(sc);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function generate(
    v: VignetteStatus,
    overrides: {
      shot_distance?: string | null;
      shot_angle?: string | null;
      mood?: string | null;
      aspect_ratio?: string;
      quality?: string;
    } = {}
  ) {
    const key = `${v.page_number}_${v.panel_number}`;
    setGenerating(key);
    setError(null);
    try {
      await apiFetch(
        `/api/projects/${slug}/vignettes/${v.page_number}/${v.panel_number}/generate`,
        {
          method: "POST",
          body: JSON.stringify({
            shot_distance: overrides.shot_distance ?? v.shot_distance ?? null,
            shot_angle: overrides.shot_angle ?? v.shot_angle ?? null,
            mood: overrides.mood ?? v.mood ?? null,
            aspect_ratio: overrides.aspect_ratio ?? v.aspect_ratio_key ?? "2_3",
            quality: overrides.quality ?? "medium",
          }),
        }
      );
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(null);
    }
  }

  if (vignettes === null && !error) {
    return <p className="text-[var(--color-fg-muted)]">Caricamento...</p>;
  }

  if (vignettes && vignettes.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">🖼 Genera</h1>
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <p className="text-[var(--color-fg-muted)]">
            Nessuna vignetta da generare. Adatta prima la sceneggiatura nella
            tab <strong>📝 Testo</strong>.
          </p>
        </div>
      </div>
    );
  }

  // Raggruppa per pagina
  const byPage = new Map<number, VignetteStatus[]>();
  for (const v of vignettes ?? []) {
    if (!byPage.has(v.page_number)) byPage.set(v.page_number, []);
    byPage.get(v.page_number)!.push(v);
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">🖼 Genera vignette</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-6">
        Per ogni vignetta scegli scena (inquadratura, angolo, mood, formato) e
        genera l'immagine. Balloon disegnato dall'AI. Costo: 1 cr (medium).
      </p>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      <div className="space-y-8">
        {Array.from(byPage.entries()).map(([pageNum, panels]) => (
          <section key={pageNum}>
            <h2 className="text-lg font-semibold mb-3">Pagina {pageNum}</h2>
            <div className="space-y-3">
              {panels.map((v) => (
                <VignetteEditor
                  key={`${v.page_number}_${v.panel_number}`}
                  v={v}
                  slug={slug}
                  opts={opts}
                  generating={
                    generating === `${v.page_number}_${v.panel_number}`
                  }
                  onGenerate={(overrides) => generate(v, overrides)}
                  refreshTag={refreshTag}
                />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function VignetteEditor({
  v,
  slug,
  opts,
  generating,
  onGenerate,
  refreshTag,
}: {
  v: VignetteStatus;
  slug: string;
  opts: SceneOptions | null;
  generating: boolean;
  onGenerate: (overrides: {
    shot_distance?: string | null;
    shot_angle?: string | null;
    mood?: string | null;
    aspect_ratio?: string;
    quality?: string;
  }) => Promise<void>;
  refreshTag: number;
}) {
  const [sd, setSd] = useState<string>(v.shot_distance ?? "");
  const [sa, setSa] = useState<string>(v.shot_angle ?? "");
  const [md, setMd] = useState<string>(v.mood ?? "");
  const [ar, setAr] = useState<string>(v.aspect_ratio_key ?? "2_3");
  const [qual, setQual] = useState<string>("medium");

  return (
    <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden">
      <div className="flex gap-4 p-4">
        {/* Image preview */}
        <div className="w-40 flex-shrink-0 bg-[var(--color-bg)] border border-[var(--color-border)] rounded">
          {v.generated ? (
            <img
              src={`/api/projects/${slug}/vignettes/${v.page_number}/${v.panel_number}/image?t=${refreshTag}`}
              alt={`P${v.page_number}V${v.panel_number}`}
              className="w-full h-full object-cover aspect-square rounded"
            />
          ) : (
            <div className="w-full h-full aspect-square flex items-center justify-center text-xs text-[var(--color-fg-muted)] px-2 text-center">
              Non generata
            </div>
          )}
        </div>

        {/* Info + controls */}
        <div className="flex-1 min-w-0">
          <div className="text-xs text-[var(--color-fg-muted)] mb-1">
            Pagina {v.page_number} · Vignetta {v.panel_number}
          </div>
          <p className="text-sm mb-2 line-clamp-2">{v.description}</p>
          {v.dialogue_text && (
            <p className="text-sm text-[var(--color-accent)] italic mb-3">
              💬{" "}
              {v.dialogue_speaker && <strong>{v.dialogue_speaker}: </strong>}
              "{v.dialogue_text}"
            </p>
          )}

          {/* Scene controls compatte */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs mb-3">
            <select
              value={sd}
              onChange={(e) => setSd(e.target.value)}
              className="px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            >
              <option value="">— Distanza —</option>
              {opts?.shot_distances.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
            <select
              value={sa}
              onChange={(e) => setSa(e.target.value)}
              className="px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            >
              <option value="">— Angolo —</option>
              {opts?.shot_angles.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
            <select
              value={md}
              onChange={(e) => setMd(e.target.value)}
              className="px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            >
              <option value="">— Mood —</option>
              {opts?.moods.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
            <select
              value={ar}
              onChange={(e) => setAr(e.target.value)}
              className="px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            >
              {opts?.aspect_ratios.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
            <select
              value={qual}
              onChange={(e) => setQual(e.target.value)}
              className="px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <button
            onClick={() =>
              onGenerate({
                shot_distance: sd || null,
                shot_angle: sa || null,
                mood: md || null,
                aspect_ratio: ar,
                quality: qual,
              })
            }
            disabled={generating}
            className="text-sm bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-medium px-4 py-1.5 rounded disabled:opacity-50"
          >
            {generating
              ? "Genero..."
              : v.generated
                ? "🔄 Rigenera"
                : "✨ Genera"}
          </button>
        </div>
      </div>
    </div>
  );
}
