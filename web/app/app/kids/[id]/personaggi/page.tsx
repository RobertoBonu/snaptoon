"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { apiFetch, type KidsProjectDetails } from "@/lib/api";

interface KidsCharacter {
  id: string;
  name: string;
  visual_description: string;
  has_reference: boolean;
}

/**
 * Pagina Personaggi KIDS: carica una foto o genera l'AI reference.
 *
 * L'utente arriva qui dopo aver creato il progetto (dal wizard /new).
 * Prima di andare al /generate SSE, può:
 *  - Caricare una foto reale del personaggio (es. foto della figlia)
 *    → l'AI userà quella come base per le vignette
 *  - Oppure lasciare che la pipeline SSE generi automaticamente
 *    la reference dalla descrizione testuale
 */
export default function KidsPersonaggiPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [details, setDetails] = useState<KidsProjectDetails | null>(null);
  const [chars, setChars] = useState<KidsCharacter[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState<string | null>(null);
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  async function load() {
    try {
      setError(null);
      const [d, ch] = await Promise.all([
        apiFetch<KidsProjectDetails>(`/api/kids/projects/${id}/details`),
        apiFetch<{ characters: KidsCharacter[] }>(
          `/api/kids/projects/${id}/characters`
        ),
      ]);
      setDetails(d);
      setChars(ch.characters);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleUploadRef(charId: string, file: File) {
    const okTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!okTypes.includes(file.type)) {
      setError("Formato non supportato. Usa PNG, JPEG o WEBP.");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError("Immagine troppo grande (max 8 MB).");
      return;
    }
    setUploading(charId);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(
        `/api/kids/projects/${id}/characters/${charId}/upload-reference`,
        {
          method: "POST",
          body: formData,
          credentials: "include",
        }
      );
      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const data = await res.json();
          if (data?.detail) detail = data.detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setUploading(null);
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-4">
        <Link
          href="/app/kids"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Tutti i libretti
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-1">👥 Personaggi</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-8">
        {details?.name} — carica una foto per ogni personaggio (opzionale)
      </p>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      <div className="bg-[var(--color-accent)]/5 border border-[var(--color-accent)]/30 rounded-xl p-4 mb-6 text-sm">
        💡 <strong>Suggerimento</strong>: se carichi una foto reale (es. foto
        di tuo figlio, del suo pupazzo preferito, di un tuo disegno) l'AI la
        userà come base per generare le vignette. Il volto sarà molto più
        riconoscibile. Se salti questo passaggio, l'AI genera la reference
        automaticamente dalla descrizione testuale.
      </div>

      <div className="space-y-4 mb-8">
        {chars.map((c) => (
          <div
            key={c.id}
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden"
          >
            <div className="flex gap-4 p-4">
              <div className="w-32 h-32 flex-shrink-0 bg-[var(--color-bg)] border border-[var(--color-border)] rounded overflow-hidden">
                {c.has_reference ? (
                  <img
                    src={`/api/kids/projects/${id}/characters/${c.id}/reference?t=${refreshTag}`}
                    alt={c.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-center p-2">
                    <div className="text-3xl opacity-30 mb-1">👤</div>
                    <p className="text-[10px] text-[var(--color-fg-muted)]">
                      Nessuna foto
                    </p>
                  </div>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <h3 className="font-semibold mb-1">{c.name}</h3>
                <p className="text-xs text-[var(--color-fg-muted)] mb-3 line-clamp-3">
                  {c.visual_description}
                </p>
                <label
                  className={`inline-block text-sm border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-4 py-1.5 rounded cursor-pointer transition-colors ${
                    uploading === c.id ? "opacity-50" : ""
                  }`}
                >
                  {uploading === c.id
                    ? "Carico..."
                    : c.has_reference
                      ? "📁 Sostituisci foto"
                      : "📁 Carica foto"}
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/jpg,image/webp"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleUploadRef(c.id, f);
                      e.target.value = "";
                    }}
                    disabled={uploading === c.id}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <Link
          href={`/app/kids/${id}/story`}
          className="flex-1 text-center border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 px-5 py-2.5 rounded-lg transition-colors"
        >
          📖 Vai alla storia
        </Link>
        <Link
          href={`/app/kids/${id}/generate`}
          className="flex-1 text-center bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg transition-colors"
        >
          ✨ Genera le immagini →
        </Link>
      </div>
    </div>
  );
}
