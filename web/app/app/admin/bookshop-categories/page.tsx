"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface Category {
  id: string;
  macro: string;
  slug: string;
  label: string;
  description: string;
  position: number;
  is_active: boolean;
}

interface MacroGroup {
  macro: string;
  label: string;
  categories: Category[];
}

interface CategoriesData {
  macros: MacroGroup[];
}

const MACRO_ORDER = ["kids", "young", "kidult"];
const MACRO_LABELS: Record<string, string> = {
  kids: "KIDS (bambini)",
  young: "YOUNG (ragazzi)",
  kidult: "KIDULT (adulti giovani)",
};

export default function AdminBookshopCategoriesPage() {
  const [data, setData] = useState<CategoriesData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  // Form state (nuova categoria)
  const [newMacro, setNewMacro] = useState("kids");
  const [newSlug, setNewSlug] = useState("");
  const [newLabel, setNewLabel] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newPosition, setNewPosition] = useState(0);

  // Edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editPosition, setEditPosition] = useState(0);
  const [editMacro, setEditMacro] = useState("kids");

  async function load() {
    try {
      setError(null);
      const d = await apiFetch<CategoriesData>(
        "/api/admin/bookshop/categories",
      );
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createCategory(e: React.FormEvent) {
    e.preventDefault();
    if (!newSlug.trim() || !newLabel.trim()) return;
    setBusy("create");
    setError(null);
    try {
      await apiFetch("/api/admin/bookshop/categories", {
        method: "POST",
        body: JSON.stringify({
          macro: newMacro,
          slug: newSlug.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-"),
          label: newLabel.trim(),
          description: newDescription.trim(),
          position: newPosition,
          is_active: true,
        }),
      });
      setNewSlug("");
      setNewLabel("");
      setNewDescription("");
      setNewPosition(0);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  function startEdit(c: Category) {
    setEditingId(c.id);
    setEditLabel(c.label);
    setEditDescription(c.description);
    setEditPosition(c.position);
    setEditMacro(c.macro);
  }

  async function saveEdit() {
    if (!editingId) return;
    setBusy(editingId);
    setError(null);
    try {
      await apiFetch(`/api/admin/bookshop/categories/${editingId}`, {
        method: "PATCH",
        body: JSON.stringify({
          macro: editMacro,
          label: editLabel,
          description: editDescription,
          position: editPosition,
        }),
      });
      setEditingId(null);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function toggleActive(c: Category) {
    setBusy(c.id);
    try {
      await apiFetch(`/api/admin/bookshop/categories/${c.id}`, {
        method: "PATCH",
        body: JSON.stringify({ is_active: !c.is_active }),
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function removeCategory(c: Category) {
    if (
      !confirm(
        `Eliminare la categoria "${c.label}"? I webtoon assegnati resteranno pubblicati ma senza categoria.`,
      )
    )
      return;
    setBusy(c.id);
    try {
      const res = await fetch(`/api/admin/bookshop/categories/${c.id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-4">
        <Link
          href="/app/admin"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
        >
          ← Pannello admin
        </Link>
      </div>

      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-1">📚 Categorie BookShop</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          Le macro categorie sono fisse (KIDS · YOUNG · KIDULT).
          Sotto ognuna puoi creare quante sotto-categorie vuoi (es. Fantasy,
          Slice of life, Sci-fi). L&apos;utente sceglierà una sotto-categoria
          quando pubblica il suo webtoon.
        </p>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {/* Form nuova categoria */}
      <form
        onSubmit={createCategory}
        className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-6 grid grid-cols-1 md:grid-cols-6 gap-3 items-end"
      >
        <div>
          <label className="block text-xs font-semibold mb-1">Macro</label>
          <select
            value={newMacro}
            onChange={(e) => setNewMacro(e.target.value)}
            className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
          >
            {MACRO_ORDER.map((m) => (
              <option key={m} value={m}>
                {MACRO_LABELS[m]}
              </option>
            ))}
          </select>
        </div>
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold mb-1">Nome</label>
          <input
            type="text"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            placeholder="Es. Fantasy magico"
            required
            className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
          />
        </div>
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold mb-1">
            Slug (URL-friendly)
          </label>
          <input
            type="text"
            value={newSlug}
            onChange={(e) => setNewSlug(e.target.value)}
            placeholder="fantasy-magico"
            required
            className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm font-mono"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold mb-1">Pos.</label>
          <input
            type="number"
            value={newPosition}
            onChange={(e) => setNewPosition(parseInt(e.target.value, 10) || 0)}
            className="w-full px-2 py-1.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
          />
        </div>
        <div className="md:col-span-6">
          <input
            type="text"
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            placeholder="Descrizione breve (facoltativa)"
            maxLength={1000}
            className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm"
          />
        </div>
        <div className="md:col-span-6 flex justify-end">
          <button
            type="submit"
            disabled={busy === "create" || !newLabel || !newSlug}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-2 rounded disabled:opacity-50"
          >
            {busy === "create" ? "Creo..." : "+ Aggiungi categoria"}
          </button>
        </div>
      </form>

      {/* Lista per macro */}
      {data === null ? (
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      ) : (
        <div className="space-y-8">
          {data.macros.map((group) => (
            <section key={group.macro}>
              <h2 className="text-lg font-semibold mb-3">
                {group.label}{" "}
                <span className="text-sm text-[var(--color-fg-muted)] font-normal">
                  ({group.categories.length})
                </span>
              </h2>
              {group.categories.length === 0 ? (
                <p className="text-sm text-[var(--color-fg-muted)] italic pl-3">
                  Nessuna categoria in questa macro.
                </p>
              ) : (
                <div className="space-y-2">
                  {group.categories.map((c) => {
                    const isEditing = editingId === c.id;
                    return (
                      <div
                        key={c.id}
                        className={`bg-[var(--color-bg-elev)] border rounded-lg p-3 ${
                          c.is_active
                            ? "border-[var(--color-border)]"
                            : "border-[var(--color-border)]/50 opacity-60"
                        }`}
                      >
                        {isEditing ? (
                          <div className="grid grid-cols-1 md:grid-cols-6 gap-2 items-end">
                            <div>
                              <label className="block text-[10px] font-semibold mb-1">
                                Macro
                              </label>
                              <select
                                value={editMacro}
                                onChange={(e) => setEditMacro(e.target.value)}
                                className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-xs"
                              >
                                {MACRO_ORDER.map((m) => (
                                  <option key={m} value={m}>
                                    {MACRO_LABELS[m]}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <div className="md:col-span-2">
                              <label className="block text-[10px] font-semibold mb-1">
                                Nome
                              </label>
                              <input
                                type="text"
                                value={editLabel}
                                onChange={(e) => setEditLabel(e.target.value)}
                                className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-xs"
                              />
                            </div>
                            <div className="md:col-span-2">
                              <label className="block text-[10px] font-semibold mb-1">
                                Descrizione
                              </label>
                              <input
                                type="text"
                                value={editDescription}
                                onChange={(e) =>
                                  setEditDescription(e.target.value)
                                }
                                className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-xs"
                              />
                            </div>
                            <div>
                              <label className="block text-[10px] font-semibold mb-1">
                                Pos.
                              </label>
                              <input
                                type="number"
                                value={editPosition}
                                onChange={(e) =>
                                  setEditPosition(
                                    parseInt(e.target.value, 10) || 0,
                                  )
                                }
                                className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-xs"
                              />
                            </div>
                            <div className="md:col-span-6 flex gap-2 justify-end">
                              <button
                                onClick={() => setEditingId(null)}
                                className="text-xs text-[var(--color-fg-muted)] px-3 py-1"
                              >
                                Annulla
                              </button>
                              <button
                                onClick={saveEdit}
                                disabled={busy === c.id}
                                className="text-xs bg-[var(--color-accent)] text-[var(--color-bg)] px-3 py-1 rounded font-semibold disabled:opacity-50"
                              >
                                💾 Salva
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between gap-3 flex-wrap">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                <span className="font-semibold text-sm">
                                  {c.label}
                                </span>
                                <span className="text-[10px] font-mono text-[var(--color-fg-muted)]">
                                  #{c.slug}
                                </span>
                                <span className="text-[10px] text-[var(--color-fg-muted)]">
                                  pos: {c.position}
                                </span>
                                {!c.is_active && (
                                  <span className="text-[10px] font-bold uppercase bg-red-900/40 text-red-300 border border-red-700/50 rounded px-1.5 py-0.5">
                                    Inattiva
                                  </span>
                                )}
                              </div>
                              {c.description && (
                                <p className="text-xs text-[var(--color-fg-muted)]">
                                  {c.description}
                                </p>
                              )}
                            </div>
                            <div className="flex gap-1 flex-wrap">
                              <button
                                onClick={() => startEdit(c)}
                                className="text-xs border border-[var(--color-border)] hover:border-[var(--color-accent)] hover:text-[var(--color-accent)] text-[var(--color-fg-muted)] px-2 py-1 rounded"
                              >
                                ✏️ Modifica
                              </button>
                              <button
                                onClick={() => toggleActive(c)}
                                disabled={busy === c.id}
                                className="text-xs border border-[var(--color-border)] hover:border-[var(--color-accent)] text-[var(--color-fg-muted)] px-2 py-1 rounded disabled:opacity-50"
                              >
                                {c.is_active ? "🚫 Disattiva" : "✅ Attiva"}
                              </button>
                              <button
                                onClick={() => removeCategory(c)}
                                disabled={busy === c.id}
                                className="text-xs text-[var(--color-fg-muted)] hover:text-red-400 px-2 py-1 disabled:opacity-50"
                              >
                                🗑
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
