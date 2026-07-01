"use client";

import { use, useEffect, useState } from "react";
import {
  apiFetch,
  type ProjectScript,
  type ScriptPage,
  type ScriptPanel,
} from "@/lib/api";

interface EditableCharacter {
  name: string;
  visual_bible: string;
  voice: string;
}

interface EditableDialogue {
  kind: string;
  speaker: string | null;
  text: string;
}

interface EditablePanel {
  number: number;
  description: string;
  dialogues: EditableDialogue[];
  shot_distance: string | null;
  shot_angle: string | null;
  mood: string | null;
}

interface EditableScript {
  logline: string;
  characters: EditableCharacter[];
  pages: { number: number; panels: EditablePanel[] }[];
}

function toEditable(s: NonNullable<ProjectScript["script"]>): EditableScript {
  return {
    logline: s.logline,
    characters: s.characters.map((c) => ({
      name: c.name,
      visual_bible: c.visual_bible || "",
      voice: c.voice || "",
    })),
    pages: s.pages.map((p) => ({
      number: p.number,
      panels: p.panels.map((pn) => ({
        number: pn.number,
        description: pn.description,
        dialogues: (pn.dialogues || []).map((d) => ({
          kind: d.kind || "FUMETTO",
          speaker: d.speaker ?? null,
          text: d.text,
        })),
        shot_distance: pn.shot_distance ?? null,
        shot_angle: pn.shot_angle ?? null,
        mood: pn.mood ?? null,
      })),
    })),
  };
}

export default function TestoPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [data, setData] = useState<ProjectScript | null>(null);
  const [sourceText, setSourceText] = useState("");
  const [edit, setEdit] = useState<EditableScript | null>(null);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [adapting, setAdapting] = useState(false);
  const [savingScript, setSavingScript] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const res = await apiFetch<ProjectScript>(
        `/api/projects/${slug}/script`
      );
      setData(res);
      setSourceText(res.source_text);
      if (res.has_script && res.script) {
        setEdit(toEditable(res.script));
        setDirty(false);
      } else {
        setEdit(null);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function saveSource() {
    setSaving(true);
    try {
      await apiFetch(`/api/projects/${slug}/source-text`, {
        method: "PATCH",
        body: JSON.stringify({ source_text: sourceText }),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  async function adapt() {
    if (!sourceText.trim()) {
      setError("Inserisci prima il testo sorgente.");
      return;
    }
    setAdapting(true);
    setError(null);
    setSyncMsg(null);
    try {
      await apiFetch(`/api/projects/${slug}/source-text`, {
        method: "PATCH",
        body: JSON.stringify({ source_text: sourceText }),
      });
      await apiFetch(`/api/projects/${slug}/adapt-script`, {
        method: "POST",
      });
      setSyncMsg(
        "Sceneggiatura generata. Personaggi importati automaticamente nel cast."
      );
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAdapting(false);
    }
  }

  async function saveScriptEdits() {
    if (!edit) return;
    setSavingScript(true);
    setError(null);
    try {
      await apiFetch(`/api/projects/${slug}/script`, {
        method: "PATCH",
        body: JSON.stringify({
          logline: edit.logline,
          characters: edit.characters,
          pages: edit.pages,
        }),
      });
      setDirty(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSavingScript(false);
    }
  }

  async function syncCharacters() {
    setSyncMsg(null);
    setError(null);
    try {
      const res = await apiFetch<{ created: string[]; already_existing: string[] }>(
        `/api/projects/${slug}/characters/sync-from-script`,
        { method: "POST" }
      );
      if (res.created.length === 0) {
        setSyncMsg(
          `Nessun nuovo personaggio da importare (${res.already_existing.length} già presenti nel cast).`
        );
      } else {
        setSyncMsg(
          `Importati nel cast: ${res.created.join(", ")}. Vai in Personaggi per completare la descrizione visiva.`
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  // Helpers per updater immutabili
  function updateLogline(v: string) {
    if (!edit) return;
    setEdit({ ...edit, logline: v });
    setDirty(true);
  }
  function updateCharacter(idx: number, patch: Partial<EditableCharacter>) {
    if (!edit) return;
    const chars = edit.characters.slice();
    chars[idx] = { ...chars[idx], ...patch };
    setEdit({ ...edit, characters: chars });
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
  function updateDialogue(
    pageIdx: number,
    panelIdx: number,
    dlgIdx: number,
    patch: Partial<EditableDialogue>
  ) {
    if (!edit) return;
    const pages = edit.pages.slice();
    const panels = pages[pageIdx].panels.slice();
    const dialogues = panels[panelIdx].dialogues.slice();
    dialogues[dlgIdx] = { ...dialogues[dlgIdx], ...patch };
    panels[panelIdx] = { ...panels[panelIdx], dialogues };
    pages[pageIdx] = { ...pages[pageIdx], panels };
    setEdit({ ...edit, pages });
    setDirty(true);
  }
  function addDialogue(pageIdx: number, panelIdx: number) {
    if (!edit) return;
    const pages = edit.pages.slice();
    const panels = pages[pageIdx].panels.slice();
    const dialogues = panels[panelIdx].dialogues.slice();
    dialogues.push({ kind: "FUMETTO", speaker: null, text: "" });
    panels[panelIdx] = { ...panels[panelIdx], dialogues };
    pages[pageIdx] = { ...pages[pageIdx], panels };
    setEdit({ ...edit, pages });
    setDirty(true);
  }
  function removeDialogue(pageIdx: number, panelIdx: number, dlgIdx: number) {
    if (!edit) return;
    const pages = edit.pages.slice();
    const panels = pages[pageIdx].panels.slice();
    const dialogues = panels[panelIdx].dialogues.slice();
    dialogues.splice(dlgIdx, 1);
    panels[panelIdx] = { ...panels[panelIdx], dialogues };
    pages[pageIdx] = { ...pages[pageIdx], panels };
    setEdit({ ...edit, pages });
    setDirty(true);
  }

  if (data === null && !error) {
    return <p className="text-[var(--color-fg-muted)]">Caricamento...</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">📝 Sceneggiatura</h1>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}
      {syncMsg && (
        <p className="text-green-400 text-sm bg-green-950/30 border border-green-900/50 rounded px-3 py-2 mb-4">
          {syncMsg}
        </p>
      )}

      {/* Source text editor */}
      <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
        <h2 className="font-semibold mb-2">Testo sorgente</h2>
        <p className="text-sm text-[var(--color-fg-muted)] mb-3">
          Incolla il tuo soggetto, racconto o canovaccio. Claude lo trasformerà
          in sceneggiatura strutturata (logline, personaggi, pagine, vignette,
          dialoghi).
        </p>
        <textarea
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
          rows={10}
          placeholder="Inizio del racconto qui..."
          className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)] font-mono text-sm"
        />
        <div className="flex gap-2 mt-3">
          <button
            onClick={saveSource}
            disabled={saving}
            className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] border border-[var(--color-border)] hover:border-[var(--color-fg-muted)] px-4 py-2 rounded transition-colors disabled:opacity-50"
          >
            {saving ? "..." : "💾 Salva testo"}
          </button>
          <button
            onClick={adapt}
            disabled={adapting || !sourceText.trim()}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded transition-colors disabled:opacity-50"
          >
            {adapting ? "Claude sta scrivendo..." : "✨ Adatta in sceneggiatura (5 cr)"}
          </button>
        </div>
      </section>

      {/* Script result — EDITABLE */}
      {data?.has_script && edit && (
        <section>
          <header className="flex items-center justify-between mb-3 gap-2 flex-wrap">
            <h2 className="text-lg font-semibold">Sceneggiatura</h2>
            <div className="flex gap-2">
              <button
                onClick={syncCharacters}
                className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] border border-[var(--color-border)] hover:border-[var(--color-fg-muted)] px-4 py-2 rounded transition-colors"
                title="Crea nel cast i personaggi presenti nello script ma mancanti"
              >
                🔄 Sincronizza personaggi
              </button>
              <button
                onClick={saveScriptEdits}
                disabled={!dirty || savingScript}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded transition-colors disabled:opacity-30"
              >
                {savingScript
                  ? "Salvo..."
                  : dirty
                  ? "💾 Salva modifiche"
                  : "✓ Salvato"}
              </button>
            </div>
          </header>

          {/* Logline editabile */}
          <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-4">
            <div className="text-xs text-[var(--color-accent)] uppercase tracking-widest mb-2">
              Logline
            </div>
            <textarea
              value={edit.logline}
              onChange={(e) => updateLogline(e.target.value)}
              rows={2}
              className="w-full px-2 py-1 bg-transparent border border-transparent hover:border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded italic transition-colors"
            />
          </div>

          {/* Personaggi editabili */}
          <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-4">
            <h3 className="font-semibold mb-3">Personaggi</h3>
            <div className="space-y-3">
              {edit.characters.map((c, i) => (
                <div
                  key={i}
                  className="border border-[var(--color-border)] rounded p-3 space-y-2"
                >
                  <input
                    type="text"
                    value={c.name}
                    onChange={(e) =>
                      updateCharacter(i, { name: e.target.value })
                    }
                    placeholder="Nome"
                    className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded text-sm font-medium"
                  />
                  <textarea
                    value={c.visual_bible}
                    onChange={(e) =>
                      updateCharacter(i, { visual_bible: e.target.value })
                    }
                    placeholder="Descrizione visiva (aspetto, colori, dettagli)"
                    rows={2}
                    className="w-full px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded text-sm"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Pagine + vignette + dialoghi editabili */}
          <div className="space-y-3">
            {edit.pages.map((p, pi) => (
              <details
                key={p.number}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden"
                open
              >
                <summary className="px-4 py-3 cursor-pointer hover:bg-[var(--color-border)]/30 font-medium text-sm">
                  Pagina {p.number}{" "}
                  <span className="text-[var(--color-fg-muted)] font-normal">
                    ({p.panels.length} vignette)
                  </span>
                </summary>
                <div className="px-4 pb-4 space-y-4 border-t border-[var(--color-border)] pt-3">
                  {p.panels.map((pn, pni) => (
                    <div
                      key={pn.number}
                      className="border border-[var(--color-border)] rounded p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          🎬 Vignetta {pn.number}
                        </span>
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

                      {/* Dialoghi */}
                      <div className="space-y-1.5">
                        {pn.dialogues.map((d, di) => (
                          <div key={di} className="flex gap-2 items-start">
                            <input
                              type="text"
                              value={d.speaker || ""}
                              onChange={(e) =>
                                updateDialogue(pi, pni, di, {
                                  speaker: e.target.value || null,
                                })
                              }
                              placeholder="Personaggio"
                              className="w-32 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded text-xs"
                            />
                            <input
                              type="text"
                              value={d.text}
                              onChange={(e) =>
                                updateDialogue(pi, pni, di, {
                                  text: e.target.value,
                                })
                              }
                              placeholder="Battuta"
                              className="flex-1 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] focus:border-[var(--color-accent)] focus:outline-none rounded text-xs italic text-[var(--color-accent)]"
                            />
                            <button
                              onClick={() => removeDialogue(pi, pni, di)}
                              title="Elimina dialogo"
                              className="text-[var(--color-fg-muted)] hover:text-red-400 px-2 text-xs"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                        <button
                          onClick={() => addDialogue(pi, pni)}
                          className="text-xs text-[var(--color-fg-muted)] hover:text-[var(--color-accent)]"
                        >
                          + Aggiungi dialogo
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>

          {/* Barra salvataggio fissa in basso quando dirty */}
          {dirty && (
            <div className="sticky bottom-4 mt-4 bg-[var(--color-accent)]/10 border border-[var(--color-accent)] rounded-lg px-4 py-2.5 flex items-center justify-between backdrop-blur">
              <span className="text-sm">
                Hai modifiche non salvate.
              </span>
              <button
                onClick={saveScriptEdits}
                disabled={savingScript}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-4 py-1.5 rounded text-sm"
              >
                {savingScript ? "Salvo..." : "💾 Salva ora"}
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
