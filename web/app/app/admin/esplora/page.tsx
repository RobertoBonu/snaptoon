"use client";

import { useEffect, useRef, useState } from "react";
import {
  apiFetch,
  uploadEsploraImage,
  type EsploraAsset,
  type EsploraSection,
  type EsploraSectionsOut,
} from "@/lib/api";

interface AssetMeta {
  asset_type: string;
  title: string;
  caption: string;
  author_name: string;
  author_role: string;
}

export default function AdminEsploraPage() {
  const [sections, setSections] = useState<EsploraSection[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<EsploraSectionsOut>("/api/admin/esplora/assets");
      setSections(d.sections);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function addAsset(sectionKey: string) {
    setWorking(`add-${sectionKey}`);
    try {
      await apiFetch("/api/admin/esplora/assets", {
        method: "POST",
        body: JSON.stringify({ section: sectionKey }),
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function saveMeta(a: EsploraAsset, fields: AssetMeta): Promise<boolean> {
    setWorking(a.id);
    try {
      await apiFetch(`/api/admin/esplora/assets/${a.id}`, {
        method: "PATCH",
        body: JSON.stringify(fields),
      });
      await load();
      return true;
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
      return false;
    } finally {
      setWorking(null);
    }
  }

  async function toggleActive(a: EsploraAsset) {
    setWorking(a.id);
    try {
      await apiFetch(`/api/admin/esplora/assets/${a.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !a.is_active }),
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function move(a: EsploraAsset, delta: number) {
    setWorking(a.id);
    try {
      await apiFetch(`/api/admin/esplora/assets/${a.id}`, {
        method: "PATCH",
        body: JSON.stringify({ position: a.position + delta }),
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function remove(a: EsploraAsset) {
    if (!confirm(`Eliminare "${a.title}"? L'immagine verrà rimossa.`)) return;
    setWorking(a.id);
    try {
      await apiFetch(`/api/admin/esplora/assets/${a.id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function upload(a: EsploraAsset, file: File) {
    setWorking(a.id);
    try {
      await uploadEsploraImage(a.id, file);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function generate(a: EsploraAsset) {
    const promptText = prompt(
      a.prompt
        ? "Modifica il prompt e rigenera:"
        : "Descrivi l'immagine da generare (prompt):",
      a.prompt || ""
    );
    if (!promptText || promptText.trim().length < 3) return;
    setWorking(a.id);
    try {
      await apiFetch(`/api/admin/esplora/assets/${a.id}/generate`, {
        method: "POST",
        body: JSON.stringify({ prompt: promptText, quality: "medium" }),
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  if (sections === null && !error) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">🖼 Asset Esplora</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Gestisci le immagini della pagina pubblica /esplora: carica, genera con
            l&apos;AI, rigenera o elimina.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <a
            href="/app/admin/esplora/personaggi-utenti"
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2.5 rounded-lg text-sm"
          >
            👥 Personaggi utenti
          </a>
          <a
            href="/app/admin/esplora/community-shares"
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2.5 rounded-lg text-sm"
          >
            🎨 Cover + tavole utenti
          </a>
          <a
            href="/app/admin"
            className="border border-[var(--color-border)] hover:bg-[var(--color-bg-elev)] text-[var(--color-fg)] font-semibold px-5 py-2.5 rounded-lg"
          >
            ← Pannello admin
          </a>
        </div>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {sections?.map((sec) => (
        <section key={sec.key} className="mb-10">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">
              {sec.label}{" "}
              <span className="text-sm text-[var(--color-fg-muted)] font-normal">
                ({sec.items.length})
              </span>
            </h2>
            <button
              onClick={() => addAsset(sec.key)}
              disabled={working === `add-${sec.key}`}
              className="text-sm border border-[var(--color-border)] hover:bg-[var(--color-bg-elev)] px-3 py-1.5 rounded disabled:opacity-50"
            >
              + Aggiungi
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {sec.items.map((a) => (
              <AssetCard
                key={a.id}
                asset={a}
                aspect={sec.aspect}
                busy={working === a.id}
                onUpload={(file) => upload(a, file)}
                onGenerate={() => generate(a)}
                onSave={(fields) => saveMeta(a, fields)}
                onToggle={() => toggleActive(a)}
                onMove={(d) => move(a, d)}
                onRemove={() => remove(a)}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function AssetCard({
  asset,
  aspect,
  busy,
  onUpload,
  onGenerate,
  onSave,
  onToggle,
  onMove,
  onRemove,
}: {
  asset: EsploraAsset;
  aspect: string;
  busy: boolean;
  onUpload: (file: File) => void;
  onGenerate: () => void;
  onSave: (fields: AssetMeta) => Promise<boolean>;
  onToggle: () => void;
  onMove: (delta: number) => void;
  onRemove: () => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<AssetMeta>({
    asset_type: asset.asset_type,
    title: asset.title,
    caption: asset.caption,
    author_name: asset.author_name,
    author_role: asset.author_role,
  });

  function startEdit() {
    setForm({
      asset_type: asset.asset_type,
      title: asset.title,
      caption: asset.caption,
      author_name: asset.author_name,
      author_role: asset.author_role,
    });
    setEditing(true);
  }

  const field = (
    label: string,
    key: keyof AssetMeta,
    placeholder = ""
  ) => (
    <label className="flex flex-col gap-1">
      <span className="text-[11px] uppercase tracking-wide text-[var(--color-fg-muted)]">{label}</span>
      <input
        value={form[key]}
        placeholder={placeholder}
        onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
        className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded px-2 py-1.5 text-xs text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent,#F59E0B)]"
      />
    </label>
  );

  return (
    <div
      className={`bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden flex flex-col ${
        asset.is_active ? "" : "opacity-50"
      }`}
    >
      <div style={{ aspectRatio: aspect, position: "relative", background: "#0A0E17" }}>
        {asset.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={asset.image_url}
            alt={asset.title}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#475569",
              fontSize: "13px",
            }}
          >
            Nessuna immagine
          </div>
        )}
        {busy && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(0,0,0,0.6)",
              color: "#F1F5F9",
              fontSize: "13px",
            }}
          >
            Lavorazione...
          </div>
        )}
      </div>

      <div className="p-3 flex flex-col gap-2 flex-1">
        {editing ? (
          <div className="flex flex-col gap-2">
            {field("Tipo", "asset_type", "es. KIDSTOONS")}
            {field("Titolo", "title")}
            {field("Didascalia", "caption")}
            {field("Nome autore", "author_name", "es. Studio Lumino")}
            {field("Ruolo", "author_role", "es. Editore")}
            <div className="grid grid-cols-2 gap-1.5 text-xs mt-1">
              <button
                onClick={async () => {
                  if (await onSave(form)) setEditing(false);
                }}
                disabled={busy}
                className="bg-[var(--color-accent,#F59E0B)] text-black font-semibold px-2 py-1.5 rounded disabled:opacity-50"
              >
                💾 Salva
              </button>
              <button
                onClick={() => setEditing(false)}
                disabled={busy}
                className="border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-2 py-1.5 rounded disabled:opacity-50"
              >
                Annulla
              </button>
            </div>
          </div>
        ) : (
          <>
            <div>
              {asset.asset_type && (
                <div className="text-[10px] uppercase tracking-wide text-[var(--color-fg-muted)] mb-0.5">
                  {asset.asset_type}
                </div>
              )}
              <div className="text-sm font-semibold truncate" title={asset.title}>
                {asset.title || "(senza titolo)"}
              </div>
              <div className="text-xs text-[var(--color-fg-muted)] truncate" title={asset.caption}>
                {asset.caption || "—"}
              </div>
              {(asset.author_name || asset.author_role) && (
                <div className="text-xs text-[var(--color-fg-muted)] truncate mt-0.5">
                  {asset.author_name}
                  {asset.author_role ? ` · ${asset.author_role}` : ""}
                </div>
              )}
            </div>

            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onUpload(f);
                e.target.value = "";
              }}
            />

            <div className="grid grid-cols-2 gap-1.5 mt-auto text-xs">
              <button
                onClick={() => fileRef.current?.click()}
                disabled={busy}
                className="border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-2 py-1.5 rounded disabled:opacity-50"
              >
                ⬆ Carica
              </button>
              <button
                onClick={onGenerate}
                disabled={busy}
                className="border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-2 py-1.5 rounded disabled:opacity-50"
              >
                {asset.has_image ? "↻ Rigenera" : "✨ Genera"}
              </button>
              <button
                onClick={startEdit}
                disabled={busy}
                className="border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-2 py-1.5 rounded disabled:opacity-50"
              >
                ✎ Modifica
              </button>
              <button
                onClick={onToggle}
                disabled={busy}
                className="border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-2 py-1.5 rounded disabled:opacity-50"
              >
                {asset.is_active ? "👁 Nascondi" : "👁 Mostra"}
              </button>
              <div className="flex gap-1.5">
                <button
                  onClick={() => onMove(-1)}
                  disabled={busy}
                  className="flex-1 border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-2 py-1.5 rounded disabled:opacity-50"
                  title="Sposta su"
                >
                  ↑
                </button>
                <button
                  onClick={() => onMove(1)}
                  disabled={busy}
                  className="flex-1 border border-[var(--color-border)] hover:bg-[var(--color-bg)] px-2 py-1.5 rounded disabled:opacity-50"
                  title="Sposta giù"
                >
                  ↓
                </button>
              </div>
              <button
                onClick={onRemove}
                disabled={busy}
                className="border border-red-900/50 text-red-400 hover:bg-red-950/30 px-2 py-1.5 rounded disabled:opacity-50"
              >
                🗑 Elimina
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
