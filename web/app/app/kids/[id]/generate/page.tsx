"use client";

import Link from "next/link";
import { use, useEffect, useRef, useState } from "react";

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

export default function KidsGeneratePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [status, setStatus] = useState<string>("Sto preparando la scatola magica...");
  const [emoji, setEmoji] = useState<string>("📦");
  const [current, setCurrent] = useState(0);
  const [total, setTotal] = useState(0);
  const [completed, setCompleted] = useState<CompletedImage[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const startedRef = useRef(false);

  useEffect(() => {
    // Evita doppio fire in dev (StrictMode)
    if (startedRef.current) return;
    startedRef.current = true;

    const source = new EventSource(
      `/api/kids/projects/${id}/generate-stream`,
      { withCredentials: true }
    );

    source.onmessage = (e) => {
      try {
        const data: SSEEvent = JSON.parse(e.data);
        if (data.type === "start") {
          setTotal(data.total_steps ?? 0);
        } else if (data.type === "step") {
          if (data.kind === "reference") setEmoji("👤");
          else if (data.kind === "cover") setEmoji("📕");
          else setEmoji("🎨");
          setStatus(data.label ?? "...");
          setCurrent(data.current ?? 0);
        } else if (data.type === "image_ready") {
          // Aggiungi immagine alla galleria
          const ts = Date.now();
          let src = "";
          let label = "";
          if (data.kind === "cover") {
            src = `/api/kids/projects/${id}/images/cover?t=${ts}`;
            label = "📕 Copertina";
          } else if (data.kind === "panel" && data.page && data.panel) {
            src = `/api/kids/projects/${id}/images/panel/${data.page}/${data.panel}?t=${ts}`;
            label = `P${data.page}V${data.panel}`;
          } else if (data.kind === "reference") {
            label = `👋 ${data.name ?? "?"}`;
          }
          if (label) {
            setCompleted((prev) => [
              ...prev,
              { kind: data.kind!, label, src },
            ]);
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
      // EventSource auto-reconnect; lascia stare. Se il server ha chiuso,
      // l'event "done" è già arrivato.
    };

    return () => {
      source.close();
    };
  }, [id]);

  const progress = total > 0 ? (current / total) * 100 : 0;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">🎁 Sto creando il tuo libretto</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-8">
        Resta qui, ogni passo lo vedi in tempo reale.
      </p>

      {/* Status box */}
      <div className="bg-gradient-to-br from-[var(--color-accent)]/20 to-[var(--color-bg-elev)] border-2 border-[var(--color-accent)] rounded-2xl p-8 text-center mb-6">
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
              {current} / {total}
            </p>
          </>
        )}
      </div>

      {/* Errori */}
      {errors.length > 0 && (
        <div className="bg-red-950/30 border border-red-900/50 rounded-lg px-4 py-3 mb-6 text-sm">
          <p className="font-semibold mb-1 text-red-400">Alcuni errori:</p>
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
