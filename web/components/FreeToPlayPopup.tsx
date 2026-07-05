"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Detail = {
  code?: string;
  quota_type?: string;
  message?: string;
  // Legacy (retrocompat)
  action?: string;
};

const QUOTA_LABEL: Record<string, string> = {
  libretti_kids: "libretti KIDS",
  progetti_pro: "progetti Pro",
  cover: "cover",
  card: "figurine",
  striscia: "striscia gratuita",
};

const UPSELL_HINT: Record<string, string> = {
  libretti_kids: "Compra un pacchetto libretti (da €4,99) o passa al piano PRO.",
  progetti_pro: "Compra un pacchetto progetti (da €9,99) o passa al piano PRO.",
  cover: "Compra un pacchetto cover (da €5,99 x3) o attendi il rinnovo mensile.",
  card: "Compra un pacchetto figurine (da €4,99 x3) o attendi il rinnovo mensile.",
  striscia: "Con Free-To-Play hai 1 striscia inclusa. Passa a KIDS (€6,99/mese) o PRO (€19/mese).",
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
    function esc(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("snaptoon:ftp_exhausted", handler as EventListener);
    window.addEventListener("keydown", esc);
    return () => {
      window.removeEventListener(
        "snaptoon:ftp_exhausted",
        handler as EventListener,
      );
      window.removeEventListener("keydown", esc);
    };
  }, []);

  if (!open) return null;

  const quotaType = detail?.quota_type || detail?.action || "";
  const quotaLabel = QUOTA_LABEL[quotaType] || "crediti";
  const hint = UPSELL_HINT[quotaType] || "Passa a un piano superiore o acquista un pacchetto extra.";
  const message = detail?.message ||
    `Hai finito i ${quotaLabel}. Aggiungi un pacchetto extra per continuare.`;

  return (
    <div
      className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4"
      onClick={() => setOpen(false)}
    >
      <div
        className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-2xl p-8 max-w-md w-full text-center relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={() => setOpen(false)}
          className="absolute top-3 right-3 text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] text-2xl"
          aria-label="Chiudi"
        >
          ×
        </button>

        <div className="text-6xl mb-4">🎨</div>

        <h2 className="text-2xl font-bold mb-2">
          Quota {quotaLabel} esaurita
        </h2>

        <p className="text-lg font-semibold text-[var(--color-accent)] mb-4">
          TI È PIACIUTO SNAPTOON?
        </p>

        <p className="text-sm text-[var(--color-fg-muted)] mb-2">{message}</p>
        <p className="text-xs text-[var(--color-fg-muted)] mb-6 italic">{hint}</p>

        <div className="flex flex-col gap-2">
          <Link
            href="/app/pacchetti"
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-bold py-3 rounded-lg text-base"
            onClick={() => setOpen(false)}
          >
            📦 Aggiungi pacchetto extra
          </Link>
          <Link
            href="/abbonamenti"
            className="border border-[var(--color-border)] hover:border-[var(--color-accent)] text-[var(--color-fg)] font-semibold py-2.5 rounded-lg text-sm"
            onClick={() => setOpen(false)}
          >
            Confronta piani →
          </Link>
        </div>

        <p className="text-xs text-[var(--color-fg-muted)] mt-4">
          Disdetta possibile in qualsiasi momento.
        </p>
      </div>
    </div>
  );
}
