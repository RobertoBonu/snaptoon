"use client";

import { use, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface CoverMetadata {
  title: string;
  subtitle: string;
  author: string;
  copyright_text: string;
  has_illustration: boolean;
}

export default function CopertinaPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [meta, setMeta] = useState<CoverMetadata | null>(null);
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [author, setAuthor] = useState("");
  const [copyrightText, setCopyrightText] = useState("");
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  async function load() {
    try {
      setError(null);
      const m = await apiFetch<CoverMetadata>(
        `/api/projects/${slug}/cover-metadata`,
      );
      setMeta(m);
      setTitle(m.title);
      setSubtitle(m.subtitle);
      setAuthor(m.author);
      setCopyrightText(m.copyright_text);
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, [slug]);

  async function handleSaveMeta() {
    setSaving(true);
    setError(null);
    try {
      await apiFetch(`/api/projects/${slug}/cover-metadata`, {
        method: "PATCH",
        body: JSON.stringify({
          title,
          subtitle,
          author,
          copyright_text: copyrightText,
        }),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerate() {
    if (dirty) {
      if (!confirm("Ci sono modifiche non salvate. Salvo prima?")) return;
      await handleSaveMeta();
    }
    setGenerating(true);
    setError(null);
    try {
      await apiFetch(`/api/projects/${slug}/generate-cover`, {
        method: "POST",
      });
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  }

  async function handleDeleteCover() {
    if (!confirm("Eliminare la copertina generata? (i metadati restano)"))
      return;
    try {
      const res = await fetch(`/api/projects/${slug}/cover`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  if (!meta) {
    return <p className="text-[var(--color-fg-muted)]">Caricamento...</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">Copertina</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          Titolo, sottotitolo, autore e copyright del fumetto. Verranno
          stampati direttamente dall&apos;AI sulla copertina generata (top =
          titolo, bottom = autore). Il testo copyright appare nella quarta.
        </p>
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2">
          {error}
        </p>
      )}

      {/* Metadata */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">📝 Testi copertina</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-1">
              Titolo *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setDirty(true);
              }}
              maxLength={255}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">
              Sottotitolo
            </label>
            <input
              type="text"
              value={subtitle}
              onChange={(e) => {
                setSubtitle(e.target.value);
                setDirty(true);
              }}
              maxLength={255}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">
              Autore *
            </label>
            <input
              type="text"
              value={author}
              onChange={(e) => {
                setAuthor(e.target.value);
                setDirty(true);
              }}
              maxLength={255}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold mb-1">
              Testo copyright (per la quarta di copertina)
            </label>
            <textarea
              value={copyrightText}
              onChange={(e) => {
                setCopyrightText(e.target.value);
                setDirty(true);
              }}
              maxLength={1000}
              rows={2}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)] resize-none"
            />
          </div>

          <button
            onClick={handleSaveMeta}
            disabled={saving || !dirty || !title.trim() || !author.trim()}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded disabled:opacity-50"
          >
            {saving ? "Salvo..." : "💾 Salva testi"}
          </button>
        </div>
      </section>

      {/* Generation + preview */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">🎨 Illustrazione</h2>

        <div className="flex gap-6 items-start flex-wrap">
          <div className="w-64 aspect-[2/3] bg-[var(--color-bg)] border border-[var(--color-border)] rounded overflow-hidden flex items-center justify-center">
            {meta.has_illustration ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`/api/projects/${slug}/cover-image?t=${refreshTag}`}
                alt="Copertina"
                className="w-full h-full object-cover"
              />
            ) : (
              <p className="text-xs text-[var(--color-fg-muted)] text-center px-4">
                Nessuna copertina generata
              </p>
            )}
          </div>

          <div className="flex-1 min-w-[240px] flex flex-col gap-2">
            <p className="text-sm text-[var(--color-fg-muted)] mb-2">
              La copertina viene generata dall&apos;AI usando titolo, autore e
              i reference dei personaggi. Se cambi i testi, ri-genera per
              vederli aggiornati. Il logo di sistema (se attivato in Admin) è
              sovrapposto solo al momento dello scaricamento PDF.
            </p>
            <button
              onClick={handleGenerate}
              disabled={generating || !title.trim() || !author.trim()}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded disabled:opacity-50 text-left"
            >
              {generating
                ? "Genero copertina..."
                : meta.has_illustration
                  ? "🔄 Rigenera copertina"
                  : "✨ Genera copertina"}
            </button>
            {meta.has_illustration && (
              <button
                onClick={handleDeleteCover}
                className="text-sm border border-[var(--color-border)] hover:border-red-400 hover:text-red-400 text-[var(--color-fg-muted)] px-4 py-2 rounded text-left"
              >
                🗑 Elimina copertina generata
              </button>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
