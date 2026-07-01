"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { apiFetch, type KidsProjectDetails } from "@/lib/api";

/**
 * Generazione KIDS step-by-step:
 *   1. Genera la COPERTINA. Attesa 30-45s.
 *   2. Cover pronta → utente decide se continuare.
 *   3. Genera pagina 1. Attesa 30-90s (dipende da quante vignette).
 *   4. Pagina 1 pronta → utente decide se continuare.
 *   5. E così via fino all'ultima pagina.
 *
 * Vantaggi rispetto alla pipeline SSE precedente:
 *   - L'utente vede risultati subito dopo il primo passo (cover in 30s)
 *   - Può fermarsi in qualsiasi momento e riprendere più tardi
 *   - Se un passo fallisce, non blocca gli altri
 *   - Ogni passo è una POST atomica: se l'utente esce e rientra, non
 *     c'è "app incartata" (fix del bug segnalato)
 */

interface StepResult {
  ok: boolean;
  kind: string;
  detail?: string;
  generated_panels?: Array<{ page: number; panel: number }>;
}

interface PageInfo {
  number: number;
  n_panels: number;
  all_generated: boolean;
}

export default function KidsGeneratePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const [details, setDetails] = useState<KidsProjectDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState<string | null>(null); // "cover" | "page-N"
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());
  const [progressMsg, setProgressMsg] = useState<string | null>(null);

  async function load() {
    try {
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

  async function generateCover() {
    setWorking("cover");
    setError(null);
    setProgressMsg("Sto disegnando la copertina... può richiedere 30-45 secondi");
    try {
      const res = await apiFetch<StepResult>(
        `/api/kids/projects/${id}/generate-cover`,
        { method: "POST" }
      );
      setProgressMsg(null);
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setProgressMsg(null);
    } finally {
      setWorking(null);
    }
  }

  async function generatePage(pageNum: number) {
    setWorking(`page-${pageNum}`);
    setError(null);
    setProgressMsg(
      `Sto disegnando la pagina ${pageNum}... può richiedere 30-90 secondi`
    );
    try {
      await apiFetch<StepResult>(
        `/api/kids/projects/${id}/generate-page/${pageNum}`,
        { method: "POST" }
      );
      setProgressMsg(null);
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setProgressMsg(null);
    } finally {
      setWorking(null);
    }
  }

  if (!details) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  // Info di stato: cover generata? pagine con vignette generate?
  const vigDone = new Set(
    details.vignettes.map((v) => `${v.page_number}_${v.panel_number}`)
  );

  const pagesInfo: PageInfo[] = (details.story?.pages ?? []).map((p) => {
    const allGen = p.panels.every((pn) =>
      vigDone.has(`${p.number}_${pn.number}`)
    );
    return {
      number: p.number,
      n_panels: p.panels.length,
      all_generated: allGen,
    };
  });

  // Trova il prossimo passo da fare
  const coverDone = details.has_cover;
  const nextPageIdx = pagesInfo.findIndex((p) => !p.all_generated);
  const nextPage = nextPageIdx >= 0 ? pagesInfo[nextPageIdx] : null;
  const allDone = coverDone && nextPage === null;

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <header className="mb-6">
        <div className="mb-4">
          <Link
            href={`/app/kids/${id}`}
            className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
          >
            ← Torna al libretto
          </Link>
        </div>
        <h1 className="text-3xl font-bold mb-1">🎁 Creiamo il tuo libretto</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          Un passo alla volta: prima la copertina, poi ogni pagina. Puoi uscire
          e tornare in qualsiasi momento — non perdi progressi.
        </p>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {progressMsg && (
        <div className="mb-4 bg-[var(--color-accent)]/10 border border-[var(--color-accent)]/40 rounded-lg px-4 py-3 flex items-center gap-3">
          <div className="w-4 h-4 rounded-full bg-[var(--color-accent)] animate-pulse flex-shrink-0" />
          <p className="text-sm">{progressMsg}</p>
        </div>
      )}

      {/* STEP 1: COPERTINA */}
      <section className="mb-6 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden">
        <div className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <span
              className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                coverDone
                  ? "bg-green-500/20 text-green-400"
                  : "bg-[var(--color-accent)] text-[var(--color-bg)]"
              }`}
            >
              {coverDone ? "✓" : "1"}
            </span>
            <h2 className="text-lg font-semibold">📕 La copertina</h2>
          </div>

          {coverDone ? (
            <>
              <img
                src={`/api/kids/projects/${id}/images/cover?t=${refreshTag}`}
                alt="Copertina"
                className="w-full max-w-xs rounded-lg border border-[var(--color-border)] mb-3"
              />
              <p className="text-sm text-green-400">
                ✓ Copertina pronta!
              </p>
            </>
          ) : (
            <div className="text-center py-6">
              <div className="text-5xl mb-3">📕</div>
              <p className="text-sm text-[var(--color-fg-muted)] mb-4">
                Iniziamo dalla copertina.
              </p>
              <button
                onClick={generateCover}
                disabled={working !== null}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded-lg disabled:opacity-50"
              >
                {working === "cover"
                  ? "Sto disegnando..."
                  : "✨ Genera copertina"}
              </button>
            </div>
          )}
        </div>
      </section>

      {/* STEP 2+: PAGINE una alla volta */}
      {coverDone && pagesInfo.length > 0 && (
        <div className="space-y-3">
          {pagesInfo.map((p, i) => {
            const isNext =
              !p.all_generated &&
              (i === 0 || pagesInfo.slice(0, i).every((pp) => pp.all_generated));
            const isBlocked = !p.all_generated && !isNext;
            const workingThis = working === `page-${p.number}`;
            return (
              <section
                key={p.number}
                className={`bg-[var(--color-bg-elev)] border rounded-xl overflow-hidden ${
                  isBlocked
                    ? "border-[var(--color-border)] opacity-40"
                    : p.all_generated
                      ? "border-green-500/30"
                      : "border-[var(--color-accent)]/60"
                }`}
              >
                <div className="p-5">
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                          p.all_generated
                            ? "bg-green-500/20 text-green-400"
                            : isNext
                              ? "bg-[var(--color-accent)] text-[var(--color-bg)]"
                              : "bg-[var(--color-border)] text-[var(--color-fg-muted)]"
                        }`}
                      >
                        {p.all_generated ? "✓" : i + 2}
                      </span>
                      <h3 className="font-semibold">
                        Pagina {p.number}{" "}
                        <span className="text-xs text-[var(--color-fg-muted)] font-normal">
                          ({p.n_panels} vignette)
                        </span>
                      </h3>
                    </div>
                    {p.all_generated ? (
                      <span className="text-green-400 text-xs">
                        ✓ Completa
                      </span>
                    ) : isNext ? (
                      <button
                        onClick={() => generatePage(p.number)}
                        disabled={working !== null}
                        className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold text-sm px-4 py-1.5 rounded disabled:opacity-50"
                      >
                        {workingThis
                          ? "Sto disegnando..."
                          : `✨ Genera pagina ${p.number}`}
                      </button>
                    ) : (
                      <span className="text-xs text-[var(--color-fg-muted)]">
                        Attendi il tuo turno
                      </span>
                    )}
                  </div>

                  {p.all_generated && (
                    <div className="grid grid-cols-3 md:grid-cols-4 gap-2 mt-3">
                      {details.story?.pages
                        .find((pp) => pp.number === p.number)
                        ?.panels.map((pn) => (
                          <div
                            key={pn.number}
                            className="rounded overflow-hidden bg-[var(--color-bg)] border border-[var(--color-border)]"
                          >
                            <img
                              src={`/api/kids/projects/${id}/images/panel/${p.number}/${pn.number}?t=${refreshTag}`}
                              alt={`P${p.number}V${pn.number}`}
                              className="w-full aspect-square object-cover"
                            />
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </section>
            );
          })}
        </div>
      )}

      {/* Chiusura */}
      {allDone && (
        <div className="mt-6 bg-green-500/10 border border-green-500/30 rounded-xl p-6 text-center">
          <div className="text-4xl mb-2">🎉</div>
          <h2 className="text-xl font-semibold mb-2">
            Il libretto è pronto!
          </h2>
          <p className="text-sm text-[var(--color-fg-muted)] mb-4">
            Copertina + {pagesInfo.length} pagine generate.
          </p>
          <Link
            href={`/app/kids/${id}`}
            className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded-lg"
          >
            📖 Vai al libretto
          </Link>
        </div>
      )}
    </div>
  );
}
