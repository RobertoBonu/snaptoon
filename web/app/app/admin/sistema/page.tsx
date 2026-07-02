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
  has_logo: boolean;
  default_copyright_text: string;
  back_cover_template: string;
  logo_params: LogoParams;
}

const CANVAS_W = 1024;
const CANVAS_H = 1536;

export default function AdminSistemaPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [defaultCopyright, setDefaultCopyright] = useState("");
  const [backCoverTemplate, setBackCoverTemplate] = useState("");
  const [logoParams, setLogoParams] = useState<LogoParams | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savingLogo, setSavingLogo] = useState(false);
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  async function load() {
    try {
      setError(null);
      const s = await apiFetch<SystemSettings>("/api/admin/system-settings");
      setSettings(s);
      setDefaultCopyright(s.default_copyright_text);
      setBackCoverTemplate(s.back_cover_template);
      setLogoParams(s.logo_params);
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

  async function handleSaveLogoParams() {
    if (!logoParams) return;
    setSavingLogo(true);
    setError(null);
    setSuccess(null);
    try {
      await apiFetch("/api/admin/logo-params", {
        method: "PATCH",
        body: JSON.stringify(logoParams),
      });
      setSuccess("Parametri logo salvati.");
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingLogo(false);
    }
  }

  function updateLogoParam<K extends keyof LogoParams>(
    key: K,
    value: LogoParams[K],
  ) {
    if (!logoParams) return;
    setLogoParams({ ...logoParams, [key]: value });
  }

  if (!settings || !logoParams) {
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
        dei libretti. L&apos;utente finale non può modificarli.
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

      {/* Sezione Logo: upload + preview */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-2">🏷 Logo di sistema</h2>
        <p className="text-sm text-[var(--color-fg-muted)] mb-4">
          Il logo viene compositato in PIL sulla{" "}
          <strong>copertina</strong> del libretto e sulla{" "}
          <strong>quarta di copertina</strong>, con dimensione (px) e
          posizione (X, Y) controllabili qui sotto. PNG con trasparenza
          consigliato. Vale per tutti i libretti KIDS.
        </p>

        <div className="flex gap-6 items-start flex-wrap">
          <div className="w-40 h-40 bg-[var(--color-bg)] border border-[var(--color-border)] rounded overflow-hidden flex items-center justify-center">
            {settings.has_logo ? (
              // eslint-disable-next-line @next/next/no-img-element
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

      {/* Sezione parametri logo: toggle + dimensione px + posizione X,Y */}
      {settings.has_logo && (
        <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={logoParams.logo_show}
                onChange={(e) =>
                  updateLogoParam("logo_show", e.target.checked)
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[var(--color-border)] peer-checked:bg-[var(--color-accent)] rounded-full peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all"></div>
            </label>
            <span className="font-semibold">
              Mostra logo su copertina e quarta di copertina
            </span>
          </div>

          <p className="text-xs text-[var(--color-fg-muted)] mb-6">
            Canvas di riferimento (identico per copertina e quarta):{" "}
            <strong>
              {CANVAS_W} × {CANVAS_H} px
            </strong>{" "}
            (larghezza × altezza). Coordinate (X, Y) = angolo alto-sinistra del
            logo. Il logo viene ridimensionato con lato lungo = dimensione
            impostata, mantenendo il rapporto d&apos;aspetto originale.
          </p>

          {/* Copertina */}
          <div className="mb-8">
            <h3 className="text-base font-semibold mb-3">📕 Copertina</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <NumberField
                label="Dimensione (px lato lungo)"
                value={logoParams.cover_size_px}
                min={20}
                max={2000}
                onChange={(v) => updateLogoParam("cover_size_px", v)}
              />
              <NumberField
                label={`X (0 = sinistra, max ${CANVAS_W})`}
                value={logoParams.cover_x}
                min={-500}
                max={2000}
                onChange={(v) => updateLogoParam("cover_x", v)}
              />
              <NumberField
                label={`Y (0 = alto, max ${CANVAS_H})`}
                value={logoParams.cover_y}
                min={-500}
                max={2500}
                onChange={(v) => updateLogoParam("cover_y", v)}
              />
            </div>
          </div>

          {/* Quarta di copertina */}
          <div className="mb-6">
            <h3 className="text-base font-semibold mb-3">
              🏷 Quarta di copertina
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <NumberField
                label="Dimensione (px lato lungo)"
                value={logoParams.back_size_px}
                min={20}
                max={2000}
                onChange={(v) => updateLogoParam("back_size_px", v)}
              />
              <NumberField
                label={`X (0 = sinistra, max ${CANVAS_W})`}
                value={logoParams.back_x}
                min={-500}
                max={2000}
                onChange={(v) => updateLogoParam("back_x", v)}
              />
              <NumberField
                label={`Y (0 = alto, max ${CANVAS_H})`}
                value={logoParams.back_y}
                min={-500}
                max={2500}
                onChange={(v) => updateLogoParam("back_y", v)}
              />
            </div>
          </div>

          <button
            onClick={handleSaveLogoParams}
            disabled={savingLogo}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded disabled:opacity-50"
          >
            {savingLogo ? "Salvo..." : "💾 Salva parametri logo"}
          </button>
        </section>
      )}

      {/* Sezione Testi */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">📝 Testi default</h2>

        <div className="space-y-5">
          <div>
            <label className="block text-sm font-semibold mb-2">
              Copyright suggerito per nuovi libretti
            </label>
            <p className="text-xs text-[var(--color-fg-muted)] mb-2">
              Verrà proposto come placeholder nel campo &quot;Testo per la
              quarta di copertina&quot; quando l&apos;utente crea un libretto.
              L&apos;utente potrà sovrascriverlo.
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

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
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
        min={min}
        max={max}
        onChange={(e) => {
          const v = parseInt(e.target.value, 10);
          if (!isNaN(v)) onChange(v);
        }}
        className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm font-mono focus:outline-none focus:border-[var(--color-accent)]"
      />
    </div>
  );
}
