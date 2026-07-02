"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { apiFetch } from "@/lib/api";

interface MyCharacter {
  id: string;
  name: string;
  visual_description: string;
  has_reference: boolean;
  created_at: string;
  share_status: string; // not_shared | pending | published | rejected
  share_caption: string;
  share_author_role: string;
  share_rejection_reason: string;
}

interface MyCharactersList {
  characters: MyCharacter[];
}

type Mode = "list" | "new-text" | "new-photo";

// Altezza fissa identica a /esplora per uniformità visiva
const CARD_H = 320;

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
        background: "rgba(3, 6, 12, 0.9)",
        backdropFilter: "blur(6px)",
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
          maxWidth: "min(96vw, 1400px)",
          maxHeight: "92vh",
          objectFit: "contain",
          borderRadius: 14,
          boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
          cursor: "default",
        }}
      />
    </div>,
    document.body,
  );
}

function ShareStatusBadge({ status }: { status: string }) {
  const styles: Record<string, { bg: string; border: string; color: string; label: string }> = {
    pending: {
      bg: "rgba(234, 179, 8, 0.12)",
      border: "rgba(234, 179, 8, 0.5)",
      color: "#FDE047",
      label: "⏳ In attesa",
    },
    published: {
      bg: "rgba(34, 197, 94, 0.12)",
      border: "rgba(34, 197, 94, 0.5)",
      color: "#86EFAC",
      label: "✅ Pubblicato",
    },
    rejected: {
      bg: "rgba(239, 68, 68, 0.12)",
      border: "rgba(239, 68, 68, 0.5)",
      color: "#FCA5A5",
      label: "❌ Rifiutato",
    },
  };
  const s = styles[status];
  if (!s) return null;
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        background: s.bg,
        border: `1px solid ${s.border}`,
        color: s.color,
        borderRadius: 999,
        padding: "3px 10px",
      }}
    >
      {s.label}
    </span>
  );
}

function CharacterCard({
  c,
  refreshTag,
  onEdit,
  onRegenerate,
  onDelete,
  onShare,
  onUnshare,
  busy,
}: {
  c: MyCharacter;
  refreshTag: number;
  onEdit: () => void;
  onRegenerate: () => void;
  onDelete: () => void;
  onShare: () => void;
  onUnshare: () => void;
  busy: boolean;
}) {
  const [width, setWidth] = useState<number>(CARD_H); // 1:1 default per portrait
  const [zoom, setZoom] = useState(false);
  const imgSrc = `/api/my-characters/${c.id}/image?t=${refreshTag}`;

  return (
    <div
      style={{
        width,
        maxWidth: "100%",
        background: "#0F1420",
        border: "1px solid #1E2436",
        borderRadius: 20,
        padding: 12,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {c.has_reference ? (
        <div
          onClick={() => setZoom(true)}
          style={{
            position: "relative",
            cursor: "zoom-in",
            borderRadius: 12,
            overflow: "hidden",
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imgSrc}
            alt={c.name}
            onLoad={(e) => {
              const el = e.currentTarget;
              if (el.naturalHeight > 0) {
                setWidth(
                  Math.round(CARD_H * (el.naturalWidth / el.naturalHeight)),
                );
              }
            }}
            style={{
              height: CARD_H,
              width: "100%",
              display: "block",
              objectFit: "cover",
              borderRadius: 12,
              opacity: busy ? 0.3 : 1,
            }}
          />
          {busy && (
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                background: "rgba(0,0,0,0.4)",
              }}
            >
              <span
                style={{
                  background: "#0F1420",
                  padding: "6px 14px",
                  borderRadius: 999,
                  fontSize: 12,
                  color: "#F1F5F9",
                }}
              >
                Elaboro...
              </span>
            </div>
          )}
          <span
            aria-hidden
            style={{
              position: "absolute",
              bottom: 10,
              right: 10,
              width: 32,
              height: 32,
              borderRadius: 999,
              background: "rgba(3,6,12,0.6)",
              border: "1px solid rgba(255,255,255,0.18)",
              color: "#F1F5F9",
              fontSize: 14,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            🔍
          </span>
        </div>
      ) : (
        <div
          style={{
            height: CARD_H,
            width: "100%",
            borderRadius: 12,
            background: "linear-gradient(135deg, #161B26, #0D1017)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#64748B",
            fontSize: 13,
          }}
        >
          Nessuna reference
        </div>
      )}

      <div style={{ padding: "14px 6px 4px" }}>
        <div
          style={{
            fontSize: 17,
            fontWeight: 700,
            color: "#F1F5F9",
            marginBottom: 6,
            overflowWrap: "break-word",
          }}
        >
          {c.name}
        </div>
        <p
          style={{
            fontSize: 13,
            color: "#94A3B8",
            lineHeight: 1.5,
            marginBottom: 10,
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {c.visual_description}
        </p>

        {c.share_status !== "not_shared" && (
          <div style={{ marginBottom: 10 }}>
            <ShareStatusBadge status={c.share_status} />
            {c.share_status === "rejected" && c.share_rejection_reason && (
              <p
                style={{
                  fontSize: 11,
                  color: "#FCA5A5",
                  marginTop: 6,
                  lineHeight: 1.4,
                }}
              >
                Motivo: {c.share_rejection_reason}
              </p>
            )}
          </div>
        )}

        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <button
            onClick={onEdit}
            className="text-xs text-[var(--color-fg-muted)] hover:text-[var(--color-accent)] border border-[var(--color-border)] hover:border-[var(--color-accent)] px-2 py-1 rounded"
          >
            ✏️ Modifica
          </button>
          <button
            onClick={onRegenerate}
            disabled={busy}
            className="text-xs text-[var(--color-fg-muted)] hover:text-[var(--color-accent)] border border-[var(--color-border)] hover:border-[var(--color-accent)] px-2 py-1 rounded disabled:opacity-50"
          >
            🔄 Rigenera (1cr)
          </button>
          {c.share_status === "not_shared" || c.share_status === "rejected" ? (
            <button
              onClick={onShare}
              disabled={!c.has_reference}
              className="text-xs bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-2.5 py-1 rounded disabled:opacity-50"
              title="Sottoponi ad approvazione admin per Esplora"
            >
              🌐 Condividi
            </button>
          ) : (
            <button
              onClick={onUnshare}
              className="text-xs text-[var(--color-fg-muted)] hover:text-red-400 border border-[var(--color-border)] hover:border-red-400 px-2 py-1 rounded"
              title="Rimuove da /esplora e ritira la richiesta"
            >
              🚫 Ritira
            </button>
          )}
          <button
            onClick={onDelete}
            className="text-xs text-[var(--color-fg-muted)] hover:text-red-400 px-2 py-1"
          >
            🗑
          </button>
        </div>
      </div>

      {zoom && c.has_reference && (
        <Lightbox src={imgSrc} alt={c.name} onClose={() => setZoom(false)} />
      )}
    </div>
  );
}

export default function MyCharactersPage() {
  const [data, setData] = useState<MyCharactersList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("list");
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  // Form state (nuovo personaggio)
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [creating, setCreating] = useState(false);

  // Editing
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  // Share modal
  const [sharingId, setSharingId] = useState<string | null>(null);
  const [shareCaption, setShareCaption] = useState("");
  const [shareAuthorRole, setShareAuthorRole] = useState("");
  const [sharingBusy, setSharingBusy] = useState(false);

  // Busy tracking per bottoni delle card
  const [busy, setBusy] = useState<Set<string>>(new Set());

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<MyCharactersList>("/api/my-characters");
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  function markBusy(id: string, on: boolean) {
    setBusy((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function resetForm() {
    setName("");
    setDescription("");
    setPhoto(null);
  }

  async function handleCreateFromText(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      await apiFetch("/api/my-characters", {
        method: "POST",
        body: JSON.stringify({ name, visual_description: description }),
      });
      resetForm();
      setMode("list");
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  async function handleCreateFromPhoto(e: React.FormEvent) {
    e.preventDefault();
    if (!photo) {
      setError("Carica una foto.");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("name", name);
      params.set("visual_description", description);
      const formData = new FormData();
      formData.append("file", photo);
      const res = await fetch(
        `/api/my-characters/from-photo?${params.toString()}`,
        { method: "POST", body: formData, credentials: "include" },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      resetForm();
      setMode("list");
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  function startEdit(c: MyCharacter) {
    setEditingId(c.id);
    setEditName(c.name);
    setEditDesc(c.visual_description);
  }

  async function saveEdit() {
    if (!editingId) return;
    try {
      await apiFetch(`/api/my-characters/${editingId}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: editName,
          visual_description: editDesc,
        }),
      });
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function regenerate(id: string) {
    if (!confirm("Rigenerare la reference costa 1 credito. Procedo?")) return;
    markBusy(id, true);
    setError(null);
    try {
      await apiFetch(`/api/my-characters/${id}/regenerate`, {
        method: "POST",
      });
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      markBusy(id, false);
    }
  }

  async function remove(id: string, charName: string) {
    if (!confirm(`Eliminare "${charName}"?`)) return;
    try {
      const res = await fetch(`/api/my-characters/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  function openShare(c: MyCharacter) {
    setSharingId(c.id);
    setShareCaption(c.share_caption || "");
    setShareAuthorRole(c.share_author_role || "");
  }

  async function submitShare() {
    if (!sharingId) return;
    setSharingBusy(true);
    setError(null);
    try {
      await apiFetch(`/api/my-characters/${sharingId}/share`, {
        method: "POST",
        body: JSON.stringify({
          caption: shareCaption,
          author_role: shareAuthorRole,
        }),
      });
      setSharingId(null);
      setShareCaption("");
      setShareAuthorRole("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSharingBusy(false);
    }
  }

  async function unshare(id: string) {
    if (
      !confirm(
        "Rimuovere la condivisione? Il personaggio non sarà più visibile su Esplora.",
      )
    )
      return;
    try {
      await apiFetch(`/api/my-characters/${id}/unshare`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-start mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-1">👤 I miei personaggi</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Archivio riusabile in qualsiasi progetto. Puoi anche condividerli
            con la community su <a href="/esplora" className="underline">Esplora</a>.
          </p>
        </div>
        {mode === "list" && (
          <div className="flex gap-2">
            <button
              onClick={() => {
                resetForm();
                setMode("new-text");
              }}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded"
            >
              + Da descrizione (1 cr)
            </button>
            <button
              onClick={() => {
                resetForm();
                setMode("new-photo");
              }}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded"
            >
              + Da foto (1 cr)
            </button>
          </div>
        )}
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {mode === "new-text" && (
        <form
          onSubmit={handleCreateFromText}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6 max-w-2xl"
        >
          <h2 className="font-semibold text-lg mb-4">✏️ Nuovo da descrizione</h2>
          <p className="text-sm text-[var(--color-fg-muted)] mb-4">
            L&apos;AI genera una reference in stile portrait neutro. Costo:
            1 credito.
          </p>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Nome (es. Lollo, Nonna Rosa, Milu il gatto)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
              maxLength={255}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
            <textarea
              placeholder="Descrizione visiva dettagliata..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={4}
              minLength={5}
              maxLength={2000}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-none"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={creating || !name.trim() || description.length < 5}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50"
              >
                {creating ? "Genero..." : "✨ Crea (1 cr)"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("list");
                  resetForm();
                }}
                className="text-[var(--color-fg-muted)] px-5 py-2"
              >
                Annulla
              </button>
            </div>
          </div>
        </form>
      )}

      {mode === "new-photo" && (
        <form
          onSubmit={handleCreateFromPhoto}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6 max-w-2xl"
        >
          <h2 className="font-semibold text-lg mb-2">📷 Nuovo da foto</h2>
          <p className="text-sm text-[var(--color-fg-muted)] mb-4">
            Carica una foto reale del soggetto. La foto originale{" "}
            <strong>viene cancellata immediatamente</strong> dopo la
            generazione. Costo: 1 credito.
          </p>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Nome"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={255}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
            <textarea
              placeholder="Descrizione aggiuntiva (facoltativa)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              maxLength={2000}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-none"
            />
            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp"
              onChange={(e) => setPhoto(e.target.files?.[0] || null)}
              required
              className="w-full text-sm"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={creating || !name.trim() || !photo}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50"
              >
                {creating ? "Genero..." : "✨ Crea (1 cr)"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("list");
                  resetForm();
                }}
                className="text-[var(--color-fg-muted)] px-5 py-2"
              >
                Annulla
              </button>
            </div>
          </div>
        </form>
      )}

      {mode === "list" && (
        <>
          {data === null && !error ? (
            <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
          ) : data && data.characters.length === 0 ? (
            <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
              <div className="text-5xl mb-4 opacity-30">👥</div>
              <p className="text-[var(--color-fg-muted)]">
                Nessun personaggio nel tuo archivio.
              </p>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "flex-start",
                gap: 20,
              }}
            >
              {data?.characters.map((c) => (
                <CharacterCard
                  key={c.id}
                  c={c}
                  refreshTag={refreshTag}
                  onEdit={() => startEdit(c)}
                  onRegenerate={() => regenerate(c.id)}
                  onDelete={() => remove(c.id, c.name)}
                  onShare={() => openShare(c)}
                  onUnshare={() => unshare(c.id)}
                  busy={busy.has(c.id)}
                />
              ))}
            </div>
          )}
        </>
      )}

      {/* Modale modifica metadata */}
      {editingId && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => setEditingId(null)}
        >
          <div
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-lg w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold mb-4">✏️ Modifica</h2>
            <div className="space-y-3">
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
              />
              <textarea
                value={editDesc}
                onChange={(e) => setEditDesc(e.target.value)}
                rows={4}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={saveEdit}
                  className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded"
                >
                  💾 Salva
                </button>
                <button
                  onClick={() => setEditingId(null)}
                  className="text-[var(--color-fg-muted)] px-4 py-2"
                >
                  Annulla
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modale condivisione */}
      {sharingId && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => (sharingBusy ? null : setSharingId(null))}
        >
          <div
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-lg w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold mb-2">
              🌐 Condividi con la community
            </h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-4">
              Un admin dovrà approvare prima che il personaggio appaia su{" "}
              <a href="/esplora" className="underline">
                Esplora
              </a>
              . Potrai ritirare la richiesta in qualsiasi momento.
            </p>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-semibold mb-1">
                  Didascalia breve (facoltativa)
                </label>
                <textarea
                  value={shareCaption}
                  onChange={(e) => setShareCaption(e.target.value)}
                  rows={2}
                  maxLength={500}
                  placeholder="Es. Un piccolo eroe che ama i biscotti."
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
                  placeholder="Es. Papà creativo, Illustratrice, Studente"
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={submitShare}
                  disabled={sharingBusy}
                  className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded disabled:opacity-50"
                >
                  {sharingBusy ? "Invio..." : "🌐 Invia per approvazione"}
                </button>
                <button
                  onClick={() => setSharingId(null)}
                  disabled={sharingBusy}
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
