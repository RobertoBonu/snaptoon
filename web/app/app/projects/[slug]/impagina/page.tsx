"use client";

import PageLoader from "@/components/PageLoader";

import { use, useEffect, useState } from "react";
import { apiFetch, type PageInfo, type PagesList } from "@/lib/api";

export default function ImpaginaPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [pages, setPages] = useState<PageInfo[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rendering, setRendering] = useState<number | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [refreshTag, setRefreshTag] = useState<Record<number, number>>({});
  // Toggle preview per pagina: se true, mostra il render; se false, mostra
  // placeholder "Preview non generata" con bottone "Genera preview".
  // Default false → l'utente sceglie quando calcolare il render (più
  // esplicito rispetto al caricamento auto della V2 originale).
  const [previewOn, setPreviewOn] = useState<Record<number, boolean>>({});

  async function load() {
    try {
      setError(null);
      const data = await apiFetch<PagesList>(`/api/projects/${slug}/pages`);
      setPages(data.pages);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function setGrid(pageNum: number, grid: string) {
    try {
      await apiFetch(`/api/projects/${slug}/pages/${pageNum}/grid`, {
        method: "PATCH",
        body: JSON.stringify({ grid_id: grid }),
      });
      // Se la preview era attiva, invalida la vecchia
      if (previewOn[pageNum]) {
        setRefreshTag((prev) => ({ ...prev, [pageNum]: Date.now() }));
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function setBalloons(pageNum: number, show: boolean) {
    try {
      await apiFetch(`/api/projects/${slug}/pages/${pageNum}/balloons`, {
        method: "PATCH",
        body: JSON.stringify({ show_balloons: show }),
      });
      if (previewOn[pageNum]) {
        setRefreshTag((prev) => ({ ...prev, [pageNum]: Date.now() }));
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function generatePreview(pageNum: number) {
    setRendering(pageNum);
    setError(null);
    try {
      const res = await fetch(
        `/api/projects/${slug}/pages/${pageNum}/render`,
        { credentials: "include" }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Errore render pagina ${pageNum}`);
      }
      setRefreshTag((prev) => ({ ...prev, [pageNum]: Date.now() }));
      setPreviewOn((prev) => ({ ...prev, [pageNum]: true }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRendering(null);
    }
  }

  function togglePreview(pageNum: number) {
    setPreviewOn((prev) => ({ ...prev, [pageNum]: !prev[pageNum] }));
  }

  async function downloadPdf() {
    setDownloading(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${slug}/pdf`, {
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Errore PDF");
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `snaptoon_${slug}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDownloading(false);
    }
  }

  if (pages === null && !error) {
    return <PageLoader message="Carico le pagine..." />;
  }

  if (pages && pages.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-4">📐 Impagina</h1>
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <p className="text-[var(--color-fg-muted)]">
            Nessuna pagina. Adatta prima la sceneggiatura.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <header className="flex justify-between items-start mb-6 gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold mb-1">📐 Impagina</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Scegli grid e balloon per ogni pagina, poi genera l'anteprima
            quando sei pronto.
          </p>
        </div>
        <button
          onClick={downloadPdf}
          disabled={downloading}
          className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg disabled:opacity-50"
        >
          {downloading ? "Genero PDF..." : "📥 Scarica PDF"}
        </button>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      <div className="space-y-6">
        {pages?.map((p) => {
          const isPreviewOn = !!previewOn[p.page_number];
          const tag = refreshTag[p.page_number];
          return (
            <div
              key={p.page_number}
              className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5"
            >
              <div className="flex gap-6 flex-col md:flex-row">
                {/* Preview render — on-demand */}
                <div className="w-full md:w-64 flex-shrink-0">
                  {isPreviewOn && tag ? (
                    <div className="relative group">
                      <img
                        src={`/api/projects/${slug}/pages/${p.page_number}/render?t=${tag}`}
                        alt={`Pagina ${p.page_number}`}
                        className="w-full rounded border border-[var(--color-border)]"
                      />
                      <button
                        onClick={() => togglePreview(p.page_number)}
                        className="absolute top-2 right-2 bg-[var(--color-bg)]/80 hover:bg-[var(--color-bg)] text-xs px-2 py-1 rounded border border-[var(--color-border)] opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Nascondi anteprima"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <div className="aspect-[2/3] w-full bg-[var(--color-bg)] border border-dashed border-[var(--color-border)] rounded flex flex-col items-center justify-center gap-3 p-4 text-center">
                      <div className="text-4xl opacity-30">📄</div>
                      <p className="text-xs text-[var(--color-fg-muted)]">
                        Anteprima non generata
                      </p>
                      <button
                        onClick={() => generatePreview(p.page_number)}
                        disabled={rendering === p.page_number}
                        className="text-xs bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-medium px-3 py-1.5 rounded transition-colors disabled:opacity-50"
                      >
                        {rendering === p.page_number
                          ? "Genero..."
                          : "👁 Genera anteprima"}
                      </button>
                    </div>
                  )}
                </div>

                {/* Controls */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold mb-3">
                    Pagina {p.page_number}{" "}
                    <span className="text-sm text-[var(--color-fg-muted)] font-normal">
                      ({p.n_panels} vignette)
                    </span>
                  </h3>

                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs text-[var(--color-fg-muted)] mb-1">
                        Layout (gabbia)
                      </label>
                      <select
                        value={p.grid_id}
                        onChange={(e) =>
                          setGrid(p.page_number, e.target.value)
                        }
                        className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                      >
                        {p.available_grids.map((g) => (
                          <option key={g} value={g}>
                            {g}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id={`balloons-${p.page_number}`}
                        checked={p.show_balloons}
                        onChange={(e) =>
                          setBalloons(p.page_number, e.target.checked)
                        }
                        className="w-4 h-4 accent-[var(--color-accent)]"
                      />
                      <label
                        htmlFor={`balloons-${p.page_number}`}
                        className="text-sm"
                      >
                        Disegna balloon come overlay (i balloon dell'AI
                        restano comunque)
                      </label>
                    </div>

                    <div className="flex gap-2 pt-1 flex-wrap">
                      <button
                        onClick={() => generatePreview(p.page_number)}
                        disabled={rendering === p.page_number}
                        className="text-sm border border-[var(--color-border)] hover:border-[var(--color-accent)] px-4 py-1.5 rounded transition-colors disabled:opacity-50"
                      >
                        {rendering === p.page_number
                          ? "Render..."
                          : isPreviewOn
                            ? "🔄 Ri-genera anteprima"
                            : "👁 Genera anteprima"}
                      </button>
                      {isPreviewOn && (
                        <button
                          onClick={() => togglePreview(p.page_number)}
                          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-3 py-1.5"
                        >
                          Nascondi
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Nota per l'utente */}
      <div className="mt-6 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4 text-sm text-[var(--color-fg-muted)]">
        💡 <strong>Come funziona</strong>: prima scegli grid e balloon per
        ciascuna pagina. Quando sei soddisfatto delle impostazioni, click
        "Genera anteprima" per vedere il render. Quando tutte le pagine
        sono a posto, scarica il PDF.
      </div>
    </div>
  );
}
