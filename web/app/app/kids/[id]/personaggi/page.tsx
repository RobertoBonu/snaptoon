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
  const [generating, setGenerating] = useState<string | null>(null);
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());
  // Picker "I miei personaggi": memorizza il char_id del progetto per cui
  // stiamo scegliendo. null = picker chiuso.
  const [pickerFor, setPickerFor] = useState<string | null>(null);
  const [myChars, setMyChars] = useState<
    Array<{ id: string; name: string; visual_description: string; has_reference: boolean }>
  >([]);
  const [importing, setImporting] = useState<string | null>(null);

  useEffect(() => {
    if (pickerFor === null) return;
    apiFetch<{ characters: typeof myChars }>("/api/my-characters")
      .then((d) => setMyChars(d.characters))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [pickerFor]);

  async function handleImportFromMy(myCharId: string) {
    if (!pickerFor) return;
    setImporting(myCharId);
    setError(null);
    try {
      await apiFetch(
        `/api/kids/projects/${id}/characters/${pickerFor}/import-from-my/${myCharId}`,
        { method: "POST" },
      );
      setPickerFor(null);
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setImporting(null);
    }
  }

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

  async function handleGenerateRef(charId: string) {
    setGenerating(charId);
    setError(null);
    try {
      await apiFetch<KidsCharacter>(
        `/api/kids/projects/${id}/characters/${charId}/generate-reference`,
        { method: "POST" }
      );
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(null);
    }
  }

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
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleGenerateRef(c.id)}
                    disabled={generating === c.id || uploading === c.id}
                    className="text-sm bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-medium px-4 py-1.5 rounded disabled:opacity-50"
                  >
                    {generating === c.id
                      ? "Genero..."
                      : c.has_reference
                        ? "🔄 Rigenera AI (1 cr)"
                        : "✨ Genera con AI (1 cr)"}
                  </button>
                  <label
                    className={`inline-block text-sm border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-4 py-1.5 rounded cursor-pointer transition-colors ${
                      uploading === c.id || generating === c.id ? "opacity-50" : ""
                    }`}
                  >
                    {uploading === c.id
                      ? "Carico..."
                      : c.has_reference
                        ? "📁 Sostituisci con foto"
                        : "📁 Carica foto"}
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/jpg,image/webp"
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) handleUploadRef(c.id, f);
                        e.target.value = "";
                      }}
                      disabled={uploading === c.id || generating === c.id}
                      className="hidden"
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() => setPickerFor(c.id)}
                    className="text-sm border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-4 py-1.5 rounded transition-colors"
                    title="Scegli dai personaggi salvati nel tuo archivio"
                  >
                    📚 Scegli dai miei
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Il prossimo step dipende da se la storia è già stata creata:
          - NO storia → "Genera la storia" (primario) va a /story
          - SÌ storia → "Genera le immagini" (primario) va a /generate,
                       con anche "Rivedi la storia" (secondario) verso /story */}
      {details?.has_story ? (
        <div className="flex gap-3">
          <Link
            href={`/app/kids/${id}/story`}
            className="flex-1 text-center border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 px-5 py-2.5 rounded-lg transition-colors"
          >
            📖 Rivedi la storia
          </Link>
          <Link
            href={`/app/kids/${id}/generate`}
            className="flex-1 text-center bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg transition-colors"
          >
            ✨ Genera le immagini →
          </Link>
        </div>
      ) : (
        <Link
          href={`/app/kids/${id}/story`}
          className="block w-full text-center bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg transition-colors"
        >
          📖 Genera la storia →
        </Link>
      )}

      {/* Modale picker "I miei personaggi" */}
      {pickerFor && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50"
          onClick={() => setPickerFor(null)}
        >
          <div
            className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 max-w-4xl w-full max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-lg font-semibold">
                  📚 I miei personaggi
                </h2>
                <p className="text-sm text-[var(--color-fg-muted)]">
                  Scegli un personaggio dal tuo archivio da importare in
                  questo slot. Nessun credito consumato — è una copia.
                </p>
              </div>
              <button
                onClick={() => setPickerFor(null)}
                className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] text-2xl leading-none"
              >
                ×
              </button>
            </div>

            {myChars.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-[var(--color-fg-muted)] mb-3">
                  Il tuo archivio è vuoto.
                </p>
                <Link
                  href="/app/my-characters"
                  className="text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] text-sm font-medium"
                >
                  Vai a &quot;I miei personaggi&quot; per crearne uno →
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {myChars
                  .filter((mc) => mc.has_reference)
                  .map((mc) => {
                    const isImporting = importing === mc.id;
                    return (
                      <button
                        key={mc.id}
                        onClick={() => handleImportFromMy(mc.id)}
                        disabled={isImporting}
                        className={`bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg overflow-hidden text-left hover:border-[var(--color-accent)] transition-colors disabled:opacity-50`}
                      >
                        <div className="relative">
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img
                            src={`/api/my-characters/${mc.id}/image?t=${refreshTag}`}
                            alt={mc.name}
                            className="w-full aspect-square object-cover"
                          />
                          {isImporting && (
                            <div className="absolute inset-0 flex items-center justify-center bg-black/60">
                              <p className="text-xs bg-[var(--color-bg)] px-2 py-1 rounded">
                                Importo...
                              </p>
                            </div>
                          )}
                        </div>
                        <div className="p-2">
                          <h3 className="font-semibold text-sm truncate">
                            {mc.name}
                          </h3>
                        </div>
                      </button>
                    );
                  })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
