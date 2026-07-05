"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Detail = {
  code?: string;
  action?: string;
  message?: string;
};

export default function FreeToPlayPopup() {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<Detail | null>(null);

  useEffect(() => {
    function handler(e: Event) {
      const custom = e as CustomEvent<Detail>;
      setDetail(custom.detail || null);
      setOpen(true);
    }
    window.addEventListener("snaptoon:ftp_exhausted", handler as EventListener);
    return () =>
      window.removeEventListener(
        "snaptoon:ftp_exhausted",
        handler as EventListener,
      );
  }, []);

  if (!open) return null;

  const isPlanLock = detail?.code === "free_to_play_plan_locked";

  return (
    <div className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4">
      <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-2xl p-8 max-w-md w-full text-center relative">
        <button
          onClick={() => setOpen(false)}
          className="absolute top-3 right-3 text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] text-2xl"
          aria-label="Chiudi"
        >
          ×
        </button>

        <div className="text-6xl mb-4">🎨</div>

        <h2 className="text-2xl font-bold mb-2">
          {isPlanLock ? "Piano gratuito limitato" : "Hai utilizzato i crediti gratuiti"}
        </h2>

        <p className="text-lg font-semibold text-[var(--color-accent)] mb-4">
          TI È PIACIUTO SNAPTOON?
        </p>

        <p className="text-sm text-[var(--color-fg-muted)] mb-6">
          {isPlanLock
            ? "Il piano Free-To-Play consente solo la Striscia (1 tavola). Per libretti Brevi e Lunghi passa a un piano superiore."
            : "Il tuo piano Free-To-Play include 1 striscia, 1 figurina e 1 cover. Passa a un abbonamento per continuare a creare senza limiti."}
        </p>

        <Link
          href="/abbonamenti"
          className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-bold px-8 py-3 rounded-lg text-lg"
          onClick={() => setOpen(false)}
        >
          Abbonati →
        </Link>

        <p className="text-xs text-[var(--color-fg-muted)] mt-4">
          Piani da €19/mese, disdetta in qualsiasi momento.
        </p>
      </div>
    </div>
  );
}
