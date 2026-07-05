"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Cover {
  id: string;
  title: string;
  subtitle: string;
  author: string;
  description: string;
  style_preset_id: string;
  author_display: string;
  cast_snapshot: { name: string; description: string; id?: string }[];
  has_image: boolean;
  moderation_status: string;
  rejection_reason: string;
  bookshop_category_id: string | null;
  created_at: string;
}

interface CoversListOut {
  covers: Cover[];
}

interface MyCharacter {
  id: string;
  name: string;
  visual_description: string;
  has_reference: boolean;
}

interface KidsStyle {
  slug: string;
  label: string;
  preset_id: string;
}

interface MacroGroup {
  macro: string;
  label: string;
  categories: { id: string; label: string }[];
}

const STATUS_STYLE: Record<
  string,
  { bg: string; border: string; color: string; label: string }
> = {
  draft: {
    bg: "rgba(100,116,139,0.12)",
    border: "rgba(100,116,139,0.4)",
    color: "#94A3B8",
    label: "Bozza",
  },
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
    label: "✅ Pubblicata",
  },
  rejected: {
    bg: "rgba(239, 68, 68, 0.12)",
    border: "rgba(239, 68, 68, 0.5)",
    color: "#FCA5A5",
    label: "❌ Rifiutata",
  },
};

export default function MyCoversPage() {
  const [covers, setCovers] = useState<Cover[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshTag, setRefreshTag] = useState(Date.now());

  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [author, setAuthor] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const [kidsStyles, setKidsStyles] = useState<KidsStyle[]>([]);
  const [styleSamples, setStyleSamples] = useState<Record<string, string>>({});
  const [selectedPresetId, setSelectedPresetId] = useState<string>("");

  const [myChars, setMyChars] = useState<MyCharacter[]>([]);
  const [selectedCharIds, setSelectedCharIds] = useState<Set<string>>(new Set());

  // Pubblicazione BookShop
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [publishCategoryId, setPublishCategoryId] = useState<string>("");
  const [publishing, setPublishing] = useState(false);
  const [categories, setCategories] = useState<MacroGroup[]>([]);

  const [busy, setBusy] = useState<Set<string>>(new Set());

  // Modal creazione personaggio al volo
  const [showCharModal, setShowCharModal] = useState(false);
  const [charTab, setCharTab] = useState<"text" | "photo">("text");
  const [newCharName, setNewCharName] = useState("");
  const [newCharDesc, setNewCharDesc] = useState("");
  const [newCharPhoto, setNewCharPhoto] = useState<File | null>(null);
  const [creatingChar, setCreatingChar] = useState(false);
  const [charError, setCharError] = useState<string | null>(null);

  async function loadAll() {
    try {
      const [list, styles, mine, cats] = await Promise.all([
        apiFetch<CoversListOut>("/api/covers/mine"),
        apiFetch<KidsStyle[]>("/api/kids/styles"),
        apiFetch<{ characters: MyCharacter[] }>("/api/my-characters"),
        apiFetch<{ macros: MacroGroup[] }>("/api/bookshop/categories").catch(
          () => ({ macros: [] as MacroGroup[] }),
        ),
      ]);
      setCovers(list.covers);
      setKidsStyles(styles);
      setMyChars(mine.characters.filter((c) => c.has_reference));
      setCategories(cats.macros || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
    // Style thumbnails
    fetch("/api/styles/samples?flow=kids")
      .then((r) => (r.ok ? r.json() : null))
      .then(
        (d: {
          samples: { style_preset_id: string; image_url: string }[];
        } | null) => {
          if (!d) return;
          const map: Record<string, string> = {};
          for (const s of d.samples) map[s.style_preset_id] = s.image_url;
          setStyleSamples(map);
        },
      )
      .catch(() => {});
  }

  useEffect(() => {
    loadAll();
  }, []);

  function resetForm() {
    setTitle("");
    setSubtitle("");
    setAuthor("");
    setDescription("");
    setSelectedPresetId("");
    setSelectedCharIds(new Set());
    setShowCreate(false);
  }

  function toggleChar(id: string) {
    setSelectedCharIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else if (next.size < 6) next.add(id);
      return next;
    });
  }

  function resetCharModal() {
    setNewCharName("");
    setNewCharDesc("");
    setNewCharPhoto(null);
    setCharError(null);
    setShowCharModal(false);
    setCharTab("text");
  }

  async function handleCreateCharacter(e: React.FormEvent) {
    e.preventDefault();
    if (!newCharName.trim()) return;
    setCreatingChar(true);
    setCharError(null);
    try {
      let created: MyCharacter;
      if (charTab === "photo" && newCharPhoto) {
        // Multipart upload: usa fetch diretto (apiFetch è solo JSON)
        const fd = new FormData();
        fd.append("photo", newCharPhoto);
        const params = new URLSearchParams({
          name: newCharName.trim(),
          notes: newCharDesc.trim(),
        });
        const res = await fetch(`/api/my-characters/from-photo?${params.toString()}`, {
          method: "POST",
          credentials: "include",
          body: fd,
        });
        if (!res.ok) {
          const d = await res.json().catch(() => ({}));
          throw new Error(
            typeof d.detail === "string"
              ? d.detail
              : d.detail?.message || `Errore ${res.status}`,
          );
        }
        created = await res.json();
      } else {
        // Da testo
        if (!newCharDesc.trim() || newCharDesc.trim().length < 5) {
          setCharError("Aggiungi almeno una breve descrizione visiva del personaggio (minimo 5 caratteri).");
          setCreatingChar(false);
          return;
        }
        created = await apiFetch<MyCharacter>("/api/my-characters", {
          method: "POST",
          body: JSON.stringify({
            name: newCharName.trim(),
            visual_description: newCharDesc.trim(),
          }),
        });
      }
      // Aggiungi alla lista + seleziona automaticamente
      setMyChars((prev) => [created, ...prev.filter((c) => c.id !== created.id)]);
      setSelectedCharIds((prev) => {
        const next = new Set(prev);
        if (next.size < 6) next.add(created.id);
        return next;
      });
      setRefreshTag(Date.now());
      resetCharModal();
    } catch (e) {
      setCharError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreatingChar(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !selectedPresetId) return;
    setCreating(true);
    setError(null);
    try {
      const characters = Array.from(selectedCharIds).map((id) => {
        const mc = myChars.find((c) => c.id === id);
        return {
          name: mc?.name || "",
          description: mc?.visual_description || "",
          my_character_id: id,
        };
      });
      await apiFetch<Cover>("/api/covers", {
        method: "POST",
        body: JSON.stringify({
          title: title.trim(),
          subtitle: subtitle.trim(),
          author: author.trim(),
          description: description.trim(),
          style_preset_id: selectedPresetId,
          characters,
        }),
      });
      resetForm();
      setRefreshTag(Date.now());
      await loadAll();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      // Sanitizza "[object Object]" nel caso di apiFetch legacy in cache
      setError(msg === "[object Object]" ? "Errore durante la generazione della cover. Riprova." : msg);
    } finally {
      setCreating(false);
    }
  }

  async function handleRegen(cid: string) {
    if (busy.has(cid)) return;
    setBusy((b) => new Set(b).add(cid));
    try {
      await apiFetch(`/api/covers/${cid}/regenerate`, { method: "POST" });
      setRefreshTag(Date.now());
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy((b) => {
        const n = new Set(b);
        n.delete(cid);
        return n;
      });
    }
  }

  async function handleDelete(cid: string) {
    if (!confirm("Eliminare questa cover? L'azione è irreversibile.")) return;
    setBusy((b) => new Set(b).add(cid));
    try {
      await apiFetch(`/api/covers/${cid}`, { method: "DELETE" });
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy((b) => {
        const n = new Set(b);
        n.delete(cid);
        return n;
      });
    }
  }

  async function handlePublish() {
    if (!publishingId || !publishCategoryId) return;
    setPublishing(true);
    try {
      await apiFetch(`/api/covers/${publishingId}/publish`, {
        method: "POST",
        body: JSON.stringify({ category_id: publishCategoryId }),
      });
      setPublishingId(null);
      setPublishCategoryId("");
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPublishing(false);
    }
  }

  async function handleUnpublish(cid: string) {
    setBusy((b) => new Set(b).add(cid));
    try {
      await apiFetch(`/api/covers/${cid}/unpublish`, { method: "POST" });
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy((b) => {
        const n = new Set(b);
        n.delete(cid);
        return n;
      });
    }
  }

  if (covers === null && !error) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">🖼️ Le mie Cover</h1>
          <p className="text-sm text-[var(--color-fg-muted)] mt-1">
            Crea copertine standalone (formato libretto 2:3). Stessi prompt
            delle copertine dei libretti KIDS.
          </p>
        </div>
        <button
          onClick={() => setShowCreate((v) => !v)}
          className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg transition-colors"
        >
          {showCreate ? "Chiudi" : "+ Nuova cover"}
        </button>
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-6">
          {error}
        </p>
      )}

      {/* FORM CREAZIONE */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-8 space-y-5"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Titolo * <span className="text-[var(--color-fg-muted)]">(sarà nell'immagine)</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={120}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Sottotitolo
              </label>
              <input
                type="text"
                value={subtitle}
                onChange={(e) => setSubtitle(e.target.value)}
                maxLength={200}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Autore</label>
              <input
                type="text"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                maxLength={120}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Descrizione breve <span className="text-[var(--color-fg-muted)]">(logline)</span>
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={1000}
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
              />
            </div>
          </div>

          {/* Stile */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Stile visivo *
            </label>
            <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
              {kidsStyles.map((s) => {
                const sample = styleSamples[s.preset_id];
                const active = selectedPresetId === s.preset_id;
                return (
                  <button
                    key={s.slug}
                    type="button"
                    onClick={() => setSelectedPresetId(s.preset_id)}
                    className={`p-2 rounded-xl border text-center transition-all overflow-hidden ${
                      active
                        ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5"
                        : "border-[var(--color-border)] bg-[var(--color-bg)] hover:border-[var(--color-accent)]/50"
                    }`}
                  >
                    {sample && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={sample}
                        alt={s.label}
                        loading="lazy"
                        className="w-full aspect-video object-cover rounded-md border border-[var(--color-border)] mb-2"
                      />
                    )}
                    <div className="text-xs font-medium">{s.label}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Cast picker */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium">
                Personaggi in cover{" "}
                <span className="text-[var(--color-fg-muted)] text-xs">
                  (max 6, opzionali)
                </span>
              </label>
              <button
                type="button"
                onClick={() => setShowCharModal(true)}
                disabled={selectedCharIds.size >= 6}
                className="text-xs bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-3 py-1.5 rounded disabled:opacity-40"
              >
                + Crea nuovo
              </button>
            </div>
            {myChars.length === 0 ? (
              <p className="text-sm text-[var(--color-fg-muted)] italic">
                Non hai ancora personaggi salvati. Usa &quot;+ Crea nuovo&quot; qui sopra per crearne uno al volo (da testo o da foto).
              </p>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {myChars.map((c) => {
                  const active = selectedCharIds.has(c.id);
                  const disabled = !active && selectedCharIds.size >= 6;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => !disabled && toggleChar(c.id)}
                      disabled={disabled}
                      className={`p-2 rounded-lg border text-left transition-colors flex gap-2 items-center ${
                        active
                          ? "border-[var(--color-accent)] bg-[var(--color-accent)]/10"
                          : disabled
                          ? "border-[var(--color-border)] opacity-40 cursor-not-allowed"
                          : "border-[var(--color-border)] bg-[var(--color-bg)] hover:border-[var(--color-accent)]/50"
                      }`}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={`/api/my-characters/${c.id}/image?t=${refreshTag}`}
                        alt={c.name}
                        className="w-10 h-10 object-cover rounded"
                      />
                      <span className="text-sm font-medium truncate">
                        {c.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-[var(--color-border)]">
            <button
              type="button"
              onClick={resetForm}
              className="px-4 py-2 text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
            >
              Annulla
            </button>
            <button
              type="submit"
              disabled={creating || !title.trim() || !selectedPresetId}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded-lg transition-colors disabled:opacity-40"
            >
              {creating ? "Generazione in corso..." : "Genera cover"}
            </button>
          </div>
        </form>
      )}

      {/* GRIGLIA COVER */}
      {covers && covers.length === 0 ? (
        <div className="text-center py-12 text-[var(--color-fg-muted)]">
          Non hai ancora creato nessuna cover. Clicca &quot;+ Nuova cover&quot;
          per iniziare.
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {covers?.map((cov) => {
            const st = STATUS_STYLE[cov.moderation_status] || STATUS_STYLE.draft;
            const isBusy = busy.has(cov.id);
            return (
              <div
                key={cov.id}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden flex flex-col"
              >
                <div className="relative bg-[var(--color-bg)]">
                  {cov.has_image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={`/api/covers/${cov.id}/image?t=${refreshTag}`}
                      alt={cov.title}
                      className="w-full aspect-[2/3] object-cover"
                    />
                  ) : (
                    <div className="w-full aspect-[2/3] flex items-center justify-center text-[var(--color-fg-muted)] text-sm">
                      Nessuna immagine
                    </div>
                  )}
                  <div
                    className="absolute top-2 right-2 text-xs px-2 py-0.5 rounded"
                    style={{
                      background: st.bg,
                      border: `1px solid ${st.border}`,
                      color: st.color,
                    }}
                  >
                    {st.label}
                  </div>
                </div>
                <div className="p-3 flex-1 flex flex-col gap-2">
                  <div className="font-semibold text-sm truncate" title={cov.title}>
                    {cov.title}
                  </div>
                  {cov.subtitle && (
                    <div className="text-xs text-[var(--color-fg-muted)] truncate">
                      {cov.subtitle}
                    </div>
                  )}
                  <div className="mt-auto flex flex-wrap gap-1.5 pt-2">
                    <button
                      onClick={() => handleRegen(cov.id)}
                      disabled={isBusy}
                      className="text-xs px-2 py-1 rounded border border-[var(--color-border)] hover:border-[var(--color-accent)] disabled:opacity-40"
                    >
                      {isBusy ? "..." : "🔄 Rigenera"}
                    </button>
                    {cov.moderation_status === "draft" ||
                    cov.moderation_status === "rejected" ? (
                      <button
                        onClick={() => setPublishingId(cov.id)}
                        disabled={isBusy || !cov.has_image}
                        className="text-xs px-2 py-1 rounded bg-[var(--color-accent)]/20 border border-[var(--color-accent)]/50 hover:bg-[var(--color-accent)]/30 disabled:opacity-40"
                      >
                        📚 Pubblica
                      </button>
                    ) : (
                      <button
                        onClick={() => handleUnpublish(cov.id)}
                        disabled={isBusy}
                        className="text-xs px-2 py-1 rounded border border-[var(--color-border)] hover:border-[var(--color-accent)] disabled:opacity-40"
                      >
                        Ritira
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(cov.id)}
                      disabled={isBusy}
                      className="text-xs px-2 py-1 rounded border border-red-900/50 text-red-400 hover:bg-red-950/30 disabled:opacity-40"
                    >
                      Elimina
                    </button>
                  </div>
                  {cov.rejection_reason && (
                    <p className="text-xs text-red-400 mt-1">
                      Motivo rifiuto: {cov.rejection_reason}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* MODAL PUBBLICAZIONE */}
      {publishingId && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-md w-full">
            <h2 className="text-lg font-semibold mb-3">Pubblica sul BookShop</h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-4">
              Scegli la categoria in cui apparirà la tua cover. Sarà
              approvata manualmente dagli admin prima di essere pubblica.
            </p>
            <select
              value={publishCategoryId}
              onChange={(e) => setPublishCategoryId(e.target.value)}
              className="w-full px-3 py-2 mb-4 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            >
              <option value="">-- scegli categoria --</option>
              {categories.map((macro) => (
                <optgroup key={macro.macro} label={macro.label}>
                  {macro.categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setPublishingId(null);
                  setPublishCategoryId("");
                }}
                className="px-4 py-2 text-sm text-[var(--color-fg-muted)]"
              >
                Annulla
              </button>
              <button
                onClick={handlePublish}
                disabled={publishing || !publishCategoryId}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded-lg disabled:opacity-40"
              >
                {publishing ? "..." : "Invia a moderazione"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL CREA NUOVO PERSONAGGIO */}
      {showCharModal && (
        <div
          className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
          onClick={() => !creatingChar && resetCharModal()}
        >
          <form
            onSubmit={handleCreateCharacter}
            onClick={(e) => e.stopPropagation()}
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-md w-full"
          >
            <h2 className="text-lg font-semibold mb-3">
              + Crea nuovo personaggio
            </h2>
            <p className="text-xs text-[var(--color-fg-muted)] mb-4">
              Costa 1 credito. Il personaggio verrà salvato nel tuo archivio
              &quot;I miei Personaggi&quot; e usato in questa cover.
            </p>

            {/* Tab selector */}
            <div className="flex gap-1 mb-4 border-b border-[var(--color-border)]">
              <button
                type="button"
                onClick={() => setCharTab("text")}
                className={`px-4 py-2 text-sm font-medium border-b-2 ${
                  charTab === "text"
                    ? "border-[var(--color-accent)] text-[var(--color-accent)]"
                    : "border-transparent text-[var(--color-fg-muted)]"
                }`}
              >
                Da descrizione
              </button>
              <button
                type="button"
                onClick={() => setCharTab("photo")}
                className={`px-4 py-2 text-sm font-medium border-b-2 ${
                  charTab === "photo"
                    ? "border-[var(--color-accent)] text-[var(--color-accent)]"
                    : "border-transparent text-[var(--color-fg-muted)]"
                }`}
              >
                Da foto reale
              </button>
            </div>

            <div className="mb-3">
              <label className="block text-sm font-medium mb-1">Nome *</label>
              <input
                type="text"
                value={newCharName}
                onChange={(e) => setNewCharName(e.target.value)}
                required
                maxLength={80}
                placeholder="Es. Lollo, Luna, Draghetto..."
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
              />
            </div>

            {charTab === "text" ? (
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">
                  Descrizione visiva *{" "}
                  <span className="text-xs text-[var(--color-fg-muted)]">
                    (aspetto fisico, colori, vestiti)
                  </span>
                </label>
                <textarea
                  value={newCharDesc}
                  onChange={(e) => setNewCharDesc(e.target.value)}
                  rows={4}
                  minLength={5}
                  required
                  maxLength={1000}
                  placeholder="Es. Bambina di 6 anni con capelli ricci castani, occhi verdi, salopette blu e maglietta a righe rosse..."
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
                />
              </div>
            ) : (
              <>
                <div className="mb-3">
                  <label className="block text-sm font-medium mb-1">
                    Foto reference *{" "}
                    <span className="text-xs text-[var(--color-fg-muted)]">
                      (JPG/PNG, max 10 MB)
                    </span>
                  </label>
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    onChange={(e) => setNewCharPhoto(e.target.files?.[0] || null)}
                    required
                    className="w-full text-sm"
                  />
                  <p className="text-xs text-[var(--color-fg-muted)] mt-1">
                    ⚠️ La foto viene usata solo per generare la reference AI, poi
                    è cancellata. Non memorizziamo foto reali.
                  </p>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-1">
                    Note{" "}
                    <span className="text-xs text-[var(--color-fg-muted)]">
                      (opzionale, es. età, professione, tratti caratteriali)
                    </span>
                  </label>
                  <textarea
                    value={newCharDesc}
                    onChange={(e) => setNewCharDesc(e.target.value)}
                    rows={2}
                    maxLength={500}
                    className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
                  />
                </div>
              </>
            )}

            {charError && (
              <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-3">
                {charError}
              </p>
            )}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={resetCharModal}
                disabled={creatingChar}
                className="px-4 py-2 text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              >
                Annulla
              </button>
              <button
                type="submit"
                disabled={
                  creatingChar ||
                  !newCharName.trim() ||
                  (charTab === "photo" && !newCharPhoto)
                }
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded disabled:opacity-40"
              >
                {creatingChar ? "Generazione..." : "Crea e usa"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
