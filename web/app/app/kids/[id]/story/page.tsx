"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { apiFetch, type KidsProjectDetails, type KidsStory } from "@/lib/api";

interface EditablePanel {
  number: number;
  description: string;
  dialogue_speaker: string;
  dialogue_text: string;
}

interface EditablePage {
  number: number;
  panels: EditablePanel[];
}

interface EditableStory {
  logline: string;
  pages: EditablePage[];
}

function toEditable(s: KidsStory): EditableStory {
  return {
    logline: s.logline,
    pages: s.pages.map((p) => ({
      number: p.number,
      panels: p.panels.map((pn) => ({
        number: pn.number,
        description: pn.description,
        dialogue_speaker: pn.dialogue_speaker ?? "",
        dialogue_text: pn.dialogue_text ?? "",
      })),
    })),
  };
}

export default function KidsStoryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [details, setDetails] = useState<KidsProjectDetails | null>(null);
  const [story, setStory] = useState<KidsStory | null>(null);
  const [edit, setEdit] = useState<EditableStory | null>(null);
  const [dirty, setDirty] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");

  async function loadDetails() {
    try {
      const d = await apiFetch<KidsProjectDetails>(
        `/api/kids/projects/${id}/details`
      );
      setDetails(d);
      if (d.has_story && d.story) {
        setStory(d.story);
        setEdit(toEditable(d.story));
        setDirty(false);
      } else {
        // Storia non ancora generata → genera al primo accesso
        await generate("");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  async function generate(fb: string) {
    setGenerating(true);
    setError(null);
    try {
      const s = await apiFetch<KidsStory>(`/api/kids/projects/${id}/story`, {
        method: "POST",
        body: JSON.stringify({ feedback: fb }),
      });
      setStory(s);
      setEdit(toEditable(s));
      setDirty(false);
      setShowFeedback(false);
      setFeedback("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  }

  async function saveEdits() {
    if (!edit) return;
    setSaving(true);
    setError(null);
    try {
      const s = await apiFetch<KidsStory>(`/api/kids/projects/${id}/story`, {
        method: "PATCH",
        body: JSON.stringify({
          logline: edit.logline,
          pages: edit.pages.map((p) => ({
            number: p.number,
            panels: p.panels.map((pn) => ({
              number: pn.number,
              description: pn.description,
              dialogue_speaker: pn.dialogue_speaker || null,
              dialogue_text: pn.dialogue_text || null,
            })),
          })),
        }),
      });
      setStory(s);
      setEdit(toEditable(s));
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    loadDetails();
  }, []);

  function updateLogline(v: string) {
    if (!edit) return;
    setEdit({ ...edit, logline: v });
    setDirty(true);
  }
  function updatePanel(
    pageIdx: number,
    panelIdx: number,
    patch: Partial<EditablePanel>
  ) {
    if (!edit) return;
    const pages = edit.pages.slice();
    const panels = pages[pageIdx].panels.slice();
    panels[panelIdx] = { ...panels[panelIdx], ...patch };
    pages[pageIdx] = { ...pages[pageIdx], panels };
    setEdit({ ...edit, pages });
    setDirty(true);
  }

  if (generating && !story) {
    return (
      <div className="p-8 max-w-3xl mx-auto">
        <div className="text-center py-20">
          <div className="text-5xl mb-4">🪄</div>
          <p className="text-lg mb-2">Claude sta scrivendo la tua storia...</p>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Possono volerci 10-20 secondi
          </p>
        </div>
      </div>
    );
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

      <h1 className="text-3xl font-bold mb-1">📖 La tua storia</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-8">
        {details?.name}
      </p>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-6">
          {error}
        </p>
      )}

      {edit && (
        <>
          {/* Logline editabile */}
          <div className="bg-gradient-to-br from-purple-950/30 to-[var(--color-bg-elev)] border-2 border-[var(--color-accent)] rounded-xl p-6 mb-6">
            <div className="text-xs text-[var(--color-accent)] uppercase tracking-widest mb-2 font-semibold">
              ✨ La tua storia
            </div>
            <textarea
              value={edit.logline}
              onChange={(e) => updateLogline(e.target.value)}
              rows={2}
              className="w-full text-xl italic font-medium leading-relaxed bg-transparent border border-transparent hover:border-[var(--color-accent)]/30 focus:border-[var(--color-accent)] focus:outline-none rounded p-2 transition-colors"
            />
          </div>

          <div className="flex items-center justify-between mb-3 gap-2">
            <h3 className="text-lg font-semibold">📚 Come si svolge</h3>
            <button
              onClick={saveEdits}
              disabled={!dirty || saving}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] text-sm font-semibold px-4 py-1.5 rounded transition-colors disabled:opacity-30"
            >
              {saving ? "Salvo..." : dirty ? "💾 Salva modifiche" : "✓ Salvato"}
            </button>
          </div>

          {/* Pagine editabili */}
          <div className="space-y-2 mb-8">
            {edit.pages.map((p, pi) => (
              <details
                key={p.number}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg overflow-hidden"
                open
              >
                <summary className="px-4 py-3 cursor-pointer hover:bg-[var(--color-border)]/30 transition-colors text-sm font-medium">
                  📖 Pagina {p.number}{" "}
                  <span className="text-[var(--color-fg-muted)] font-normal">
                    ({p.panels.length} vignette)
                  </span>
                </summary>
                <div className="px-4 pb-4 space-y-3 border-t border-[var(--color-border)] pt-3">
                  {p.panels.map((pn, pni) => (
                    <div
                      key={pn.number}
                      className="border border-[var(--color-border)] rounded p-3 space-y-2"
                    >
                      <div className="text-sm font-medium">
                        🎬 Vignetta {pn.number}
                      </div>
                      <textarea
                        value={pn.description}
                        onChange={(e) =>
                          updatePanel(pi, pni, { description: e.target.value })
                        }
                        rows={2}
                        placeholder="Descrizione scena"
                        className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded text-sm text-[var(--color-fg-muted)]"
                      />
                      <div className="flex gap-2 items-start">
                        <input
                          type="text"
                          value={pn.dialogue_speaker}
                          onChange={(e) =>
                            updatePanel(pi, pni, {
                              dialogue_speaker: e.target.value,
                            })
                          }
                          placeholder="Chi parla"
                          className="w-28 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded text-xs"
                        />
                        <input
                          type="text"
                          value={pn.dialogue_text}
                          onChange={(e) =>
                            updatePanel(pi, pni, {
                              dialogue_text: e.target.value,
                            })
                          }
                          placeholder="Battuta MAIUSCOLA breve"
                          className="flex-1 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded text-xs italic text-[var(--color-accent)]"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>

          {/* Barra salvataggio fissa quando dirty */}
          {dirty && (
            <div className="sticky bottom-4 mb-6 bg-[var(--color-accent)]/10 border border-[var(--color-accent)] rounded-lg px-4 py-2.5 flex items-center justify-between backdrop-blur">
              <span className="text-sm">Hai modifiche non salvate.</span>
              <button
                onClick={saveEdits}
                disabled={saving}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-1.5 rounded text-sm"
              >
                {saving ? "Salvo..." : "💾 Salva ora"}
              </button>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowFeedback(!showFeedback)}
              className="border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 px-5 py-2.5 rounded-lg transition-colors"
            >
              🔄 Rigenera con Claude
            </button>
            <Link
              href={`/app/kids/${id}/generate`}
              className="flex-1 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold text-center px-5 py-2.5 rounded-lg transition-colors"
            >
              ✨ Mi piace! Genera le immagini →
            </Link>
          </div>

          {showFeedback && (
            <div className="mt-6 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5">
              <h3 className="font-semibold mb-2">🔄 Rigenera con feedback</h3>
              <p className="text-sm text-[var(--color-fg-muted)] mb-3">
                Cosa vuoi cambiare? Scrivilo e Claude riscriverà tenendone conto.
                Se hai già modificato la storia manualmente, la rigenerazione
                sovrascriverà le tue modifiche.
              </p>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                rows={3}
                placeholder="Es: rendila più allegra, aggiungi un nonno, meno paurosa..."
                className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)] mb-3"
              />
              <p className="text-xs text-[var(--color-fg-muted)] mb-3">
                Costa 5 crediti.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => generate(feedback)}
                  disabled={generating}
                  className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded transition-colors disabled:opacity-50"
                >
                  {generating ? "..." : "🔄 Rigenera"}
                </button>
                <button
                  onClick={() => setShowFeedback(false)}
                  className="text-[var(--color-fg-muted)] px-5 py-2"
                >
                  Annulla
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
