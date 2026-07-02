"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface LogoParams {
  logo_show: boolean;
  cover_size_px: number;
  cover_x: number;
  cover_y: number;
  back_size_px: number;
  back_x: number;
  back_y: number;
}

interface SystemSettings {
  has_logo_kids: boolean;
  has_logo_pro: boolean;
  default_copyright_text: string;
  back_cover_template: string;
  logo_params_kids: LogoParams;
  logo_params_pro: LogoParams;
}

const CANVAS_W = 1024;
const CANVAS_H = 1536;

type Kind = "kids" | "pro";

export default function AdminSistemaPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [defaultCopyright, setDefaultCopyright] = useState("");
  const [backCoverTemplate, setBackCoverTemplate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
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
        Logo di sistema e testi default per copertine e quarta di copertina.
        Logo separato per libretti KIDS e progetti Pro. L&apos;utente finale
        non può modificarli.
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

      {/* Logo KIDS */}
      <LogoBlock
        kind="kids"
        label="Logo libretti KIDS"
        icon="📖"
        hasLogo={settings.has_logo_kids}
        params={settings.logo_params_kids}
        refreshTag={refreshTag}
        onFeedback={(err, ok) => {
          setError(err);
          setSuccess(ok);
        }}
        onChanged={async () => {
          setRefreshTag(Date.now());
          await load();
        }}
      />

      {/* Logo Pro */}
      <LogoBlock
        kind="pro"
        label="Logo fumetti Pro"
        icon="💥"
        hasLogo={settings.has_logo_pro}
        params={settings.logo_params_pro}
        refreshTag={refreshTag}
        onFeedback={(err, ok) => {
          setError(err);
          setSuccess(ok);
        }}
        onChanged={async () => {
          setRefreshTag(Date.now());
          await load();
        }}
      />

      {/* Testi (condivisi) */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">
          📝 Testi default (condivisi KIDS + Pro)
        </h2>

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-semibold mb-2">
              Copyright suggerito per nuovi progetti
            </label>
            <p className="text-xs text-[var(--color-fg-muted)] mb-2">
              Placeholder proposto nel wizard di creazione (libretti KIDS +
              fumetti Pro). L&apos;utente può sovrascriverlo.
            </p>
            <textarea
              value={defaultCopyright}
              onChange={(e) => setDefaultCopyright(e.target.value)}
              rows={2}
              maxLength={1000}
              placeholder="Es. 2026 SnapToon. Tutti i diritti riservati."
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
              Testo che appare sotto titolo/autore sulla quarta di copertina
              di ogni progetto (KIDS + Pro).
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

function LogoBlock({
  kind,
  label,
  icon,
  hasLogo,
  params,
  refreshTag,
  onFeedback,
  onChanged,
}: {
  kind: Kind;
  label: string;
  icon: string;
  hasLogo: boolean;
  params: LogoParams;
  refreshTag: number;
  onFeedback: (err: string | null, ok: string | null) => void;
  onChanged: () => Promise<void>;
}) {
  const [uploading, setUploading] = useState(false);
  const [savingParams, setSavingParams] = useState(false);
  const [local, setLocal] = useState<LogoParams>(params);

  useEffect(() => {
    setLocal(params);
  }, [params]);

  async function handleUpload(file: File) {
    const okTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!okTypes.includes(file.type)) {
      onFeedback("Formato non supportato. Usa PNG, JPEG o WEBP.", null);
      return;
    }
    if (file.size > 4 * 1024 * 1024) {
      onFeedback("Logo troppo grande (max 4 MB).", null);
      return;
    }
    setUploading(true);
    onFeedback(null, null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`/api/admin/logo/${kind}`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      onFeedback(null, `Logo ${kind.toUpperCase()} caricato.`);
      await onChanged();
    } catch (e) {
      onFeedback(e instanceof Error ? e.message : String(e), null);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Eliminare il logo ${kind.toUpperCase()}?`)) return;
    try {
      const res = await fetch(`/api/admin/logo/${kind}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      onFeedback(null, `Logo ${kind.toUpperCase()} eliminato.`);
      await onChanged();
    } catch (e) {
      onFeedback(e instanceof Error ? e.message : String(e), null);
    }
  }

  async function handleSaveParams() {
    setSavingParams(true);
    onFeedback(null, null);
    try {
      await apiFetch(`/api/admin/logo-params/${kind}`, {
        method: "PATCH",
        body: JSON.stringify(local),
      });
      onFeedback(null, `Parametri logo ${kind.toUpperCase()} salvati.`);
      await onChanged();
    } catch (e) {
      onFeedback(e instanceof Error ? e.message : String(e), null);
    } finally {
      setSavingParams(false);
    }
  }

  function upd<K extends keyof LogoParams>(k: K, v: LogoParams[K]) {
    setLocal({ ...local, [k]: v });
  }

  return (
    <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
      <h2 className="text-lg font-semibold mb-2">
        {icon} {label}
      </h2>
      <p className="text-sm text-[var(--color-fg-muted)] mb-4">
        Compositato sulla copertina e sulla quarta di copertina di ogni
        progetto {kind === "kids" ? "KIDS" : "Pro"}. Canvas di riferimento{" "}
        <strong>
          {CANVAS_W} × {CANVAS_H} px
        </strong>
        .
      </p>

      <div className="flex gap-6 items-start flex-wrap mb-4">
        <div className="w-40 h-40 bg-[var(--color-bg)] border border-[var(--color-border)] rounded overflow-hidden flex items-center justify-center">
          {hasLogo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={`/api/admin/logo/${kind}?t=${refreshTag}`}
              alt={`Logo ${kind}`}
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
              : hasLogo
                ? "📁 Sostituisci logo"
                : "📁 Carica logo"}
            <input
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleUpload(f);
                e.target.value = "";
              }}
              disabled={uploading}
              className="hidden"
            />
          </label>
          {hasLogo && (
            <button
              onClick={handleDelete}
              className="text-sm border border-[var(--color-border)] hover:border-red-400 hover:text-red-400 text-[var(--color-fg-muted)] px-4 py-2 rounded"
            >
              🗑 Rimuovi logo
            </button>
          )}
        </div>
      </div>

      {hasLogo && (
        <div className="border-t border-[var(--color-border)] pt-4">
          <div className="flex items-center gap-3 mb-4">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={local.logo_show}
                onChange={(e) => upd("logo_show", e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[var(--color-border)] peer-checked:bg-[var(--color-accent)] rounded-full peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
            <span className="font-semibold text-sm">
              Mostra logo su copertina e quarta
            </span>
          </div>

          <div className="mb-6">
            <h3 className="text-sm font-semibold mb-2">📕 Copertina</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <NumberField
                label="Dimensione (px lato lungo)"
                value={local.cover_size_px}
                onChange={(v) => upd("cover_size_px", v)}
              />
              <NumberField
                label={`X (0-${CANVAS_W})`}
                value={local.cover_x}
                onChange={(v) => upd("cover_x", v)}
              />
              <NumberField
                label={`Y (0-${CANVAS_H})`}
                value={local.cover_y}
                onChange={(v) => upd("cover_y", v)}
              />
            </div>
          </div>

          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2">🏷 Quarta</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <NumberField
                label="Dimensione (px lato lungo)"
                value={local.back_size_px}
                onChange={(v) => upd("back_size_px", v)}
              />
              <NumberField
                label={`X (0-${CANVAS_W})`}
                value={local.back_x}
                onChange={(v) => upd("back_x", v)}
              />
              <NumberField
                label={`Y (0-${CANVAS_H})`}
                value={local.back_y}
                onChange={(v) => upd("back_y", v)}
              />
            </div>
          </div>

          <button
            onClick={handleSaveParams}
            disabled={savingParams}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50 text-sm"
          >
            {savingParams
              ? "Salvo..."
              : `💾 Salva parametri ${kind.toUpperCase()}`}
          </button>
        </div>
      )}
    </section>
  );
}

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <label className="block text-xs font-semibold mb-1 text-[var(--color-fg-muted)]">
        {label}
      </label>
      <input
        type="number"
        value={value}
        onChange={(e) => {
          const v = parseInt(e.target.value, 10);
          if (!isNaN(v)) onChange(v);
        }}
        className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm font-mono focus:outline-none focus:border-[var(--color-accent)]"
      />
    </div>
  );
}
