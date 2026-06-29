"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  apiFetch,
  type KidsCharacterIn,
  type KidsProject,
  type KidsStyle,
  type KidsTemplate,
} from "@/lib/api";

type Step = 1 | 2 | 3;

const STEP_LABELS: Record<Step, string> = {
  1: "Template & Stile",
  2: "Scintilla & nomi",
  3: "Personaggi",
};

export default function NewKidsPage() {
  // Wizard state
  const [step, setStep] = useState<Step>(1);
  const [error, setError] = useState<string | null>(null);

  // Data caricati dall'API
  const [templates, setTemplates] = useState<KidsTemplate[]>([]);
  const [styles, setStyles] = useState<KidsStyle[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Scelte utente
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [selectedStyleSlug, setSelectedStyleSlug] = useState<string | null>(null);
  const [scintilla, setScintilla] = useState("");
  const [characters, setCharacters] = useState<KidsCharacterIn[]>([]);
  const [creating, setCreating] = useState(false);

  // Init: load templates + styles
  useEffect(() => {
    (async () => {
      try {
        const [tpls, sts] = await Promise.all([
          apiFetch<{ templates: KidsTemplate[] }>("/api/kids/templates"),
          apiFetch<KidsStyle[]>("/api/kids/styles"),
        ]);
        setTemplates(tpls.templates);
        setStyles(sts);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoadingData(false);
      }
    })();
  }, []);

  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId);
  const requiredChars = selectedTemplate?.n_characters ?? 1;

  // Sync characters array dimensioni quando si cambia template
  useEffect(() => {
    if (!selectedTemplate) return;
    setCharacters((prev) => {
      const next = [...prev];
      while (next.length < requiredChars) next.push({ name: "", description: "" });
      while (next.length > requiredChars) next.pop();
      return next;
    });
  }, [requiredChars, selectedTemplate]);

  function updateCharacter(idx: number, field: keyof KidsCharacterIn, value: string) {
    setCharacters((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], [field]: value };
      return next;
    });
  }

  function canGoToStep2(): boolean {
    return selectedTemplateId !== null && selectedStyleSlug !== null;
  }

  function canGoToStep3(): boolean {
    return canGoToStep2() && scintilla.trim().length > 10 && characters.every((c) => c.name.trim());
  }

  function canSubmit(): boolean {
    return (
      canGoToStep3() &&
      characters.every((c) => c.description.trim().length >= 5)
    );
  }

  async function handleSubmit() {
    if (!canSubmit() || !selectedTemplateId || !selectedStyleSlug) return;
    setCreating(true);
    setError(null);
    try {
      const proj = await apiFetch<KidsProject>("/api/kids/projects", {
        method: "POST",
        body: JSON.stringify({
          template_id: selectedTemplateId,
          style_slug: selectedStyleSlug,
          scintilla,
          characters,
        }),
      });
      // Va all'anteprima del libretto (Sett. 4 = step generazione)
      window.location.href = `/app/kids/${proj.id}`;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setCreating(false);
    }
  }

  if (loadingData) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento template...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Top nav */}
      <div className="mb-4">
        <Link
          href="/app/kids"
          className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] transition-colors"
        >
          ← Tutti i libretti
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-1">⭐ Nuovo libretto KIDS</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-8">
        Step {step} di 3 — {STEP_LABELS[step]}
      </p>

      {/* Step indicator */}
      <div className="flex gap-2 mb-8">
        {([1, 2, 3] as Step[]).map((n) => (
          <div
            key={n}
            className={`flex-1 h-1.5 rounded-full transition-colors ${
              step >= n ? "bg-[var(--color-accent)]" : "bg-[var(--color-border)]"
            }`}
          />
        ))}
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-6">
          {error}
        </p>
      )}

      {/* STEP 1 — Template + Stile */}
      {step === 1 && (
        <div className="space-y-8">
          <section>
            <h2 className="text-lg font-semibold mb-4">Scegli il template</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTemplateId(t.id)}
                  className={`text-left p-4 rounded-xl border transition-all ${
                    selectedTemplateId === t.id
                      ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5"
                      : "border-[var(--color-border)] bg-[var(--color-bg-elev)] hover:border-[var(--color-accent)]/50"
                  }`}
                >
                  <div className="font-medium mb-1">{t.label}</div>
                  <div className="text-xs text-[var(--color-fg-muted)]">
                    {t.notes}
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold mb-4">Scegli lo stile</h2>
            <div className="grid grid-cols-3 gap-3">
              {styles.map((s) => (
                <button
                  key={s.slug}
                  onClick={() => setSelectedStyleSlug(s.slug)}
                  className={`p-4 rounded-xl border text-center transition-all ${
                    selectedStyleSlug === s.slug
                      ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5"
                      : "border-[var(--color-border)] bg-[var(--color-bg-elev)] hover:border-[var(--color-accent)]/50"
                  }`}
                >
                  <div className="font-medium">{s.label}</div>
                </button>
              ))}
            </div>
          </section>

          <div className="flex justify-end pt-4">
            <button
              onClick={() => setStep(2)}
              disabled={!canGoToStep2()}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Avanti →
            </button>
          </div>
        </div>
      )}

      {/* STEP 2 — Scintilla + nomi */}
      {step === 2 && (
        <div className="space-y-6">
          <section>
            <label htmlFor="scintilla" className="block text-lg font-semibold mb-2">
              ✨ Scintilla narrativa
            </label>
            <p className="text-sm text-[var(--color-fg-muted)] mb-3">
              Una frase o un paragrafo che descrive la storia. Es: <em>"Mia il riccio
              perde la mamma nel bosco e con l'aiuto di nuovi amici torna a casa."</em>
            </p>
            <textarea
              id="scintilla"
              value={scintilla}
              onChange={(e) => setScintilla(e.target.value)}
              rows={5}
              placeholder="Scrivi qui la tua scintilla..."
              className="w-full px-4 py-3 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)]"
            />
          </section>

          <section>
            <h2 className="text-lg font-semibold mb-3">
              I nomi dei {requiredChars}{" "}
              {requiredChars === 1 ? "personaggio" : "personaggi"}
            </h2>
            <div className="space-y-2">
              {characters.map((c, i) => (
                <input
                  key={i}
                  type="text"
                  value={c.name}
                  onChange={(e) => updateCharacter(i, "name", e.target.value)}
                  placeholder={`Nome personaggio ${i + 1}`}
                  className="w-full px-4 py-2 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)]"
                />
              ))}
            </div>
          </section>

          <div className="flex justify-between pt-4">
            <button
              onClick={() => setStep(1)}
              className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-5 py-2 transition-colors"
            >
              ← Indietro
            </button>
            <button
              onClick={() => setStep(3)}
              disabled={!canGoToStep3()}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Avanti →
            </button>
          </div>
        </div>
      )}

      {/* STEP 3 — Descrizioni personaggi */}
      {step === 3 && (
        <div className="space-y-6">
          <section>
            <h2 className="text-lg font-semibold mb-2">
              👥 Descrivi i personaggi
            </h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-4">
              Descrizione visiva concreta: aspetto, colori, vestiti, dettagli
              distintivi. Sarà usata dall'AI per generare le immagini coerenti.
            </p>
            <div className="space-y-4">
              {characters.map((c, i) => (
                <div
                  key={i}
                  className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4"
                >
                  <h3 className="font-semibold mb-2">
                    {c.name || `Personaggio ${i + 1}`}
                  </h3>
                  <textarea
                    value={c.description}
                    onChange={(e) =>
                      updateCharacter(i, "description", e.target.value)
                    }
                    rows={3}
                    placeholder={`Es: ${c.name || "Mia"} è un riccio piccolo, marrone scuro, occhi grandi neri, indossa una sciarpetta rossa`}
                    className="w-full px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-[var(--color-fg)] focus:outline-none focus:border-[var(--color-accent)]"
                  />
                </div>
              ))}
            </div>
          </section>

          <div className="bg-[var(--color-accent)]/5 border border-[var(--color-accent)]/20 rounded-xl p-4 text-sm">
            <p className="text-[var(--color-fg-muted)]">
              <span className="text-[var(--color-accent)] font-semibold">
                Prossimo:
              </span>{" "}
              al click su "Crea libretto" salviamo il progetto. Generazione AI
              della storia e delle vignette arriva nel prossimo aggiornamento
              dell'app.
            </p>
          </div>

          <div className="flex justify-between pt-4">
            <button
              onClick={() => setStep(2)}
              className="text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] px-5 py-2 transition-colors"
            >
              ← Indietro
            </button>
            <button
              onClick={handleSubmit}
              disabled={!canSubmit() || creating}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {creating ? "Creo..." : "✨ Crea libretto"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
