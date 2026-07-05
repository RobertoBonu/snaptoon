"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface AdminCard {
  id: string;
  name: string;
  character_type: string;
  caption: string;
  author_display: string;
  author_email: string;
  progressive_number: number;
  moderation_status: string;
  rejection_reason: string;
  submitted_at: string | null;
  moderated_at: string | null;
  image_url: string;
  category_id: string | null;
  category_label: string | null;
  category_macro: string | null;
}

type Filter = "pending" | "published" | "rejected" | "all";

export default function AdminBookshopCardsPage() {
  const [cards, setCards] = useState<AdminCard[] | null>(null);
  const [filter, setFilter] = useState<Filter>("pending");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<{ cards: AdminCard[] }>(
        `/api/admin/bookshop/cards?status_filter=${filter}`,
      );
      setCards(d.cards);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function approve(id: string) {
    if (!confirm("Approvare e pubblicare la figurina?")) return;
    setBusy(id);
    try {
      await apiFetch(`/api/admin/bookshop/cards/${id}/approve`, {
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
      await apiFetch(`/api/admin/bookshop/cards/${rejectingId}/reject`, {
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

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-4">
        <Link
          href="/app/admin"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Pannello admin
        </Link>
      </div>

      <header className="flex justify-between items-start mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-1">
            🎴 Figurine BookShop
          </h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Modera le richieste di pubblicazione delle card collezionabili.
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

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {cards === null ? (
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      ) : cards.length === 0 ? (
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <div className="text-5xl mb-4 opacity-30">🎴</div>
          <p className="text-[var(--color-fg-muted)]">
            Nessuna figurina in questa vista.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {cards.map((c) => {
            const isBusy = busy === c.id;
            return (
              <div
                key={c.id}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4 flex gap-4"
              >
                <div className="w-32 flex-shrink-0 bg-[var(--color-bg)] rounded-lg overflow-hidden border border-[var(--color-border)]" style={{ aspectRatio: "9 / 16" }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={c.image_url}
                    alt={c.name}
                    className="w-full h-full object-contain"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="text-xs font-bold tracking-wide bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-0.5 font-mono">
                      #{String(c.progressive_number).padStart(4, "0")}
                    </span>
                    <span
                      className={`text-xs font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${
                        c.moderation_status === "pending"
                          ? "bg-yellow-900/40 text-yellow-300 border border-yellow-700/50"
                          : c.moderation_status === "published"
                            ? "bg-green-900/40 text-green-300 border border-green-700/50"
                            : c.moderation_status === "rejected"
                              ? "bg-red-900/40 text-red-300 border border-red-700/50"
                              : "bg-slate-800/40 text-slate-300 border border-slate-700/50"
                      }`}
                    >
                      {c.moderation_status}
                    </span>
                    {c.category_label && (
                      <span className="text-[10px] text-[var(--color-fg-muted)]">
                        {c.category_macro?.toUpperCase()} · {c.category_label}
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold text-base mb-0.5">{c.name}</h3>
                  <p className="text-xs text-[var(--color-fg-muted)] mb-1">
                    {c.character_type}
                  </p>
                  <p className="text-xs text-[var(--color-fg-muted)] mb-2">
                    <strong>{c.author_display || c.author_email}</strong>
                    {c.author_email && ` (${c.author_email})`}
                  </p>
                  {c.caption && (
                    <p className="text-sm italic text-[var(--color-fg)] mb-2">
                      &quot;{c.caption}&quot;
                    </p>
                  )}
                  {c.moderation_status === "rejected" && c.rejection_reason && (
                    <p className="text-xs text-red-300 mb-2">
                      Motivo: {c.rejection_reason}
                    </p>
                  )}
                  {c.submitted_at && (
                    <p className="text-[10px] text-[var(--color-fg-muted)] mb-3">
                      Inviata:{" "}
                      {new Date(c.submitted_at).toLocaleString("it-IT")}
                    </p>
                  )}
                  {c.moderation_status === "pending" && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => approve(c.id)}
                        disabled={isBusy}
                        className="text-xs bg-green-600 hover:bg-green-500 text-white font-semibold px-3 py-1.5 rounded disabled:opacity-50"
                      >
                        ✅ Approva
                      </button>
                      <button
                        onClick={() => {
                          setRejectingId(c.id);
                          setRejectReason("");
                        }}
                        disabled={isBusy}
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

      {rejectingId && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => (busy ? null : setRejectingId(null))}
        >
          <div
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold mb-2">❌ Rifiuta figurina</h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-3">
              Motiva il rifiuto (visibile all&apos;utente).
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={4}
              maxLength={1000}
              placeholder="Es. Contenuto non conforme alle linee guida."
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
