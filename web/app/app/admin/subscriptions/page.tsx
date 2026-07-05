"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

interface Subscription {
  id: string;
  email: string;
  plan: string;
  plan_label: string;
  plan_requested: string | null;
  plan_requested_label: string | null;
  subscription_status: string;
  subscription_activated_at: string | null;
  subscription_rejection_reason: string;
  created_at: string;
  credits_total: number;
  credits_used: number;
  ftp_striscia_used: number;
  ftp_card_used: number;
  ftp_cover_used: number;
  is_free_to_play: boolean;
}

const STATUS_LABEL: Record<string, { label: string; color: string }> = {
  pending_approval: { label: "⏳ In attesa", color: "#FDE047" },
  active: { label: "✅ Attivo", color: "#86EFAC" },
  cancelled: { label: "🚫 Disdetto", color: "#94A3B8" },
  rejected: { label: "❌ Rifiutato", color: "#FCA5A5" },
};

export default function AdminSubscriptionsPage() {
  const [subs, setSubs] = useState<Subscription[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("pending_approval");
  const [busy, setBusy] = useState<Set<string>>(new Set());
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  async function load() {
    try {
      setError(null);
      const q = filter ? `?status_filter=${filter}` : "";
      const d = await apiFetch<{ subscriptions: Subscription[] }>(
        `/api/admin/subscriptions${q}`,
      );
      setSubs(d.subscriptions);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  async function approve(id: string) {
    if (busy.has(id)) return;
    setBusy((b) => new Set(b).add(id));
    try {
      await apiFetch(`/api/admin/subscriptions/${id}/approve`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy((b) => {
        const n = new Set(b);
        n.delete(id);
        return n;
      });
    }
  }

  async function doReject() {
    if (!rejectingId) return;
    setBusy((b) => new Set(b).add(rejectingId));
    try {
      await apiFetch(`/api/admin/subscriptions/${rejectingId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason: rejectReason }),
      });
      setRejectingId(null);
      setRejectReason("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy((b) => {
        const n = new Set(b);
        if (rejectingId) n.delete(rejectingId);
        return n;
      });
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">💳 Abbonamenti</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Approva / rifiuta richieste registrazione e cambi piano.
          </p>
        </div>
        <Link
          href="/app/admin"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Admin
        </Link>
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {/* Filtri */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {[
          { v: "pending_approval", l: "⏳ In attesa" },
          { v: "active", l: "✅ Attivi" },
          { v: "rejected", l: "❌ Rifiutati" },
          { v: "cancelled", l: "🚫 Disdetti" },
          { v: "", l: "Tutti" },
        ].map((f) => (
          <button
            key={f.v}
            onClick={() => setFilter(f.v)}
            className={`text-sm px-3 py-1.5 rounded-full border ${
              filter === f.v
                ? "bg-[var(--color-accent)] text-[var(--color-bg)] border-[var(--color-accent)]"
                : "border-[var(--color-border)] hover:border-[var(--color-accent)]"
            }`}
          >
            {f.l}
          </button>
        ))}
      </div>

      {subs === null ? (
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      ) : subs.length === 0 ? (
        <p className="text-[var(--color-fg-muted)] italic">
          Nessuna richiesta con questo filtro.
        </p>
      ) : (
        <div className="overflow-x-auto border border-[var(--color-border)] rounded-xl">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-bg-elev)]">
              <tr>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Piano attuale</th>
                <th className="text-left px-4 py-3">Piano richiesto</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">FTP usati</th>
                <th className="text-left px-4 py-3">Registrato</th>
                <th className="text-right px-4 py-3">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {subs.map((s) => {
                const st = STATUS_LABEL[s.subscription_status] || {
                  label: s.subscription_status,
                  color: "#94A3B8",
                };
                const isBusy = busy.has(s.id);
                return (
                  <tr
                    key={s.id}
                    className="border-t border-[var(--color-border)]"
                  >
                    <td className="px-4 py-3">{s.email}</td>
                    <td className="px-4 py-3">{s.plan_label}</td>
                    <td className="px-4 py-3">
                      {s.plan_requested_label || "—"}
                    </td>
                    <td className="px-4 py-3" style={{ color: st.color }}>
                      {st.label}
                      {s.subscription_rejection_reason && (
                        <div className="text-xs text-red-400 mt-1">
                          {s.subscription_rejection_reason}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {s.is_free_to_play ? (
                        <>
                          Str {s.ftp_striscia_used}/1 · Fig{" "}
                          {s.ftp_card_used}/1 · Cov {s.ftp_cover_used}/1
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {new Date(s.created_at).toLocaleDateString("it-IT")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {s.subscription_status === "pending_approval" && (
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => approve(s.id)}
                            disabled={isBusy}
                            className="text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded disabled:opacity-40"
                          >
                            {isBusy ? "..." : "✅ Approva"}
                          </button>
                          <button
                            onClick={() => setRejectingId(s.id)}
                            disabled={isBusy}
                            className="text-xs bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded disabled:opacity-40"
                          >
                            ❌ Rifiuta
                          </button>
                        </div>
                      )}
                      {s.subscription_status === "active" && (
                        <span className="text-xs text-[var(--color-fg-muted)]">
                          già attivo
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal Reject */}
      {rejectingId && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-md w-full">
            <h2 className="text-lg font-semibold mb-4">Rifiuta richiesta</h2>
            <label className="block text-sm mb-1">
              Motivo (verrà inviato via email all&apos;utente):
            </label>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={4}
              maxLength={500}
              className="w-full px-3 py-2 mb-4 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
              placeholder="Es. Dati incompleti, contattaci per assistenza..."
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setRejectingId(null);
                  setRejectReason("");
                }}
                className="px-4 py-2 text-sm text-[var(--color-fg-muted)]"
              >
                Annulla
              </button>
              <button
                onClick={doReject}
                className="bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded"
              >
                Rifiuta
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
