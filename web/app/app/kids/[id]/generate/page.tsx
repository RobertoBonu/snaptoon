"use client";

import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";
import { apiFetch, type KidsProjectDetails } from "@/lib/api";

interface SSEEvent {
  type: "start" | "step" | "image_ready" | "error" | "done";
  total_steps?: number;
  kind?: "reference" | "cover" | "panel";
  label?: string;
  current?: number;
  total?: number;
  name?: string;
  page?: number;
  panel?: number;
  message?: string;
}

interface CompletedImage {
  kind: "reference" | "cover" | "panel";
  label: string;
  src: string;
}

// Timeline degli step attesi — mostrata da subito così l'utente sa
// cosa deve succedere e cosa manca. Ogni voce può essere "done" o in
// attesa. La UI si aggiorna in tempo reale al ricevere gli eventi SSE.
interface Step {
  kind: "reference" | "cover" | "panel";
  label: string;
  key: string; // univoco per identificare lo step
  done: boolean;
  active: boolean;
}

export default function KidsGeneratePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const [status, setStatus] = useState<string>("Mi connetto al server...");
  const [emoji, setEmoji] = useState<string>("📦");
  const [current, setCurrent] = useState(0);
  const [total, setTotal] = useState(0);
  const [completed, setCompleted] = useState<CompletedImage[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  // Heartbeat: quanti secondi dall'ultimo evento SSE. Se sale sopra 15s
  // l'utente vede un messaggio esplicito che è normale (l'AI sta
  // generando le immagini, ci mette 5-15s per ognuna).
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);
  const [connected, setConnected] = useState(false);

  const startedRef = useRef(false);
  const lastUpdateRef = useRef<number>(Date.now());

  // Timer del heartbeat: aggiorna secondi trascorsi dall'ultimo evento
  useEffect(() => {
    const iv = setInterval(() => {
      const sec = Math.floor((Date.now() - lastUpdateRef.current) / 1000);
      setSecondsSinceUpdate(sec);
    }, 500);
    return () => clearInterval(iv);
  }, []);

  // Bump del timer alla ricezione di un evento
  function touch() {
    lastUpdateRef.current = Date.now();
    setSecondsSinceUpdate(0);
  }

  // Fetch iniziale dei details per costruire la timeline attesa
  async function fetchInitialTimeline() {
    try {
      const d = await apiFetch<KidsProjectDetails>(
        `/api/kids/projects/${id}/details`
      );
      const timelineSteps: Step[] = [];

      // Cover attesa
      timelineSteps.push({
        kind: "cover",
        label: "📕 Copertina",
        key: "cover",
        done: d.has_cover,
        active: false,
      });

      // Vignette attese (dalla story, se già generata)
      if (d.story) {
        const vigDone = new Set(
          d.vignettes.map((v) => `${v.page_number}_${v.panel_number}`)
        );
        for (const p of d.story.pages) {
          for (const pn of p.panels) {
            const key = `p${p.page_number}_v${pn.number}`;
            timelineSteps.push({
              kind: "panel",
              label: `Pagina ${p.number} · Vignetta ${pn.number}`,
              key,
              done: vigDone.has(`${p.number}_${pn.number}`),
              active: false,
            });
          }
        }
      }
      setSteps(timelineSteps);
    } catch {
      // Non è un errore bloccante, la SSE popola comunque
    }
  }

  useEffect(() => {
    fetchInitialTimeline();
  }, [id]);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    const source = new EventSource(
      `/api/kids/projects/${id}/generate-stream`,
      { withCredentials: true }
    );

    source.onopen = () => {
      setConnected(true);
      setStatus("Sto preparando la scatola magica...");
      touch();
    };

    source.onmessage = (e) => {
      touch();
      try {
        const data: SSEEvent = JSON.parse(e.data);
        if (data.type === "start") {
          setTotal(data.total_steps ?? 0);
          setStatus("La pipeline è partita — ora genero un pezzo alla volta");
        } else if (data.type === "step") {
          if (data.kind === "reference") setEmoji("👤");
          else if (data.kind === "cover") setEmoji("📕");
          else setEmoji("🎨");
          setStatus(data.label ?? "...");
          setCurrent(data.current ?? 0);
          // Aggiorna "active" nella timeline
          setSteps((prev) => {
            const marker = describeStepKey(data);
            return prev.map((s) => ({
              ...s,
              active: s.key === marker,
            }));
          });
        } else if (data.type === "image_ready") {
          const ts = Date.now();
          let src = "";
          let label = "";
          let stepKey: string | null = null;
          if (data.kind === "cover") {
            src = `/api/kids/projects/${id}/images/cover?t=${ts}`;
            label = "📕 Copertina";
            stepKey = "cover";
          } else if (data.kind === "panel" && data.page && data.panel) {
            src = `/api/kids/projects/${id}/images/panel/${data.page}/${data.panel}?t=${ts}`;
            label = `P${data.page}V${data.panel}`;
            stepKey = `p${data.page}_v${data.panel}`;
          } else if (data.kind === "reference") {
            label = `👋 ${data.name ?? "?"}`;
          }
          if (label) {
            setCompleted((prev) => [
              ...prev,
              { kind: data.kind!, label, src },
            ]);
          }
          if (stepKey) {
            setSteps((prev) =>
              prev.map((s) =>
                s.key === stepKey ? { ...s, done: true, active: false } : s
              )
            );
          }
        } else if (data.type === "error") {
          setErrors((prev) => [...prev, data.message ?? "Errore"]);
        } else if (data.type === "done") {
          setDone(true);
          setStatus("🎉 Il tuo libretto è pronto!");
          setEmoji("🎉");
          source.close();
          setTimeout(() => {
            window.location.href = `/app/kids/${id}`;
          }, 2500);
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    source.onerror = () => {
      setConnected(false);
      // EventSource auto-reconnect. Non chiudo, lascio riprovare.
    };

    return () => {
      source.close();
    };
  }, [id]);

  const progress = total > 0 ? (current / total) * 100 : 0;

  // Se sono passati più di 12s dall'ultimo evento e non siamo done →
  // mostro un messaggio esplicito che è normale (l'AI ci mette).
  const showLongWaitMessage = secondsSinceUpdate > 12 && !done;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <header className="mb-6">
        <h1 className="text-3xl font-bold mb-1">🎁 Sto creando il tuo libretto</h1>
        <p className="text-sm text-[var(--color-fg-muted)]">
          La generazione può richiedere 5-15 minuti. Resta qui — le vignette
          appaiono man mano che sono pronte. Puoi anche{" "}
          <Link href={`/app/kids/${id}`} className="text-[var(--color-accent)] underline">
            uscire e tornare più tardi
          </Link>
          : la pipeline continua in background.
        </p>
      </header>

      {/* Status box con heartbeat visivo */}
      <div className="bg-gradient-to-br from-[var(--color-accent)]/20 to-[var(--color-bg-elev)] border-2 border-[var(--color-accent)] rounded-2xl p-8 text-center mb-6 relative">
        {/* Spinner ambra pulsante — heartbeat visivo che l'app è viva */}
        {!done && (
          <div className="absolute top-4 right-4">
            <div className="w-4 h-4 rounded-full bg-[var(--color-accent)] animate-pulse" />
          </div>
        )}
        <div className="text-6xl mb-3">{emoji}</div>
        <p className="text-xl font-medium mb-4">{status}</p>
        {total > 0 && !done && (
          <>
            <div className="h-2 bg-[var(--color-border)] rounded-full overflow-hidden mb-2">
              <div
                className="h-full bg-[var(--color-accent)] transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-[var(--color-fg-muted)]">
              {current} / {total} passi completati
            </p>
          </>
        )}
        {/* Heartbeat testuale */}
        {!done && (
          <p className="text-[10px] text-[var(--color-fg-muted)] mt-3 uppercase tracking-widest">
            {connected ? "connesso" : "riconnessione..."} · ultimo aggiornamento{" "}
            {secondsSinceUpdate}s fa
          </p>
        )}
        {/* Messaggio esplicito per attese lunghe */}
        {showLongWaitMessage && (
          <p className="text-xs text-[var(--color-accent)] mt-2 max-w-md mx-auto">
            💡 È normale — l'AI sta disegnando un'immagine, ci mette 5-15
            secondi per ognuna. Vedrai il prossimo aggiornamento tra poco.
          </p>
        )}
      </div>

      {/* Timeline degli step attesi — sempre visibile */}
      {steps.length > 0 && (
        <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-6">
          <h2 className="text-sm font-semibold mb-3 text-[var(--color-fg-muted)] uppercase tracking-widest">
            Cosa verrà generato
          </h2>
          <ul className="space-y-1 text-sm max-h-64 overflow-y-auto">
            {steps.map((s) => (
              <li
                key={s.key}
                className={`flex items-center gap-2 py-1 ${
                  s.done
                    ? "text-[var(--color-fg-muted)] line-through"
                    : s.active
                      ? "text-[var(--color-accent)] font-medium"
                      : "text-[var(--color-fg)]"
                }`}
              >
                <span className="inline-block w-4 text-center">
                  {s.done ? "✓" : s.active ? "▶" : "·"}
                </span>
                <span>{s.label}</span>
                {s.active && (
                  <span className="text-xs text-[var(--color-accent)] ml-auto">
                    in corso...
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Errori */}
      {errors.length > 0 && (
        <div className="bg-red-950/30 border border-red-900/50 rounded-lg px-4 py-3 mb-6 text-sm">
          <p className="font-semibold mb-1 text-red-400">
            Alcuni pezzi hanno dato errore (i crediti sono stati rimborsati):
          </p>
          <ul className="space-y-0.5 text-red-300">
            {errors.map((e, i) => (
              <li key={i}>• {e}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Galleria */}
      {completed.length > 0 && (
        <>
          <h2 className="text-lg font-semibold mb-3">
            ✨ Pronti ({completed.length})
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {completed.map((item, i) => (
              <div
                key={i}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-lg overflow-hidden"
              >
                {item.src && (
                  <img
                    src={item.src}
                    alt={item.label}
                    className="w-full aspect-square object-cover"
                  />
                )}
                <div className="px-2 py-1.5 text-xs text-center text-[var(--color-fg-muted)]">
                  {item.label}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {done && (
        <div className="mt-8 text-center">
          <p className="text-[var(--color-fg-muted)] text-sm">
            Sto aprendo il libretto...
          </p>
        </div>
      )}
    </div>
  );
}

function describeStepKey(e: SSEEvent): string {
  if (e.kind === "cover") return "cover";
  if (e.kind === "panel" && e.page && e.panel) {
    return `p${e.page}_v${e.panel}`;
  }
  return "";
}
