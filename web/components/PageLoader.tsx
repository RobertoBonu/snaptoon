/**
 * Loading overlay riusabile per le pagine authenticate.
 *
 * Uso:
 *   {loading && <PageLoader message="Caricamento sceneggiatura..." />}
 *
 * Design:
 *   - Absolute su tutta la pagina (dentro <main>)
 *   - Blur del contenuto sotto (backdrop-blur)
 *   - Spinner ambra rotante + messaggio + brand SnapToon
 *   - Pulse subtle sul messaggio
 */
export default function PageLoader({
  message = "Caricamento...",
  fullscreen = false,
}: {
  message?: string;
  fullscreen?: boolean;
}) {
  return (
    <div
      className={`${
        fullscreen ? "fixed" : "absolute"
      } inset-0 z-40 flex flex-col items-center justify-center gap-4 bg-[var(--color-bg)]/85 backdrop-blur-sm`}
      role="status"
      aria-live="polite"
    >
      <div className="text-sm text-[var(--color-accent)] font-semibold tracking-widest uppercase">
        📚 SnapToon
      </div>
      <div className="relative w-14 h-14">
        <div className="absolute inset-0 rounded-full border-4 border-[var(--color-border)]" />
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-[var(--color-accent)] animate-spin" />
      </div>
      <div className="text-[var(--color-fg)] text-base font-medium animate-pulse">
        {message}
      </div>
    </div>
  );
}


/**
 * Loader inline compatto per azioni granulari (es. "sto rigenerando",
 * "sto salvando", ecc). Non copre la pagina, sta accanto al bottone.
 */
export function InlineLoader({ label }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs text-[var(--color-fg-muted)]">
      <span className="relative w-3 h-3">
        <span className="absolute inset-0 rounded-full border-2 border-[var(--color-border)]" />
        <span className="absolute inset-0 rounded-full border-2 border-transparent border-t-[var(--color-accent)] animate-spin" />
      </span>
      {label && <span>{label}</span>}
    </span>
  );
}
