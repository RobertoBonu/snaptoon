"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface MyCharacter {
  id: string;
  name: string;
  visual_description: string;
  has_reference: boolean;
  created_at: string;
}

interface MyCharactersList {
  characters: MyCharacter[];
}

type Mode = "list" | "new-text" | "new-photo";

export default function MyCharactersPage() {
  const [data, setData] = useState<MyCharactersList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("list");
  const [refreshTag, setRefreshTag] = useState<number>(Date.now());

  // Form state (used by new-text + new-photo)
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [creating, setCreating] = useState(false);

  // Editing state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  // Regen/delete busy states
  const [busy, setBusy] = useState<Set<string>>(new Set());

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<MyCharactersList>("/api/my-characters");
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  function resetForm() {
    setName("");
    setDescription("");
    setPhoto(null);
  }

  async function handleCreateFromText(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      await apiFetch("/api/my-characters", {
        method: "POST",
        body: JSON.stringify({
          name,
          visual_description: description,
        }),
      });
      resetForm();
      setMode("list");
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  async function handleCreateFromPhoto(e: React.FormEvent) {
    e.preventDefault();
    if (!photo) {
      setError("Carica una foto.");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("name", name);
      params.set("visual_description", description);
      const formData = new FormData();
      formData.append("file", photo);
      const res = await fetch(
        `/api/my-characters/from-photo?${params.toString()}`,
        { method: "POST", body: formData, credentials: "include" },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      resetForm();
      setMode("list");
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  }

  function startEdit(c: MyCharacter) {
    setEditingId(c.id);
    setEditName(c.name);
    setEditDesc(c.visual_description);
  }

  async function saveEdit(id: string) {
    try {
      await apiFetch(`/api/my-characters/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: editName,
          visual_description: editDesc,
        }),
      });
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function regenerate(id: string) {
    if (!confirm("Rigenerare la reference costa 1 credito. Procedo?")) return;
    setBusy((prev) => new Set(prev).add(id));
    setError(null);
    try {
      await apiFetch(`/api/my-characters/${id}/regenerate`, {
        method: "POST",
      });
      setRefreshTag(Date.now());
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  }

  async function remove(id: string, name: string) {
    if (!confirm(`Eliminare "${name}"? Non potrai recuperarlo.`)) return;
    try {
      const res = await fetch(`/api/my-characters/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <header className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">👤 I miei personaggi</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Archivio riusabile in qualsiasi progetto (KIDS o Pro).
          </p>
        </div>
        {mode === "list" && (
          <div className="flex gap-2">
            <button
              onClick={() => {
                resetForm();
                setMode("new-text");
              }}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded"
            >
              + Da descrizione (1 cr)
            </button>
            <button
              onClick={() => {
                resetForm();
                setMode("new-photo");
              }}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded"
            >
              + Da foto (1 cr)
            </button>
          </div>
        )}
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {/* Form: nuovo da descrizione */}
      {mode === "new-text" && (
        <form
          onSubmit={handleCreateFromText}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6 max-w-2xl"
        >
          <h2 className="font-semibold text-lg mb-4">
            ✏️ Nuovo da descrizione
          </h2>
          <p className="text-sm text-[var(--color-fg-muted)] mb-4">
            L&apos;AI genera una reference in stile portrait neutro
            (riusabile in qualsiasi progetto). Costo: 1 credito.
          </p>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Nome (es. Lollo, Nonna Rosa, Milu il gatto)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
              maxLength={255}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
            <textarea
              placeholder="Descrizione visiva dettagliata (es. bambino biondo di 6 anni, occhiali rossi, felpa a righe blu, jeans, scarpe rosse)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={4}
              minLength={5}
              maxLength={2000}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-none"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={creating || !name.trim() || description.length < 5}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50"
              >
                {creating ? "Genero..." : "✨ Crea (1 cr)"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("list");
                  resetForm();
                }}
                className="text-[var(--color-fg-muted)] px-5 py-2"
              >
                Annulla
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Form: nuovo da foto */}
      {mode === "new-photo" && (
        <form
          onSubmit={handleCreateFromPhoto}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6 max-w-2xl"
        >
          <h2 className="font-semibold text-lg mb-2">📷 Nuovo da foto</h2>
          <p className="text-sm text-[var(--color-fg-muted)] mb-4">
            Carica una foto reale del soggetto (es. tuo figlio, il gatto).
            L&apos;AI genera una reference illustrata neutra riusabile in
            qualsiasi progetto. La foto originale <strong>viene cancellata
            immediatamente dopo la generazione</strong> e non viene mai
            archiviata. Costo: 1 credito.
          </p>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Nome (es. Lollo, Nonna Rosa)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              autoFocus
              maxLength={255}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
            <textarea
              placeholder="Descrizione aggiuntiva (facoltativa: aiuta l'AI con dettagli non visibili nella foto — colore preferito, ecc.)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              maxLength={2000}
              className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded resize-none"
            />
            <div>
              <label className="block text-sm font-semibold mb-1">
                Foto del soggetto *
              </label>
              <input
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={(e) => setPhoto(e.target.files?.[0] || null)}
                required
                className="w-full text-sm"
              />
              {photo && (
                <p className="text-xs text-[var(--color-fg-muted)] mt-1">
                  Selezionato: {photo.name} (
                  {Math.round(photo.size / 1024)} KB)
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={creating || !name.trim() || !photo}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50"
              >
                {creating ? "Genero..." : "✨ Crea (1 cr)"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setMode("list");
                  resetForm();
                }}
                className="text-[var(--color-fg-muted)] px-5 py-2"
              >
                Annulla
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Lista */}
      {mode === "list" && (
        <>
          {data === null && !error ? (
            <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
          ) : data && data.characters.length === 0 ? (
            <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-12 text-center">
              <div className="text-5xl mb-4 opacity-30">👥</div>
              <p className="text-[var(--color-fg-muted)] mb-4">
                Nessun personaggio nel tuo archivio.
              </p>
              <p className="text-sm text-[var(--color-fg-muted)]">
                Creane uno per riusarlo in tutti i tuoi progetti.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data?.characters.map((c) => {
                const isBusy = busy.has(c.id);
                const isEditing = editingId === c.id;
                return (
                  <div
                    key={c.id}
                    className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden"
                  >
                    <div className="relative">
                      {c.has_reference ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={`/api/my-characters/${c.id}/image?t=${refreshTag}`}
                          alt={c.name}
                          className={`w-full aspect-square object-cover ${isBusy ? "opacity-30" : ""}`}
                        />
                      ) : (
                        <div className="w-full aspect-square flex items-center justify-center bg-[var(--color-bg)]">
                          <p className="text-xs text-[var(--color-fg-muted)]">
                            Nessuna reference
                          </p>
                        </div>
                      )}
                      {isBusy && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                          <p className="text-sm bg-[var(--color-bg)] px-3 py-1.5 rounded-full">
                            Genero...
                          </p>
                        </div>
                      )}
                    </div>
                    <div className="p-4 space-y-2">
                      {isEditing ? (
                        <>
                          <input
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm font-semibold"
                          />
                          <textarea
                            value={editDesc}
                            onChange={(e) => setEditDesc(e.target.value)}
                            rows={3}
                            className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-xs resize-none"
                          />
                          <div className="flex gap-1">
                            <button
                              onClick={() => saveEdit(c.id)}
                              className="text-xs bg-[var(--color-accent)] text-[var(--color-bg)] px-3 py-1 rounded"
                            >
                              💾 Salva
                            </button>
                            <button
                              onClick={() => setEditingId(null)}
                              className="text-xs text-[var(--color-fg-muted)] px-3 py-1"
                            >
                              Annulla
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <h3 className="font-semibold text-base">{c.name}</h3>
                          <p className="text-xs text-[var(--color-fg-muted)] line-clamp-2">
                            {c.visual_description}
                          </p>
                          <div className="flex gap-1 pt-1 flex-wrap">
                            <button
                              onClick={() => startEdit(c)}
                              className="text-xs border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-2 py-1 rounded"
                            >
                              ✏️ Modifica
                            </button>
                            <button
                              onClick={() => regenerate(c.id)}
                              disabled={isBusy}
                              className="text-xs border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-2 py-1 rounded disabled:opacity-50"
                              title="Rigenera reference (1 credito)"
                            >
                              🔄 Rigenera (1cr)
                            </button>
                            <button
                              onClick={() => remove(c.id, c.name)}
                              className="text-xs text-[var(--color-fg-muted)] hover:text-red-400 px-2 py-1"
                            >
                              🗑
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
