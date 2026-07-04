"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { apiFetch } from "@/lib/api";

/** Lightbox fullscreen: mostra l'immagine a dimensione reale (max 96vw x 92vh).
 *  Click sullo sfondo o Escape per chiudere. */
function Lightbox({
  src,
  alt,
  onClose,
}: {
  src: string;
  alt: string;
  onClose: () => void;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);
  if (!mounted) return null;
  return createPortal(
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background: "rgba(3, 6, 12, 0.92)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        cursor: "zoom-out",
      }}
    >
      <button
        onClick={onClose}
        aria-label="Chiudi"
        style={{
          position: "absolute",
          top: 20,
          right: 24,
          width: 44,
          height: 44,
          borderRadius: 999,
          border: "1px solid rgba(255,255,255,0.18)",
          background: "rgba(15,20,32,0.7)",
          color: "#F1F5F9",
          fontSize: 22,
          cursor: "pointer",
        }}
      >
        ✕
      </button>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: "min(96vw, 1600px)",
          maxHeight: "92vh",
          objectFit: "contain",
          borderRadius: 12,
          boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
          cursor: "default",
        }}
      />
    </div>,
    document.body,
  );
}

interface Preset {
  id: string;
  label: string;
  category: string;
  has_sample_pro: boolean;
  has_sample_kids: boolean;
}

interface TestImage {
  id: string;
  style_preset_id: string;
  prompt: string;
  scene_params: {
    shot_distance?: string | null;
    shot_angle?: string | null;
    mood?: string | null;
  };
  quality: string;
  aspect_ratio: string;
  is_sample_pro: boolean;
  is_sample_kids: boolean;
  notes: string;
  image_url: string;
  created_at: string;
}

interface SceneOption {
  key: string;
  label: string;
}
interface SceneOptions {
  shot_distances: SceneOption[];
  shot_angles: SceneOption[];
  moods: SceneOption[];
  aspect_ratios: SceneOption[];
}

const QUALITIES = ["low", "medium", "high"];

export default function AdminStyleTestPage() {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [images, setImages] = useState<TestImage[]>([]);
  const [scene, setScene] = useState<SceneOptions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Filter
  const [filterPreset, setFilterPreset] = useState<string>("");
  // Lightbox: URL immagine attualmente ingrandita
  const [zoomed, setZoomed] = useState<{ src: string; alt: string } | null>(
    null,
  );

  // Form state
  const [selectedPreset, setSelectedPreset] = useState<string>("");
  const [prompt, setPrompt] = useState("");
  const [shotDistance, setShotDistance] = useState("");
  const [shotAngle, setShotAngle] = useState("");
  const [mood, setMood] = useState("");
  const [aspectRatio, setAspectRatio] = useState("1_1");
  const [quality, setQuality] = useState("medium");
  const [reference, setReference] = useState<File | null>(null);

  async function loadPresets() {
    try {
      const d = await apiFetch<{ presets: Preset[] }>(
        "/api/admin/style-test/presets",
      );
      setPresets(d.presets);
      if (!selectedPreset && d.presets.length > 0) {
        setSelectedPreset(d.presets[0].id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function loadImages() {
    try {
      const q = filterPreset ? `?style_preset_id=${filterPreset}` : "";
      const d = await apiFetch<{ images: TestImage[] }>(
        `/api/admin/style-test/images${q}`,
      );
      setImages(d.images);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function loadScene() {
    try {
      const d = await apiFetch<SceneOptions>("/api/scene-options");
      setScene(d);
    } catch {
      // Non fatale
    }
  }

  useEffect(() => {
    loadPresets();
    loadScene();
  }, []);

  useEffect(() => {
    loadImages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterPreset]);

  const grouped = useMemo(() => {
    const g: Record<string, Preset[]> = {};
    for (const p of presets) {
      (g[p.category] ||= []).push(p);
    }
    return g;
  }, [presets]);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedPreset || !prompt.trim()) {
      setError("Prompt e stile obbligatori");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      // Tutti i campi vanno nel multipart body (insieme al reference),
      // altrimenti l'endpoint FastAPI li ignora e usa i default.
      const formData = new FormData();
      formData.append("style_preset_id", selectedPreset);
      formData.append("prompt", prompt);
      formData.append("shot_distance", shotDistance || "");
      formData.append("shot_angle", shotAngle || "");
      formData.append("mood", mood || "");
      formData.append("aspect_ratio", aspectRatio);
      formData.append("quality", quality);
      if (reference) formData.append("reference", reference);

      const res = await fetch("/api/admin/style-test/generate", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      // Reset (mantengo preset selezionato e prompt per iterare facilmente)
      setReference(null);
      await Promise.all([loadImages(), loadPresets()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function assignSample(imageId: string, flow: "pro" | "kids") {
    try {
      await apiFetch(`/api/admin/style-test/images/${imageId}/assign-sample`, {
        method: "POST",
        body: JSON.stringify({ flow }),
      });
      await Promise.all([loadImages(), loadPresets()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function unassignSample(imageId: string, flow: "pro" | "kids") {
    try {
      await apiFetch(
        `/api/admin/style-test/images/${imageId}/unassign-sample`,
        {
          method: "POST",
          body: JSON.stringify({ flow }),
        },
      );
      await Promise.all([loadImages(), loadPresets()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function deleteImage(imageId: string) {
    if (!confirm("Eliminare questo test?")) return;
    try {
      const res = await fetch(`/api/admin/style-test/images/${imageId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await Promise.all([loadImages(), loadPresets()]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-4">
        <Link
          href="/app/admin"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Pannello admin
        </Link>
      </div>

      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-1">🎨 Test-Style</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          Genera immagini di prova per gli stili preset. Assegna una card
          come &quot;sample&quot; per far vedere agli utenti come appare
          uno stile nel wizard (KIDS o Pro).
        </p>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6">
        {/* Form colonna sinistra */}
        <form
          onSubmit={handleGenerate}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 space-y-3 h-fit"
        >
          <h2 className="font-semibold text-lg mb-1">📝 Nuovo test</h2>
          <p className="text-xs text-[var(--color-fg-muted)] mb-2">
            Costo: 1 credito (medium) — 4 crediti (high).
          </p>

          <div>
            <label className="block text-xs font-semibold mb-1">Stile *</label>
            <select
              value={selectedPreset}
              onChange={(e) => setSelectedPreset(e.target.value)}
              required
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
            >
              {Object.entries(grouped).map(([cat, list]) => (
                <optgroup key={cat} label={cat}>
                  {list.map((p) => {
                    const flags = [
                      p.has_sample_pro ? "PRO" : "",
                      p.has_sample_kids ? "KIDS" : "",
                    ]
                      .filter(Boolean)
                      .join("+");
                    return (
                      <option key={p.id} value={p.id}>
                        {p.label} {flags && `[${flags}]`}
                      </option>
                    );
                  })}
                </optgroup>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1">
              Prompt / soggetto *
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              required
              rows={4}
              placeholder="Es. Bea l'illustratrice sorride tenendo un pennello, sfondo studio creativo."
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm resize-none"
            />
          </div>

          {scene && (
            <>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-semibold mb-1">
                    Distanza
                  </label>
                  <select
                    value={shotDistance}
                    onChange={(e) => setShotDistance(e.target.value)}
                    className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                  >
                    <option value="">— libera —</option>
                    {scene.shot_distances.map((o) => (
                      <option key={o.key} value={o.key}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">
                    Angolo
                  </label>
                  <select
                    value={shotAngle}
                    onChange={(e) => setShotAngle(e.target.value)}
                    className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                  >
                    <option value="">— libero —</option>
                    {scene.shot_angles.map((o) => (
                      <option key={o.key} value={o.key}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Mood</label>
                  <select
                    value={mood}
                    onChange={(e) => setMood(e.target.value)}
                    className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                  >
                    <option value="">— libero —</option>
                    {scene.moods.map((o) => (
                      <option key={o.key} value={o.key}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">
                    Formato
                  </label>
                  <select
                    value={aspectRatio}
                    onChange={(e) => setAspectRatio(e.target.value)}
                    className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                  >
                    {scene.aspect_ratios.map((o) => (
                      <option key={o.key} value={o.key}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold mb-1">Qualità</label>
            <select
              value={quality}
              onChange={(e) => setQuality(e.target.value)}
              className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
            >
              {QUALITIES.map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold mb-1">
              Reference personaggio (facoltativo)
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setReference(e.target.files?.[0] || null)}
              className="w-full text-sm"
            />
            {reference && (
              <p className="text-xs text-[var(--color-fg-muted)] mt-1">
                {reference.name} ({Math.round(reference.size / 1024)} KB)
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={busy || !selectedPreset || !prompt.trim()}
            className="w-full bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2.5 rounded disabled:opacity-50"
          >
            {busy ? "Genero..." : "✨ Genera test"}
          </button>
        </form>

        {/* Gallery colonna destra */}
        <div>
          <div className="flex items-center justify-between mb-3 gap-3 flex-wrap">
            <h2 className="font-semibold text-lg">
              🖼 Galleria ({images.length})
            </h2>
            <select
              value={filterPreset}
              onChange={(e) => setFilterPreset(e.target.value)}
              className="text-sm px-2 py-1.5 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded"
            >
              <option value="">— tutti gli stili —</option>
              {presets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {images.length === 0 ? (
            <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
              <div className="text-4xl mb-3 opacity-30">🎨</div>
              <p className="text-[var(--color-fg-muted)] text-sm">
                Nessun test generato.
                {filterPreset && " Nessun test per questo stile."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {images.map((img) => {
                const preset = presets.find(
                  (p) => p.id === img.style_preset_id,
                );
                return (
                  <div
                    key={img.id}
                    className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg overflow-hidden"
                  >
                    <button
                      type="button"
                      onClick={() =>
                        setZoomed({ src: img.image_url, alt: img.prompt })
                      }
                      title="Zoom a dimensione reale"
                      style={{
                        display: "block",
                        width: "100%",
                        padding: 0,
                        border: "none",
                        background: "#0D1017",
                        cursor: "zoom-in",
                        position: "relative",
                      }}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={img.image_url}
                        alt={img.prompt}
                        loading="lazy"
                        // object-contain + max-height mantiene la griglia
                        // ordinata ma NON crop l'immagine: portrait 2:3,
                        // landscape 3:2 ecc. si vedono intere.
                        style={{
                          width: "100%",
                          maxHeight: 360,
                          objectFit: "contain",
                          display: "block",
                        }}
                      />
                      <span
                        aria-hidden
                        style={{
                          position: "absolute",
                          bottom: 8,
                          right: 8,
                          width: 28,
                          height: 28,
                          borderRadius: 999,
                          background: "rgba(3,6,12,0.75)",
                          border: "1px solid rgba(255,255,255,0.15)",
                          color: "#F1F5F9",
                          fontSize: 13,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                        }}
                      >
                        🔍
                      </span>
                    </button>
                    <div className="p-3">
                      <div className="flex items-center gap-1 mb-2 flex-wrap">
                        <span className="text-[10px] font-bold uppercase tracking-wide text-[var(--color-fg-muted)]">
                          {preset?.label || img.style_preset_id}
                        </span>
                        {img.is_sample_pro && (
                          <span className="text-[9px] font-bold bg-blue-900/40 text-blue-300 border border-blue-700/50 rounded px-1.5 py-0.5">
                            SAMPLE PRO
                          </span>
                        )}
                        {img.is_sample_kids && (
                          <span className="text-[9px] font-bold bg-purple-900/40 text-purple-300 border border-purple-700/50 rounded px-1.5 py-0.5">
                            SAMPLE KIDS
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[var(--color-fg-muted)] line-clamp-2 mb-2 leading-relaxed">
                        {img.prompt}
                      </p>
                      <div className="text-[10px] text-[var(--color-fg-muted)] mb-3 space-y-0.5">
                        {img.scene_params.shot_distance && (
                          <div>📷 {img.scene_params.shot_distance}</div>
                        )}
                        {img.scene_params.mood && (
                          <div>🎭 {img.scene_params.mood}</div>
                        )}
                        <div>
                          🖼 {img.aspect_ratio} · {img.quality}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-1 mb-1">
                        {img.is_sample_pro ? (
                          <button
                            onClick={() => unassignSample(img.id, "pro")}
                            className="text-[10px] bg-blue-900/40 hover:bg-blue-900/60 text-blue-300 px-2 py-1 rounded border border-blue-700/50"
                          >
                            ✕ Rimuovi PRO
                          </button>
                        ) : (
                          <button
                            onClick={() => assignSample(img.id, "pro")}
                            className="text-[10px] border border-[var(--color-border)] hover:border-blue-500 text-[var(--color-fg-muted)] hover:text-blue-300 px-2 py-1 rounded"
                          >
                            📖 Sample PRO
                          </button>
                        )}
                        {img.is_sample_kids ? (
                          <button
                            onClick={() => unassignSample(img.id, "kids")}
                            className="text-[10px] bg-purple-900/40 hover:bg-purple-900/60 text-purple-300 px-2 py-1 rounded border border-purple-700/50"
                          >
                            ✕ Rimuovi KIDS
                          </button>
                        ) : (
                          <button
                            onClick={() => assignSample(img.id, "kids")}
                            className="text-[10px] border border-[var(--color-border)] hover:border-purple-500 text-[var(--color-fg-muted)] hover:text-purple-300 px-2 py-1 rounded"
                          >
                            ⭐ Sample KIDS
                          </button>
                        )}
                      </div>
                      <button
                        onClick={() => deleteImage(img.id)}
                        className="w-full text-[10px] text-[var(--color-fg-muted)] hover:text-red-400 py-1"
                      >
                        🗑 Elimina
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {zoomed && (
        <Lightbox
          src={zoomed.src}
          alt={zoomed.alt}
          onClose={() => setZoomed(null)}
        />
      )}
    </div>
  );
}
