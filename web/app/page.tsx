import Link from "next/link";

/**
 * Landing page placeholder.
 *
 * Design completo arriva separato dall'utente (canvas Replit).
 * Per ora: brand + bottone "Accedi" → /login.
 */
export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 text-center">
      <div className="text-7xl mb-6 select-none">📚</div>
      <h1 className="text-5xl md:text-6xl font-bold mb-3 text-[var(--color-accent)] tracking-tight">
        SnapToon
      </h1>
      <p className="text-xl md:text-2xl text-[var(--color-fg-muted)] mb-12 max-w-xl">
        Dall'idea al fumetto, in uno snap.
      </p>

      <Link
        href="/login"
        className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-10 py-3 rounded-lg transition-colors text-lg"
      >
        Accedi
      </Link>

      <p className="text-xs text-[var(--color-fg-muted)] opacity-60 mt-16">
        Landing placeholder. Il design completo sarà sviluppato a parte.
      </p>
    </main>
  );
}
