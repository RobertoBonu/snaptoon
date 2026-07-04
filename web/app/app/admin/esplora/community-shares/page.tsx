"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface ShareAdminItem {
  id: string;
  project_id: string;
  project_title: string;
  project_flow: string;
  asset_kind: string; // cover | tavola
  page_number: number | null;
  author_name: string;
  author_email: string;
  author_role: string;
  caption: string;
  submitted_at: string | null;
  moderated_at: string | null;
  rejection_reason: string;
  share_status: string;
  image_url: string;
}

type Filter = "pending" | "published" | "rejected" | "all";
type KindTab = "all" | "cover" | "tavola" | "webtoon";

export default function AdminCommunitySharesPage() {
  const [items, setItems] = useState<ShareAdminItem[] | null>(null);
  const [filter, setFilter] = useState<Filter>("pending");
  const [kindTab, setKindTab] = useState<KindTab>("all");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  async function load() {
    try {
      setError(null);
      const q = `?status_filter=${filter}`;
      const d = await apiFetch<ShareAdminItem[]>(
        `/api/admin/esplora/project-shares${q}`,
      );
      setItems(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function approve(id: string) {
    if (!confirm("Approvare e pubblicare su /esplora?")) return;
    setBusy(id);
    try {
      await apiFetch(`/api/admin/esplora/project-shares/${id}/approve`, {
        method: "POST",
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function submitReject() {
    if (!rejectingId) return;
    setBusy(rejectingId);
    try {
      await apiFetch(`/api/admin/esplora/project-shares/${rejectingId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason: rejectReason }),
      });
      setRejectingId(null);
      setRejectReason("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  const filtered = (items || []).filter((c) => {
    if (kindTab === "all") return true;
    return c.asset_kind === kindTab;
  });

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-4">
        <Link
          href="/app/admin/esplora"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Asset Esplora
        </Link>
      </div>

      <header className="flex justify-between items-start mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-1">
            🎨 Copertine e tavole condivise dagli utenti
          </h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Modera le richieste di pubblicazione su{" "}
            <a href="/esplora" className="underline">
              Esplora
            </a>
            .
          </p>
        </div>
        <div className="flex gap-1 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg p-1">
          {(["pending", "published", "rejected", "all"] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-xs font-semibold px-3 py-1.5 rounded transition-colors ${
                filter === f
                  ? "bg-[var(--color-accent)] text-[var(--color-bg)]"
                  : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              }`}
            >
              {f === "pending" && "⏳ In attesa"}
              {f === "published" && "✅ Pubblicate"}
              {f === "rejected" && "❌ Rifiutate"}
              {f === "all" && "Tutte"}
            </button>
          ))}
        </div>
      </header>

      {/* Tab kind: tutte / cover / tavola */}
      <div className="flex gap-1 mb-4 flex-wrap">
        {(["all", "cover", "tavola", "webtoon"] as KindTab[]).map((k) => (
          <button
            key={k}
            onClick={() => setKindTab(k)}
            className={`text-xs font-semibold px-3 py-1.5 rounded transition-colors ${
              kindTab === k
                ? "bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-[var(--color-accent)]/50"
                : "text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] border border-[var(--color-border)]"
            }`}
          >
            {k === "all" && "Tutti i tipi"}
            {k === "cover" && "📕 Copertine"}
            {k === "tavola" && "🖼 Tavole"}
            {k === "webtoon" && "🌐 WebToon"}
          </button>
        ))}
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {items === null ? (
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      ) : filtered.length === 0 ? (
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <div className="text-5xl mb-4 opacity-30">📭</div>
          <p className="text-[var(--color-fg-muted)]">
            {filter === "pending"
              ? "Nessuna richiesta in attesa."
              : "Niente in questa vista."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((c) => {
            const isWorking = busy === c.id;
            return (
              <div
                key={c.id}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4 flex gap-4"
              >
                <div className="w-40 flex-shrink-0 bg-[var(--color-bg)] rounded-lg overflow-hidden border border-[var(--color-border)]">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={c.image_url}
                    alt={c.project_title}
                    className="w-full h-auto object-cover"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="text-xs font-bold uppercase tracking-wide px-2 py-0.5 rounded-full bg-[var(--color-bg)] border border-[var(--color-border)]">
                      {c.asset_kind === "cover"
                        ? "📕 Cover"
                        : c.asset_kind === "webtoon"
                          ? "🌐 WebToon"
                          : `🖼 Tavola P${c.page_number}`}
                    </span>
                    {c.asset_kind === "webtoon" &&
                      c.share_status === "published" && (
                        <a
                          href={`/w/${c.id}`}
                          target="_blank"
                          rel="noopener"
                          className="text-xs text-[var(--color-accent)] hover:underline"
                        >
                          Apri reader →
                        </a>
                      )}
                    <span
                      className={`text-xs font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${
                        c.share_status === "pending"
                          ? "bg-yellow-900/40 text-yellow-300 border border-yellow-700/50"
                          : c.share_status === "published"
                            ? "bg-green-900/40 text-green-300 border border-green-700/50"
                            : "bg-red-900/40 text-red-300 border border-red-700/50"
                      }`}
                    >
                      {c.share_status}
                    </span>
                    <span className="text-xs text-[var(--color-fg-muted)]">
                      {c.project_flow.toUpperCase()}
                    </span>
                  </div>
                  <h3 className="font-semibold text-sm mb-1 truncate">
                    {c.project_title || "(senza titolo)"}
                  </h3>
                  <p className="text-xs text-[var(--color-fg-muted)] mb-2">
                    <strong>{c.author_name}</strong>
                    {c.author_role && ` — ${c.author_role}`} (
                    {c.author_email})
                  </p>
                  {c.caption && (
                    <p className="text-sm mb-2 italic text-[var(--color-fg)]">
                      &quot;{c.caption}&quot;
                    </p>
                  )}
                  {c.share_status === "rejected" && c.rejection_reason && (
                    <p className="text-xs text-red-300 mb-2">
                      Motivo rifiuto: {c.rejection_reason}
                    </p>
                  )}
                  {c.submitted_at && (
                    <p className="text-[10px] text-[var(--color-fg-muted)] mb-3">
                      Inviato:{" "}
                      {new Date(c.submitted_at).toLocaleString("it-IT")}
                    </p>
                  )}
                  {c.share_status === "pending" && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => approve(c.id)}
                        disabled={isWorking}
                        className="text-xs bg-green-600 hover:bg-green-500 text-white font-semibold px-3 py-1.5 rounded disabled:opacity-50"
                      >
                        ✅ Approva
                      </button>
                      <button
                        onClick={() => {
                          setRejectingId(c.id);
                          setRejectReason("");
                        }}
                        disabled={isWorking}
                        className="text-xs border border-red-500/50 hover:border-red-500 hover:text-red-300 text-[var(--color-fg-muted)] px-3 py-1.5 rounded disabled:opacity-50"
                      >
                        ❌ Rifiuta
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modale rifiuto */}
      {rejectingId && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => (busy ? null : setRejectingId(null))}
        >
          <div
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold mb-2">❌ Rifiuta</h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-3">
              Motiva il rifiuto (sarà visibile all&apos;utente).
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={4}
              maxLength={1000}
              placeholder="Es. Non conforme alle linee guida della community."
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm resize-none mb-3"
            />
            <div className="flex gap-2">
              <button
                onClick={submitReject}
                disabled={busy !== null}
                className="bg-red-600 hover:bg-red-500 text-white font-semibold px-4 py-2 rounded disabled:opacity-50"
              >
                Conferma rifiuto
              </button>
              <button
                onClick={() => setRejectingId(null)}
                disabled={busy !== null}
                className="text-[var(--color-fg-muted)] px-4 py-2"
              >
                Annulla
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
