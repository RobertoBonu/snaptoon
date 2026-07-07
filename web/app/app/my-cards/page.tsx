"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Card {
  id: string;
  name: string;
  character_type: string;
  caption: string;
  author_display: string;
  progressive_number: number;
  has_rendered: boolean;
  has_reference: boolean;
  moderation_status: string;
  rejection_reason: string;
  bookshop_category_id: string | null;
  bookshop_category_label: string | null;
  bookshop_category_macro: string | null;
  image_url: string;
  read_url: string;
  created_at: string;
}

interface MacroGroup {
  macro: string;
  label: string;
  categories: { id: string; label: string }[];
}

interface KidsStyle {
  slug: string;
  label: string;
  preset_id: string;
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

export default function MyCardsPage() {
  const [cards, setCards] = useState<Card[] | null>(null);
  const [categories, setCategories] = useState<MacroGroup[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [refreshTag, setRefreshTag] = useState(Date.now());

  // Create form
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [ctype, setCtype] = useState("");
  const [caption, setCaption] = useState("");
  const [reference, setReference] = useState<File | null>(null);
  const [creating, setCreating] = useState(false);
  const [dragging, setDragging] = useState(false);

  // Stili KIDS + sample thumbnail (dallo stesso endpoint del wizard KIDS)
  const [kidsStyles, setKidsStyles] = useState<KidsStyle[]>([]);
  const [styleSamples, setStyleSamples] = useState<Record<string, string>>({});
  const [selectedStyleSlug, setSelectedStyleSlug] = useState<string>("");

  // Publish modal
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [publishCategoryId, setPublishCategoryId] = useState<string>("");
  const [publishing, setPublishing] = useState(false);

  // Busy tracking
  const [busy, setBusy] = useState<Set<string>>(new Set());

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<{ cards: Card[] }>("/api/cards/mine");
      setCards(d.cards);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
    fetch("/api/bookshop/categories")
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { macros: MacroGroup[] } | null) => {
        if (d) setCategories(d.macros);
      })
      .catch(() => {});

    // Stili KIDS (stesso endpoint usato dal wizard KIDS)
    fetch("/api/kids/styles")
      .then((r) => (r.ok ? r.json() : null))
      .then((d: KidsStyle[] | null) => {
        if (d) setKidsStyles(d);
      })
      .catch(() => {});

    // Sample thumbnail per stile (dallo stesso endpoint del wizard KIDS)
    fetch("/api/styles/samples?flow=kids")
      .then((r) => (r.ok ? r.json() : null))
      .then(
        (d: { samples: { style_preset_id: string; image_url: string }[] } | null) => {
          if (!d) return;
          const map: Record<string, string> = {};
          for (const s of d.samples) map[s.style_preset_id] = s.image_url;
          setStyleSamples(map);
        },
      )
      .catch(() => {});
  }, []);

  function mark(id: string, on: boolean) {
    setBusy((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !ctype.trim() || !selectedStyleSlug) return;
    setCreating(true);
    setError(null);
    try {
      const preset = kidsStyles.find((s) => s.slug === selectedStyleSlug);
      const fd = new FormData();
      fd.append("name", name);
      fd.append("character_type", ctype);
      fd.append("caption", caption);
      if (preset) fd.append("style_preset_id", preset.preset_id);
      if (reference) fd.append("reference", reference);
      const res = await fetch("/api/cards", {
        method: "POST",
        body: fd,
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      setName("");
      setCtype("");
      setCaption("");
      setReference(null);
      setSelectedStyleSlug("");
      setShowCreate(false);
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  // Validazione + assegnazione file (usata sia da drag&drop sia da click)
  function acceptFile(file: File | null) {
    if (!file) {
      setReference(null);
      return;
    }
    const okMimes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!okMimes.includes(file.type)) {
      setError("Formato non supportato. Usa PNG, JPEG o WEBP.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File troppo grande (max 10 MB).");
      return;
    }
    setError(null);
    setReference(file);
  }

  async function regenerate(c: Card) {
    if (!confirm(`Rigenerare la card #${String(c.progressive_number).padStart(4, "0")}? Costa 1 credito.`))
      return;
    mark(c.id, true);
    try {
      await apiFetch(`/api/cards/${c.id}/regenerate`, { method: "POST" });
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      mark(c.id, false);
    }
  }

  async function submitPublish() {
    if (!publishingId || !publishCategoryId) return;
    setPublishing(true);
    setError(null);
    try {
      await apiFetch(`/api/cards/${publishingId}/publish`, {
        method: "POST",
        body: JSON.stringify({ bookshop_category_id: publishCategoryId }),
      });
      setPublishingId(null);
      setPublishCategoryId("");
      await load();
      alert("Richiesta di pubblicazione inviata! Un admin la esaminerà a breve.");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPublishing(false);
    }
  }

  async function unpublish(c: Card) {
    if (!confirm("Ritirare la card dalla pubblicazione?")) return;
    try {
      await apiFetch(`/api/cards/${c.id}/unpublish`, { method: "POST" });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function remove(c: Card) {
    if (
      !confirm(
        `Eliminare la card "${c.name}" (#${String(c.progressive_number).padStart(4, "0")})?`,
      )
    )
      return;
    try {
      const res = await fetch(`/api/cards/${c.id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-start mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold mb-1">🎴 Le mie figurine</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Card collezionabili 9:16 con banner nome, autore, tre stelle e
            numero progressivo. Costo: 1 credito a card. Pubblicabili sul
            BookShop previa approvazione admin.
          </p>
        </div>
        {!showCreate && (
          <button
            onClick={() => setShowCreate(true)}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg"
          >
            + Nuova figurina (1 cr)
          </button>
        )}
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {/* Form crea */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6 max-w-2xl space-y-3"
        >
          <h2 className="font-semibold text-lg mb-2">✨ Nuova figurina</h2>
          <div>
            <label className="block text-sm font-semibold mb-1">
              Nome del personaggio *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              maxLength={120}
              placeholder="Es. NEO"
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">
              Tipo di personaggio *
            </label>
            <input
              type="text"
              value={ctype}
              onChange={(e) => setCtype(e.target.value)}
              required
              maxLength={120}
              placeholder="Es. GATTO CURIOSO"
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">
              Didascalia (visualizzata sulla card)
            </label>
            <textarea
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              rows={2}
              maxLength={200}
              placeholder="Es. Riesce a nascondersi in posti assurdi"
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-none text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-2">
              Stile visivo *
            </label>
            <p className="text-xs text-[var(--color-fg-muted)] mb-2">
              Come sarà disegnato il personaggio. Il layout della card
              (banner, badge, numero) resta identico per tutte.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {kidsStyles.map((s) => {
                const sample = styleSamples[s.preset_id];
                const active = selectedStyleSlug === s.slug;
                return (
                  <button
                    key={s.slug}
                    type="button"
                    onClick={() => setSelectedStyleSlug(s.slug)}
                    className={`p-1.5 rounded-lg border text-center transition-all overflow-hidden ${
                      active
                        ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5"
                        : "border-[var(--color-border)] bg-[var(--color-bg)] hover:border-[var(--color-accent)]/50"
                    }`}
                  >
                    {sample ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={sample}
                        alt={s.label}
                        loading="lazy"
                        className="w-full aspect-video object-cover rounded mb-1 border border-[var(--color-border)]"
                      />
                    ) : (
                      <div
                        className="w-full aspect-video rounded mb-1 flex items-center justify-center bg-[var(--color-bg-elev)] text-[var(--color-fg-muted)]"
                        style={{ fontSize: 11 }}
                      >
                        (no preview)
                      </div>
                    )}
                    <div className="text-xs font-medium">{s.label}</div>
                  </button>
                );
              })}
            </div>
            {kidsStyles.length === 0 && (
              <p className="text-xs text-yellow-400 mt-1">
                Nessuno stile disponibile.
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-semibold mb-1">
              Reference personaggio (facoltativa)
            </label>
            <p className="text-xs text-[var(--color-fg-muted)] mb-2">
              Se carichi una foto (o un&apos;illustrazione), l&apos;AI cercherà
              di replicare il soggetto sulla card.
            </p>
            <label
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragging(false);
                acceptFile(e.dataTransfer.files?.[0] || null);
              }}
              className={`block w-full cursor-pointer rounded-lg border-2 border-dashed transition-colors ${
                dragging
                  ? "border-[var(--color-accent)] bg-[var(--color-accent)]/10"
                  : "border-[var(--color-border)] bg-[var(--color-bg)] hover:border-[var(--color-accent)]/60 hover:bg-[var(--color-bg-elev)]"
              } px-4 py-6 text-center`}
            >
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={(e) => acceptFile(e.target.files?.[0] || null)}
                className="hidden"
              />
              {reference ? (
                <div className="flex items-center justify-center gap-3 flex-wrap">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={URL.createObjectURL(reference)}
                    alt="preview"
                    className="w-16 h-16 object-cover rounded border border-[var(--color-border)]"
                  />
                  <div className="text-left">
                    <p className="text-sm font-medium">{reference.name}</p>
                    <p className="text-xs text-[var(--color-fg-muted)]">
                      {Math.round(reference.size / 1024)} KB · click o
                      trascina per sostituire
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      setReference(null);
                    }}
                    className="text-xs text-[var(--color-fg-muted)] hover:text-red-400 underline"
                  >
                    rimuovi
                  </button>
                </div>
              ) : (
                <div>
                  <div className="text-3xl mb-1">📁</div>
                  <p className="text-sm font-medium mb-0.5">
                    Trascina qui la foto del personaggio
                  </p>
                  <p className="text-xs text-[var(--color-fg-muted)]">
                    o clicca per selezionarla (PNG · JPEG · WEBP, max 10 MB)
                  </p>
                </div>
              )}
            </label>
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={
                creating ||
                !name.trim() ||
                !ctype.trim() ||
                !selectedStyleSlug
              }
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50"
            >
              {creating ? "Genero..." : "✨ Crea figurina (1 cr)"}
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="text-[var(--color-fg-muted)] px-4 py-2"
            >
              Annulla
            </button>
          </div>
        </form>
      )}

      {/* Griglia card */}
      {cards === null ? (
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      ) : cards.length === 0 ? (
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <div className="text-5xl mb-4 opacity-30">🎴</div>
          <p className="text-[var(--color-fg-muted)]">
            Nessuna figurina ancora creata.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {cards.map((c) => {
            const isBusy = busy.has(c.id);
            const st = STATUS_STYLE[c.moderation_status];
            return (
              <div
                key={c.id}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden"
              >
                {/* Card image 9:16 (letterbox su lato lungo se 2:3 sorgente) */}
                <div
                  style={{
                    position: "relative",
                    aspectRatio: "9 / 16",
                    background: "#0D1017",
                    overflow: "hidden",
                  }}
                >
                  {c.has_rendered ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={`${c.image_url}?variant=thumb&t=${refreshTag}`}
                      alt={c.name}
                      loading="lazy"
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        opacity: isBusy ? 0.3 : 1,
                      }}
                    />
                  ) : (
                    <div
                      style={{
                        position: "absolute",
                        inset: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#64748B",
                        fontSize: 13,
                      }}
                    >
                      Nessuna immagine
                    </div>
                  )}
                  {isBusy && (
                    <div
                      style={{
                        position: "absolute",
                        inset: 0,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "rgba(0,0,0,0.4)",
                        color: "#F1F5F9",
                        fontSize: 13,
                      }}
                    >
                      Elaboro...
                    </div>
                  )}
                  <span
                    style={{
                      position: "absolute",
                      top: 8,
                      right: 8,
                      background: "rgba(13,16,23,0.85)",
                      border: "1px solid #1E2436",
                      color: "#CBD5E1",
                      fontSize: 11,
                      fontWeight: 700,
                      padding: "3px 8px",
                      borderRadius: 6,
                      fontFamily: "monospace",
                    }}
                  >
                    #{String(c.progressive_number).padStart(4, "0")}
                  </span>
                </div>
                <div className="p-3 space-y-2">
                  <div>
                    <h3 className="font-semibold text-base leading-tight">
                      {c.name}
                    </h3>
                    <p className="text-xs text-[var(--color-fg-muted)]">
                      {c.character_type}
                    </p>
                  </div>
                  {st && (
                    <span
                      style={{
                        display: "inline-block",
                        fontSize: 10,
                        fontWeight: 700,
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                        background: st.bg,
                        border: `1px solid ${st.border}`,
                        color: st.color,
                        borderRadius: 100,
                        padding: "2px 8px",
                      }}
                    >
                      {st.label}
                      {c.bookshop_category_label && ` · ${c.bookshop_category_label}`}
                    </span>
                  )}
                  {c.moderation_status === "rejected" && c.rejection_reason && (
                    <p className="text-xs text-red-300">
                      Motivo: {c.rejection_reason}
                    </p>
                  )}
                  <div className="flex flex-wrap gap-1 pt-1">
                    {c.moderation_status !== "published" && c.has_rendered && (
                      <button
                        onClick={() => regenerate(c)}
                        disabled={isBusy}
                        className="text-xs border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-2 py-1 rounded disabled:opacity-50"
                      >
                        🔄 Rigenera (1cr)
                      </button>
                    )}
                    {(c.moderation_status === "draft" ||
                      c.moderation_status === "rejected") &&
                      c.has_rendered && (
                        <button
                          onClick={() => {
                            setPublishingId(c.id);
                            setPublishCategoryId(c.bookshop_category_id || "");
                          }}
                          className="text-xs bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold px-2 py-1 rounded"
                        >
                          🌐 Pubblica
                        </button>
                      )}
                    {(c.moderation_status === "pending" ||
                      c.moderation_status === "published") && (
                      <button
                        onClick={() => unpublish(c)}
                        className="text-xs border border-[var(--color-border)] hover:border-red-400 hover:text-red-400 text-[var(--color-fg-muted)] px-2 py-1 rounded"
                      >
                        🚫 Ritira
                      </button>
                    )}
                    <button
                      onClick={() => remove(c)}
                      className="text-xs text-[var(--color-fg-muted)] hover:text-red-400 px-2 py-1"
                    >
                      🗑
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modale publish */}
      {publishingId && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => (publishing ? null : setPublishingId(null))}
        >
          <div
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-lg w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold mb-2">
              🌐 Pubblica figurina sul BookShop
            </h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-4">
              Un admin approverà la richiesta prima della pubblicazione. Scegli
              una categoria per far trovare la card ai lettori giusti.
            </p>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-semibold mb-1">
                  Categoria BookShop *
                </label>
                <select
                  value={publishCategoryId}
                  onChange={(e) => setPublishCategoryId(e.target.value)}
                  required
                  className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
                >
                  <option value="">— Scegli una categoria —</option>
                  {categories.map((m) => (
                    <optgroup key={m.macro} label={m.label}>
                      {m.categories.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.label}
                        </option>
                      ))}
                    </optgroup>
                  ))}
                </select>
                {categories.every((m) => m.categories.length === 0) && (
                  <p className="text-xs text-yellow-400 mt-1">
                    Nessuna categoria disponibile. Chiedi a un admin di
                    crearne.
                  </p>
                )}
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={submitPublish}
                  disabled={publishing || !publishCategoryId}
                  className="bg-[var(--color-accent)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded disabled:opacity-50"
                >
                  {publishing ? "Invio..." : "🌐 Invia per approvazione"}
                </button>
                <button
                  onClick={() => setPublishingId(null)}
                  disabled={publishing}
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
