"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface SystemSettings {
  has_logo: boolean;
  default_copyright_text: string;
  back_cover_template: string;
}

export default function AdminSistemaPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [defaultCopyright, setDefaultCopyright] = useState("");
  const [backCoverTemplate, setBackCoverTemplate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  async function load() {
    try {
      setError(null);
      const s = await apiFetch<SystemSettings>("/api/admin/system-settings");
      setSettings(s);
      setDefaultCopyright(s.default_copyright_text);
      setBackCoverTemplate(s.back_cover_template);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleLogoUpload(file: File) {
    const okTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!okTypes.includes(file.type)) {
      setError("Formato non supportato. Usa PNG, JPEG o WEBP.");
      return;
    }
    if (file.size > 4 * 1024 * 1024) {
      setError("Logo troppo grande (max 4 MB).");
      return;
    }
    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/admin/logo", {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      setSuccess("Logo caricato.");
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(false);
    }
  }

  async function handleLogoDelete() {
    if (!confirm("Eliminare il logo di sistema?")) return;
    try {
      const res = await fetch("/api/admin/logo", {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSuccess("Logo eliminato.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleSaveTexts() {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await apiFetch("/api/admin/system-settings", {
        method: "PATCH",
        body: JSON.stringify({
          default_copyright_text: defaultCopyright,
          back_cover_template: backCoverTemplate,
        }),
      });
      setSuccess("Testi salvati.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  if (!settings) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-4">
        <Link
          href="/app/admin"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Pannello admin
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-2">⚙️ Sistema</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-8">
        Logo di sistema + testi default per copertine e quarta di copertina
        dei libretti. L'utente finale non può modificarli.
      </p>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}
      {success && (
        <p className="text-green-400 text-sm bg-green-950/30 border border-green-900/50 rounded px-3 py-2 mb-4">
          ✓ {success}
        </p>
      )}

      {/* Sezione Logo */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-2">🖼 Logo di sistema</h2>
        <p className="text-sm text-[var(--color-fg-muted)] mb-4">
          Sarà stampato sulla copertina e sulla quarta di copertina di ogni
          libretto. Formato: PNG, JPEG o WEBP (max 4 MB). Sfondo trasparente
          consigliato.
        </p>

        <div className="flex gap-6 items-start flex-wrap">
          <div className="w-40 h-40 bg-[var(--color-bg)] border border-[var(--color-border)] rounded overflow-hidden flex items-center justify-center">
            {settings.has_logo ? (
              <img
                src={`/api/admin/logo?t=${refreshTag}`}
                alt="Logo di sistema"
                className="max-w-full max-h-full object-contain"
              />
            ) : (
              <p className="text-xs text-[var(--color-fg-muted)] text-center px-2">
                Nessun logo
              </p>
            )}
          </div>

          <div className="flex-1 min-w-[200px] flex flex-col gap-2">
            <label
              className={`inline-block text-sm bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-medium px-4 py-2 rounded cursor-pointer text-center ${
                uploading ? "opacity-50" : ""
              }`}
            >
              {uploading
                ? "Carico..."
                : settings.has_logo
                  ? "📁 Sostituisci logo"
                  : "📁 Carica logo"}
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleLogoUpload(f);
                  e.target.value = "";
                }}
                disabled={uploading}
                className="hidden"
              />
            </label>
            {settings.has_logo && (
              <button
                onClick={handleLogoDelete}
                className="text-sm border border-[var(--color-border)] hover:border-red-400 hover:text-red-400 text-[var(--color-fg-muted)] px-4 py-2 rounded transition-colors"
              >
                🗑 Rimuovi logo
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Sezione Testi */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">📝 Testi default</h2>

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-semibold mb-2">
              Copyright suggerito per nuovi libretti
            </label>
            <p className="text-xs text-[var(--color-fg-muted)] mb-2">
              Verrà proposto come placeholder nel campo "Testo per la quarta
              di copertina" quando l'utente crea un libretto. L'utente potrà
              sovrascriverlo.
            </p>
            <textarea
              value={defaultCopyright}
              onChange={(e) => setDefaultCopyright(e.target.value)}
              rows={2}
              maxLength={1000}
              placeholder="Es. © 2026 SnapToon. Tutti i diritti riservati."
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm focus:outline-none focus:border-[var(--color-accent)]"
            />
            <p className="text-xs text-[var(--color-fg-muted)] mt-1">
              {defaultCopyright.length}/1000
            </p>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2">
              Testo editoriale per la quarta di copertina
            </label>
            <p className="text-xs text-[var(--color-fg-muted)] mb-2">
              Testo che appare sotto il titolo/autore sulla quarta di
              copertina di ogni libretto (es. descrizione editore, tagline,
              disclaimer stampa). Sarà lo stesso su tutti i libretti.
            </p>
            <textarea
              value={backCoverTemplate}
              onChange={(e) => setBackCoverTemplate(e.target.value)}
              rows={4}
              maxLength={2000}
              placeholder="Es. SnapToon — Dall'idea al fumetto in uno snap. Creato con AI e con amore."
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm focus:outline-none focus:border-[var(--color-accent)]"
            />
            <p className="text-xs text-[var(--color-fg-muted)] mt-1">
              {backCoverTemplate.length}/2000
            </p>
          </div>

          <button
            onClick={handleSaveTexts}
            disabled={saving}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded disabled:opacity-50"
          >
            {saving ? "Salvo..." : "💾 Salva testi"}
          </button>
        </div>
      </section>
    </div>
  );
}
