"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import {
  apiFetch,
  type KidsProjectDetails,
} from "@/lib/api";

export default function KidsPreviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [details, setDetails] = useState<KidsProjectDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Refresh-tag per forzare ricarica immagini dopo rigenerazione
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<KidsProjectDetails>(
        `/api/kids/projects/${id}/details`
      );
      setDetails(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function downloadPdf() {
    setDownloadingPdf(true);
    setError(null);
    try {
      const res = await fetch(`/api/kids/projects/${id}/pdf`, {
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Errore PDF (HTTP ${res.status})`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeName = (details?.name || "libretto")
        .replace(/[^a-z0-9]+/gi, "-")
        .toLowerCase();
      a.download = `snaptoon-kids-${safeName}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDownloadingPdf(false);
    }
  }

  if (details === null && !error) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento libretto...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <Link
          href="/app/kids"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Tutti i libretti
        </Link>
        <p className="text-red-400 mt-4">{error}</p>
      </div>
    );
  }

  if (!details) return null;

  // Se non ha storia → invita a generare
  if (!details.has_story) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <Link
          href="/app/kids"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Tutti i libretti
        </Link>
        <h1 className="text-2xl font-bold my-4">{details.name}</h1>
        <p className="text-[var(--color-fg-muted)] mb-6">
          La storia non è ancora stata generata.
        </p>
        <Link
          href={`/app/kids/${id}/story`}
          className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg transition-colors"
        >
          ✨ Genera la storia
        </Link>
      </div>
    );
  }

  // Mappa per veloce lookup vignette
  const vigSet = new Set(
    details.vignettes.map((v) => `${v.page_number}_${v.panel_number}`)
  );
  const totalPanels = details.story?.pages.reduce(
    (s, p) => s + p.panels.length,
    0
  ) ?? 0;
  const completed = details.vignettes.length;
  const allGenerated = completed >= totalPanels && details.has_cover;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-4">
        <Link
          href="/app/kids"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Tutti i libretti
        </Link>
      </div>

      <header className="mb-8 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold mb-1">📖 {details.name}</h1>
          {details.story && (
            <p className="text-[var(--color-fg-muted)] italic">
              "{details.story.logline}"
            </p>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          <Link
            href={`/app/kids/${id}/personaggi`}
            className="border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-4 py-2.5 rounded-lg transition-colors"
          >
            👥 Personaggi
          </Link>
          <Link
            href={`/app/kids/${id}/story`}
            className="border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-4 py-2.5 rounded-lg transition-colors"
          >
            📖 Storia
          </Link>
          <button
            onClick={downloadPdf}
            disabled={
              downloadingPdf || (!details.has_cover && details.vignettes.length === 0)
            }
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
            title={
              !details.has_cover && details.vignettes.length === 0
                ? "Genera almeno la cover o una vignetta"
                : "Scarica il libretto in PDF"
            }
          >
            {downloadingPdf ? "Genero PDF..." : "📥 Scarica PDF"}
          </button>
        </div>
      </header>

      {!allGenerated && (
        <div className="bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/30 rounded-xl p-5 mb-6 flex items-center justify-between gap-4">
          <div>
            <p className="font-medium mb-1">
              Generazione incompleta ({completed}/{totalPanels} vignette
              {!details.has_cover && " + cover mancante"})
            </p>
            <p className="text-sm text-[var(--color-fg-muted)]">
              Riprendi la pipeline per generare quel che manca.
            </p>
          </div>
          <Link
            href={`/app/kids/${id}/generate`}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg whitespace-nowrap"
          >
            Continua →
          </Link>
        </div>
      )}

      {/* Cover */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-3">📕 Copertina</h2>
        {details.has_cover ? (
          <img
            src={`/api/kids/projects/${id}/images/cover?t=${refreshTag}`}
            alt="Cover"
            className="rounded-xl max-w-md w-full border border-[var(--color-border)]"
          />
        ) : (
          <div className="bg-[var(--color-bg-elev)] border border-dashed border-[var(--color-border)] rounded-xl p-12 text-center max-w-md">
            <p className="text-[var(--color-fg-muted)]">
              Copertina non ancora generata
            </p>
          </div>
        )}
      </section>

      {/* Vignette per pagina */}
      <section>
        <h2 className="text-lg font-semibold mb-4">
          🖼 Vignette ({completed}/{totalPanels})
        </h2>
        <div className="space-y-8">
          {details.story?.pages.map((p) => (
            <div key={p.number}>
              <h3 className="text-sm font-medium text-[var(--color-fg-muted)] mb-3">
                Pagina {p.number}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {p.panels.map((pn) => {
                  const isGenerated = vigSet.has(`${p.number}_${pn.number}`);
                  return (
                    <div
                      key={pn.number}
                      className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg overflow-hidden"
                    >
                      {isGenerated ? (
                        <img
                          src={`/api/kids/projects/${id}/images/panel/${p.number}/${pn.number}?t=${refreshTag}`}
                          alt={`P${p.number}V${pn.number}`}
                          className="w-full aspect-square object-cover"
                        />
                      ) : (
                        <div className="w-full aspect-square flex items-center justify-center bg-[var(--color-bg)]">
                          <p className="text-xs text-[var(--color-fg-muted)]">
                            Non generata
                          </p>
                        </div>
                      )}
                      <div className="px-2 py-1.5 text-xs text-center text-[var(--color-fg-muted)]">
                        P{p.number}V{pn.number}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer con secondo bottone download PDF (utile per libretti lunghi) */}
      {(details.has_cover || details.vignettes.length > 0) && (
        <div className="mt-10 flex justify-center">
          <button
            onClick={downloadPdf}
            disabled={downloadingPdf}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-3 rounded-lg disabled:opacity-50"
          >
            {downloadingPdf ? "Genero PDF..." : "📥 Scarica il libretto in PDF"}
          </button>
        </div>
      )}
    </div>
  );
}
