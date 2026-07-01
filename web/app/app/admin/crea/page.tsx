"use client";

import { useEffect, useRef, useState } from "react";
import {
  apiFetch,
  uploadCreaImage,
  type CreaImage,
  type CreaImagesOut,
} from "@/lib/api";

export default function AdminCreaPage() {
  const [images, setImages] = useState<CreaImage[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<CreaImagesOut>("/api/admin/crea/images");
      setImages(d.images);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function upload(img: CreaImage, file: File) {
    setWorking(img.slot);
    try {
      await uploadCreaImage(img.slot, file);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function reset(img: CreaImage) {
    if (
      !confirm(
        "Rimuovere l'immagine caricata e tornare al default? L'immagine originale del sito verrà ripristinata."
      )
    )
      return;
    setWorking(img.slot);
    try {
      await apiFetch(`/api/admin/crea/images/${img.slot}`, { method: "DELETE" });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  if (images === null && !error) {
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
          <h1 className="text-3xl font-bold mb-1">🎨 Immagini CREA</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Gestisci le 6 immagini della pagina pubblica /crea: carica una tua
            immagine o ripristina quella di default.
          </p>
        </div>
        <a
          href="/app/admin"
          className="border border-[var(--color-border)] hover:bg-[var(--color-bg-elev)] text-[var(--color-fg)] font-semibold px-5 py-2.5 rounded-lg"
        >
          ← Pannello admin
        </a>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {images?.map((img) => (
          <CreaCard
            key={img.slot}
            img={img}
            busy={working === img.slot}
            onUpload={(file) => upload(img, file)}
            onReset={() => reset(img)}
          />
        ))}
      </div>
    </div>
  );
}

function CreaCard({
  img,
  busy,
  onUpload,
  onReset,
}: {
  img: CreaImage;
  busy: boolean;
  onUpload: (file: File) => void;
  onReset: () => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  // Sorgente mostrata: immagine caricata se presente, altrimenti il default statico.
  const src = img.image_url || img.default_src;

  return (
    <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden flex flex-col">
      <div style={{ aspectRatio: img.aspect, position: "relative", background: "#0A0E17" }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={src}
          alt={img.label}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
        <span
          className="absolute top-2 left-2 text-[10px] font-semibold px-2 py-0.5 rounded"
          style={{
            background: img.has_image ? "rgba(16,185,129,0.85)" : "rgba(71,85,105,0.85)",
            color: "#fff",
          }}
        >
          {img.has_image ? "Personalizzata" : "Default"}
        </span>
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
        <div>
          <div className="text-sm font-semibold truncate" title={img.label}>
            {img.label}
          </div>
          <div className="text-[11px] text-[var(--color-fg-muted)] font-mono truncate">
            {img.slot}
          </div>
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
            onClick={onReset}
            disabled={busy || !img.has_image}
            className="border border-red-900/50 text-red-400 hover:bg-red-950/30 px-2 py-1.5 rounded disabled:opacity-40"
          >
            ↺ Default
          </button>
        </div>
      </div>
    </div>
  );
}
