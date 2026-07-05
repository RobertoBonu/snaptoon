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
  // Set di chiavi "cover" | "p<page>v<panel>" attualmente in rigenerazione
  const [regenerating, setRegenerating] = useState<Set<string>>(new Set());

  async function regenerateCover() {
    if (
      !confirm(
        "Rigenerare la copertina consuma 1 credito. La copertina attuale sarà eliminata. Procedo?",
      )
    )
      return;
    setRegenerating((prev) => new Set(prev).add("cover"));
    setError(null);
    try {
      await apiFetch(`/api/kids/projects/${id}/regenerate-cover`, {
        method: "POST",
      });
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRegenerating((prev) => {
        const next = new Set(prev);
        next.delete("cover");
        return next;
      });
    }
  }

  // === Community share (cover + tavole) ===
  const [shareModal, setShareModal] = useState<
    | { kind: "cover" }
    | { kind: "tavola"; page: number }
    | { kind: "webtoon" }
    | null
  >(null);
  const [publishedWebtoonId, setPublishedWebtoonId] = useState<string | null>(
    null,
  );
  const [shareCaption, setShareCaption] = useState("");
  const [shareAuthorRole, setShareAuthorRole] = useState("");
  const [sharing, setSharing] = useState(false);
  // Categorie BookShop (per webtoon)
  const [bookshopCategories, setBookshopCategories] = useState<
    Array<{ macro: string; label: string; categories: Array<{ id: string; label: string }> }>
  >([]);
  const [shareCategoryId, setShareCategoryId] = useState<string>("");

  // Carico categorie BookShop una sola volta (per il picker webtoon)
  useEffect(() => {
    fetch("/api/bookshop/categories")
      .then((r) => (r.ok ? r.json() : null))
      .then(
        (d: {
          macros: Array<{
            macro: string;
            label: string;
            categories: Array<{ id: string; label: string }>;
          }>;
        } | null) => {
          if (d) setBookshopCategories(d.macros);
        },
      )
      .catch(() => {});
  }, []);

  async function submitShare() {
    if (!shareModal) return;
    setSharing(true);
    setError(null);
    try {
      let url: string;
      if (shareModal.kind === "cover") url = `/api/project-shares/cover/${id}`;
      else if (shareModal.kind === "webtoon")
        url = `/api/project-shares/webtoon/${id}`;
      else url = `/api/project-shares/tavola/${id}/${shareModal.page}`;
      const body: {
        caption: string;
        author_role: string;
        bookshop_category_id?: string;
      } = {
        caption: shareCaption,
        author_role: shareAuthorRole,
      };
      if (shareModal.kind === "webtoon" && shareCategoryId) {
        body.bookshop_category_id = shareCategoryId;
      }
      const res = await apiFetch<{ id: string }>(url, {
        method: "POST",
        body: JSON.stringify(body),
      });
      const kindLabel =
        shareModal.kind === "webtoon"
          ? "webtoon"
          : shareModal.kind === "cover"
            ? "copertina"
            : "tavola";
      // Per il webtoon salvo l'id share per mostrare subito il link al lettore
      if (shareModal.kind === "webtoon") {
        setPublishedWebtoonId(res.id);
      }
      setShareModal(null);
      setShareCaption("");
      setShareAuthorRole("");
      alert(
        `Richiesta di condivisione ${kindLabel} inviata! Un admin la esaminerà a breve.`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSharing(false);
    }
  }

  async function regenerateVignette(page: number, panel: number) {
    const key = `p${page}v${panel}`;
    if (
      !confirm(
        `Rigenerare la vignetta P${page}V${panel} consuma 1 credito. L'immagine attuale sarà eliminata. Procedo?`,
      )
    )
      return;
    setRegenerating((prev) => new Set(prev).add(key));
    setError(null);
    try {
      await apiFetch(
        `/api/kids/projects/${id}/regenerate-vignette/${page}/${panel}`,
        { method: "POST" },
      );
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRegenerating((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  }

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
              &quot;{details.story.logline}&quot;
            </p>
          )}
          {details.grid_variant_label && (
            <p
              className="mt-2 inline-block text-xs bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-full px-2.5 py-0.5 text-[var(--color-fg-muted)]"
              title="Ritmo di impaginazione scelto casualmente alla creazione"
            >
              🎞 Ritmo: {details.grid_variant_label}
            </p>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          <Link
            href={`/app/kids/${id}/titolo`}
            className="border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-4 py-2.5 rounded-lg transition-colors"
          >
            📝 Titolo & Autore
          </Link>
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
          <button
            onClick={() => {
              setShareCaption("");
              setShareAuthorRole("");
              setShareModal({ kind: "webtoon" });
            }}
            disabled={!details.has_cover || details.vignettes.length === 0}
            className="border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-5 py-2.5 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
            title={
              !details.has_cover
                ? "Genera prima la copertina"
                : details.vignettes.length === 0
                  ? "Genera almeno una vignetta"
                  : "Pubblica come WebToon verticale scrollabile"
            }
          >
            🌐 Pubblica WebToon
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
          <div className="max-w-md">
            <div className="relative">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/api/kids/projects/${id}/images/cover?t=${refreshTag}`}
                alt="Cover"
                className={`rounded-xl w-full border border-[var(--color-border)] ${
                  regenerating.has("cover") ? "opacity-30" : ""
                }`}
              />
              {regenerating.has("cover") && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/40 rounded-xl">
                  <p className="text-sm bg-[var(--color-bg)] px-3 py-1.5 rounded-full">
                    Rigenero...
                  </p>
                </div>
              )}
            </div>
            <div className="mt-2 flex gap-2 flex-wrap">
              <button
                onClick={regenerateCover}
                disabled={regenerating.has("cover")}
                className="text-sm border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-4 py-1.5 rounded transition-colors disabled:opacity-50"
                title="Elimina e ri-genera la copertina (1 credito)"
              >
                🔄 Rigenera copertina (1 cr)
              </button>
              <button
                onClick={() => {
                  setShareCaption("");
                  setShareAuthorRole("");
                  setShareModal({ kind: "cover" });
                }}
                className="text-sm border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-4 py-1.5 rounded transition-colors"
                title="Proponi la copertina per la pagina Esplora"
              >
                🌐 Condividi
              </button>
            </div>
          </div>
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
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-[var(--color-fg-muted)]">
                  Pagina {p.number}
                </h3>
                <button
                  onClick={() => {
                    setShareCaption("");
                    setShareAuthorRole("");
                    setShareModal({ kind: "tavola", page: p.number });
                  }}
                  className="text-xs border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-3 py-1 rounded transition-colors"
                  title="Proponi la tavola per Esplora"
                >
                  🌐 Condividi tavola
                </button>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {p.panels.map((pn) => {
                  const isGenerated = vigSet.has(`${p.number}_${pn.number}`);
                  const rKey = `p${p.number}v${pn.number}`;
                  const isRegen = regenerating.has(rKey);
                  return (
                    <div
                      key={pn.number}
                      className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg overflow-hidden group relative"
                    >
                      {isGenerated ? (
                        <div className="relative">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={`/api/kids/projects/${id}/images/panel/${p.number}/${pn.number}?t=${refreshTag}`}
                            alt={`P${p.number}V${pn.number}`}
                            className={`w-full aspect-square object-cover ${
                              isRegen ? "opacity-30" : ""
                            }`}
                          />
                          {isRegen ? (
                            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                              <p className="text-xs bg-[var(--color-bg)] px-2 py-1 rounded-full">
                                Rigenero...
                              </p>
                            </div>
                          ) : (
                            <button
                              onClick={() =>
                                regenerateVignette(p.number, pn.number)
                              }
                              className="absolute top-1.5 right-1.5 bg-[var(--color-bg)]/85 hover:bg-[var(--color-accent)] hover:text-[var(--color-bg)] text-[var(--color-fg)] text-xs px-2 py-1 rounded shadow opacity-0 group-hover:opacity-100 transition-opacity"
                              title={`Rigenera P${p.number}V${pn.number} (1 credito)`}
                            >
                              🔄 Rigenera
                            </button>
                          )}
                        </div>
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

      {/* Modale condivisione community */}
      {shareModal && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => (sharing ? null : setShareModal(null))}
        >
          <div
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-lg w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold mb-2">
              {shareModal.kind === "webtoon" ? (
                <>🌐 Pubblica come WebToon</>
              ) : (
                <>
                  🌐 Condividi{" "}
                  {shareModal.kind === "cover"
                    ? "la copertina"
                    : `la tavola (pagina ${shareModal.page})`}
                </>
              )}
            </h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-4">
              {shareModal.kind === "webtoon" ? (
                <>
                  Il tuo libretto diventa un WebToon: le vignette impilate
                  verticalmente, scrollabili come un fumetto in stile Naver.
                  Un admin dovrà approvare prima della pubblicazione. Dopo
                  potrai condividere il link pubblico.
                </>
              ) : (
                <>
                  Un admin dovrà approvare prima che appaia su Esplora.
                  Potrai ritirare la richiesta dalla lista delle tue
                  condivisioni.
                </>
              )}
            </p>
            <div className="space-y-3">
              {shareModal.kind === "webtoon" && (
                <div>
                  <label className="block text-sm font-semibold mb-1">
                    Categoria BookShop *
                  </label>
                  <select
                    value={shareCategoryId}
                    onChange={(e) => setShareCategoryId(e.target.value)}
                    required
                    className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                  >
                    <option value="">— Scegli una categoria —</option>
                    {bookshopCategories.map((m) => (
                      <optgroup key={m.macro} label={m.label}>
                        {m.categories.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.label}
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                  {bookshopCategories.every((m) => m.categories.length === 0) && (
                    <p className="text-xs text-yellow-400 mt-1">
                      Nessuna categoria disponibile. Chiedi a un admin di
                      crearne.
                    </p>
                  )}
                </div>
              )}
              <div>
                <label className="block text-sm font-semibold mb-1">
                  Didascalia breve (facoltativa)
                </label>
                <textarea
                  value={shareCaption}
                  onChange={(e) => setShareCaption(e.target.value)}
                  rows={2}
                  maxLength={500}
                  placeholder="Es. Il momento più tenero della storia..."
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">
                  Il tuo ruolo (facoltativo)
                </label>
                <input
                  type="text"
                  value={shareAuthorRole}
                  onChange={(e) => setShareAuthorRole(e.target.value)}
                  maxLength={80}
                  placeholder="Es. Papà creativo, Illustratrice"
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={submitShare}
                  disabled={
                    sharing ||
                    (shareModal.kind === "webtoon" && !shareCategoryId)
                  }
                  className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded disabled:opacity-50"
                >
                  {sharing ? "Invio..." : "🌐 Invia per approvazione"}
                </button>
                <button
                  onClick={() => setShareModal(null)}
                  disabled={sharing}
                  className="text-[var(--color-fg-muted)] px-4 py-2"
                >
                  Annulla
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
