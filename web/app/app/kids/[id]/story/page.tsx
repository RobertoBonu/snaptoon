"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { apiFetch, type KidsProjectDetails, type KidsStory } from "@/lib/api";

export default function KidsStoryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [details, setDetails] = useState<KidsProjectDetails | null>(null);
  const [story, setStory] = useState<KidsStory | null>(null);
  const [generating, setGenerating] = useState(false);
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
      setShowFeedback(false);
      setFeedback("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  }

  useEffect(() => {
    loadDetails();
  }, []);

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

      {story && (
        <>
          {/* Logline card */}
          <div className="bg-gradient-to-br from-purple-950/30 to-[var(--color-bg-elev)] border-2 border-[var(--color-accent)] rounded-xl p-6 mb-6">
            <div className="text-xs text-[var(--color-accent)] uppercase tracking-widest mb-2 font-semibold">
              ✨ La tua storia
            </div>
            <p className="text-xl italic font-medium leading-relaxed">
              "{story.logline}"
            </p>
          </div>

          {/* Pagine */}
          <h3 className="text-lg font-semibold mb-3">📚 Come si svolge</h3>
          <div className="space-y-2 mb-8">
            {story.pages.map((p) => (
              <details
                key={p.number}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg overflow-hidden"
              >
                <summary className="px-4 py-3 cursor-pointer hover:bg-[var(--color-border)]/30 transition-colors text-sm font-medium">
                  📖 Pagina {p.number}{" "}
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
                      <div className="text-[var(--color-fg-muted)] mb-1 pl-4">
                        {pn.description}
                      </div>
                      {pn.dialogue_text && (
                        <div className="pl-4 text-[var(--color-accent)] italic">
                          💬{" "}
                          {pn.dialogue_speaker && (
                            <strong>{pn.dialogue_speaker}: </strong>
                          )}
                          "{pn.dialogue_text}"
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowFeedback(!showFeedback)}
              className="border border-[var(--color-border)] hover:border-[var(--color-accent)]/50 px-5 py-2.5 rounded-lg transition-colors"
            >
              🔄 Rigenera storia
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
