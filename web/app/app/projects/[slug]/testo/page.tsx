"use client";

import { use, useEffect, useState } from "react";
import { apiFetch, type ProjectScript } from "@/lib/api";

export default function TestoPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const [data, setData] = useState<ProjectScript | null>(null);
  const [sourceText, setSourceText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [adapting, setAdapting] = useState(false);

  async function load() {
    try {
      setError(null);
      const res = await apiFetch<ProjectScript>(
        `/api/projects/${slug}/script`
      );
      setData(res);
      setSourceText(res.source_text);
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
    try {
      // Salva sempre la source text prima di adattare
      await apiFetch(`/api/projects/${slug}/source-text`, {
        method: "PATCH",
        body: JSON.stringify({ source_text: sourceText }),
      });
      await apiFetch(`/api/projects/${slug}/adapt-script`, {
        method: "POST",
      });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAdapting(false);
    }
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

      {/* Script result */}
      {data?.has_script && data.script && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Sceneggiatura generata</h2>

          <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-4">
            <div className="text-xs text-[var(--color-accent)] uppercase tracking-widest mb-1">
              Logline
            </div>
            <p className="italic">"{data.script.logline}"</p>
          </div>

          <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-4">
            <h3 className="font-semibold mb-2">Personaggi</h3>
            <ul className="space-y-2">
              {data.script.characters.map((c, i) => (
                <li key={i} className="text-sm">
                  <span className="font-medium">{c.name}</span>
                  {c.visual_bible && (
                    <span className="text-[var(--color-fg-muted)] ml-2">
                      — {c.visual_bible}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            {data.script.pages.map((p) => (
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
                <div className="px-4 pb-4 space-y-3 border-t border-[var(--color-border)] pt-3">
                  {p.panels.map((pn) => (
                    <div key={pn.number} className="text-sm">
                      <div className="font-medium mb-1">
                        🎬 Vignetta {pn.number}
                      </div>
                      <div className="text-[var(--color-fg-muted)] pl-4 mb-1">
                        {pn.description}
                      </div>
                      {pn.dialogues.map((d, di) => (
                        <div
                          key={di}
                          className="pl-4 text-[var(--color-accent)] italic"
                        >
                          💬 <strong>{d.speaker || "—"}: </strong>"{d.text}"
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
