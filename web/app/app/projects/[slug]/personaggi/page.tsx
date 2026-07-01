"use client";

import PageLoader from "@/components/PageLoader";

import { use, useEffect, useState } from "react";
import { apiFetch, type Character, type CharacterList } from "@/lib/api";

export default function PersonaggiPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [characters, setCharacters] = useState<Character[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);
  const [generatingRef, setGeneratingRef] = useState<string | null>(null);
  const [uploadingRef, setUploadingRef] = useState<string | null>(null);
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  async function load() {
    try {
      setError(null);
      const data = await apiFetch<CharacterList>(
        `/api/projects/${slug}/characters`
      );
      setCharacters(data.characters);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      await apiFetch<Character>(`/api/projects/${slug}/characters`, {
        method: "POST",
        body: JSON.stringify({ name: newName, visual_description: newDesc }),
      });
      setNewName("");
      setNewDesc("");
      setShowCreate(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(charId: string, name: string) {
    if (!confirm(`Eliminare "${name}"?`)) return;
    try {
      await apiFetch(`/api/projects/${slug}/characters/${charId}`, {
        method: "DELETE",
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  }

  async function handleGenerateRef(charId: string) {
    setGeneratingRef(charId);
    setError(null);
    try {
      await apiFetch<Character>(
        `/api/projects/${slug}/characters/${charId}/reference`,
        { method: "POST" }
      );
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGeneratingRef(null);
    }
  }

  async function handleUploadRef(charId: string, file: File) {
    // Validazione lato client (rapida)
    const okTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    if (!okTypes.includes(file.type)) {
      setError("Formato non supportato. Usa PNG, JPEG o WEBP.");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError("Immagine troppo grande (max 8 MB).");
      return;
    }
    setUploadingRef(charId);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(
        `/api/projects/${slug}/characters/${charId}/upload-reference`,
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
      setUploadingRef(null);
    }
  }

  if (characters === null && !error) {
    return <PageLoader message="Carico i personaggi..." />;
  }

  return (
    <div>
      <header className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1">👥 Personaggi</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Cast del fumetto. Genera reference image AI per ogni personaggio
            (1 cr).
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded-lg whitespace-nowrap"
        >
          + Aggiungi
        </button>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-6 space-y-3"
        >
          <h3 className="font-semibold">Nuovo personaggio</h3>
          <input
            type="text"
            placeholder="Nome"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            required
            className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
          />
          <textarea
            placeholder="Descrizione visiva (aspetto, colori, vestiti, dettagli)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            rows={3}
            required
            className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={creating || !newName.trim() || !newDesc.trim()}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50"
            >
              {creating ? "..." : "Crea"}
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="text-[var(--color-fg-muted)] px-5 py-2"
            >
              Annulla
            </button>
          </div>
        </form>
      )}

      {characters && characters.length === 0 ? (
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
          <div className="text-5xl mb-4 opacity-30">👥</div>
          <p className="text-[var(--color-fg-muted)]">Nessun personaggio.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {characters?.map((c) => (
            <div
              key={c.id}
              className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden"
            >
              <div className="flex">
                <div className="w-40 flex-shrink-0 bg-[var(--color-bg)] border-r border-[var(--color-border)]">
                  {c.has_reference ? (
                    <img
                      src={`/api/projects/${slug}/characters/${c.id}/reference?t=${refreshTag}`}
                      alt={c.name}
                      className="w-full h-full object-cover aspect-square"
                    />
                  ) : (
                    <div className="w-full h-full aspect-square flex items-center justify-center text-[var(--color-fg-muted)] text-xs px-2 text-center">
                      Nessuna reference
                    </div>
                  )}
                </div>
                <div className="flex-1 p-4 min-w-0">
                  <h3 className="font-semibold mb-1">{c.name}</h3>
                  <p className="text-xs text-[var(--color-fg-muted)] mb-3 line-clamp-3">
                    {c.visual_description}
                  </p>
                  <div className="flex flex-wrap gap-2 items-center">
                    <button
                      onClick={() => handleGenerateRef(c.id)}
                      disabled={
                        generatingRef === c.id || uploadingRef === c.id
                      }
                      className="text-xs bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-medium px-3 py-1.5 rounded disabled:opacity-50"
                    >
                      {generatingRef === c.id
                        ? "..."
                        : c.has_reference
                          ? "🔄 Rigenera ref (1 cr)"
                          : "✨ Genera ref (1 cr)"}
                    </button>

                    {/* Upload foto reference */}
                    <label
                      className={`text-xs border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-3 py-1.5 rounded cursor-pointer transition-colors ${
                        uploadingRef === c.id ? "opacity-50" : ""
                      }`}
                      title="Carica una foto o un disegno del personaggio"
                    >
                      {uploadingRef === c.id ? "..." : "📁 Carica foto"}
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/jpg,image/webp"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) handleUploadRef(c.id, f);
                          // Reset input value così l'utente può ricaricare
                          // lo stesso file dopo un errore
                          e.target.value = "";
                        }}
                        disabled={
                          generatingRef === c.id || uploadingRef === c.id
                        }
                        className="hidden"
                      />
                    </label>

                    <button
                      onClick={() => handleDelete(c.id, c.name)}
                      className="text-xs text-[var(--color-fg-muted)] hover:text-red-400 px-2 py-1.5"
                    >
                      Elimina
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
