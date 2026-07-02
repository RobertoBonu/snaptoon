"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { apiFetch, type KidsProjectDetails } from "@/lib/api";

interface CoverMetadata {
  title: string;
  subtitle: string;
  author: string;
  copyright_text: string;
}

/**
 * Pagina "Titolo & Autore" del libretto KIDS.
 *
 * L'utente inserisce:
 *   - Titolo del libretto (verrà stampato in copertina AI-baked + PDF cover
 *     + quarta di copertina)
 *   - Sottotitolo (mostrato in copertina, opzionale)
 *   - Autore (es. "Mamma di Lillo", "Zio Marco", ecc.)
 *   - Testo copyright (visibile solo nella quarta di copertina, es.
 *     "© 2026 Lillo. Tutti i diritti riservati.")
 *
 * Il logo viene gestito dall'admin a livello globale (non da qui).
 */
export default function KidsTitoloPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [details, setDetails] = useState<KidsProjectDetails | null>(null);
  const [meta, setMeta] = useState<CoverMetadata | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [d, m] = await Promise.all([
        apiFetch<KidsProjectDetails>(`/api/kids/projects/${id}/details`),
        apiFetch<CoverMetadata>(`/api/kids/projects/${id}/cover-metadata`),
      ]);
      setDetails(d);
      setMeta(m);
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function save() {
    if (!meta) return;
    setSaving(true);
    setError(null);
    setSavedMsg(null);
    try {
      await apiFetch<CoverMetadata>(
        `/api/kids/projects/${id}/cover-metadata`,
        {
          method: "PATCH",
          body: JSON.stringify(meta),
        }
      );
      setDirty(false);
      setSavedMsg("✓ Salvato");
      setTimeout(() => setSavedMsg(null), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  function update(patch: Partial<CoverMetadata>) {
    if (!meta) return;
    setMeta({ ...meta, ...patch });
    setDirty(true);
  }

  if (!meta) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-4">
        <Link
          href={`/app/kids/${id}`}
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Torna al libretto
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-1">📝 Titolo & Autore</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-8">
        {details?.name}
      </p>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      <div className="bg-[var(--color-accent)]/5 border border-[var(--color-accent)]/30 rounded-xl p-4 mb-6 text-sm">
        💡 Il <strong>titolo</strong> apparirà sulla copertina illustrata,
        sopra la pagina copertina del PDF e nella quarta di copertina. Se
        cambi il titolo dopo aver generato la cover AI, dovrai rigenerarla
        per aggiornare il testo dentro l'illustrazione.
      </div>

      <div className="space-y-5 mb-8">
        {/* Titolo */}
        <div>
          <label className="block text-sm font-semibold mb-2">
            Titolo del libretto <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={meta.title}
            onChange={(e) => update({ title: e.target.value })}
            placeholder="Es. Le avventure di Lillo nel bosco"
            maxLength={120}
            className="w-full px-4 py-2.5 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)] text-lg"
          />
          <p className="text-xs text-[var(--color-fg-muted)] mt-1">
            {meta.title.length}/120 · consigliato max 40 caratteri per la
            leggibilità in copertina
          </p>
        </div>

        {/* Sottotitolo */}
        <div>
          <label className="block text-sm font-semibold mb-2">
            Sottotitolo <span className="text-[var(--color-fg-muted)] font-normal">(opzionale)</span>
          </label>
          <input
            type="text"
            value={meta.subtitle}
            onChange={(e) => update({ subtitle: e.target.value })}
            placeholder="Es. Una storia di amicizia"
            maxLength={200}
            className="w-full px-4 py-2.5 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)]"
          />
        </div>

        {/* Autore */}
        <div>
          <label className="block text-sm font-semibold mb-2">
            Autore <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            value={meta.author}
            onChange={(e) => update({ author: e.target.value })}
            placeholder="Es. Mamma di Lillo"
            maxLength={120}
            className="w-full px-4 py-2.5 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)]"
          />
          <p className="text-xs text-[var(--color-fg-muted)] mt-1">
            Come firmi il libretto (es. "Mamma di Lillo", "Zio Marco",
            "Nonna Anna"). Apparirà su copertina e quarta.
          </p>
        </div>

        {/* Copyright */}
        <div>
          <label className="block text-sm font-semibold mb-2">
            Testo per la quarta di copertina{" "}
            <span className="text-[var(--color-fg-muted)] font-normal">
              (opzionale)
            </span>
          </label>
          <textarea
            value={meta.copyright_text}
            onChange={(e) => update({ copyright_text: e.target.value })}
            placeholder="Es. © 2026 Famiglia Rossi. Tutti i diritti riservati. Per Lillo, con amore."
            rows={3}
            maxLength={500}
            className="w-full px-4 py-2.5 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)] text-sm"
          />
          <p className="text-xs text-[var(--color-fg-muted)] mt-1">
            {meta.copyright_text.length}/500 · testo che verrà stampato
            sulla quarta di copertina del PDF
          </p>
        </div>
      </div>

      {/* Save bar */}
      <div className="flex items-center gap-3 justify-between">
        <div>
          {savedMsg && (
            <span className="text-green-400 text-sm">{savedMsg}</span>
          )}
        </div>
        <div className="flex gap-2">
          <Link
            href={`/app/kids/${id}`}
            className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-5 py-2.5 transition-colors"
          >
            Annulla
          </Link>
          <button
            onClick={save}
            disabled={!dirty || saving}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded-lg disabled:opacity-40"
          >
            {saving ? "Salvo..." : "💾 Salva"}
          </button>
        </div>
      </div>
    </div>
  );
}
