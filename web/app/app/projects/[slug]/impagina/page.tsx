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
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

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
      setRefreshTag(Date.now());
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
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function renderPage(pageNum: number) {
    setRendering(pageNum);
    setError(null);
    try {
      // Forza render lato server (e cacha su storage)
      await fetch(`/api/projects/${slug}/pages/${pageNum}/render`, {
        credentials: "include",
      });
      setRefreshTag(Date.now());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRendering(null);
    }
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
      <header className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1">📐 Impagina</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Scegli grid e balloon per ogni pagina, esporta PDF.
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
        {pages?.map((p) => (
          <div
            key={p.page_number}
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5"
          >
            <div className="flex gap-6">
              {/* Preview render */}
              <div className="w-64 flex-shrink-0">
                <img
                  src={`/api/projects/${slug}/pages/${p.page_number}/render?t=${refreshTag}`}
                  alt={`Pagina ${p.page_number}`}
                  className="w-full rounded border border-[var(--color-border)]"
                />
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
                      Mostra balloon overlay (PIL)
                    </label>
                  </div>

                  <button
                    onClick={() => renderPage(p.page_number)}
                    disabled={rendering === p.page_number}
                    className="text-sm border border-[var(--color-border)] hover:border-[var(--color-accent)] px-4 py-1.5 rounded transition-colors disabled:opacity-50"
                  >
                    {rendering === p.page_number ? "Render..." : "🔄 Re-render"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
