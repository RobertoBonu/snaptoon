"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { use } from "react";
import { NavIcon } from "@/components/NavIcon";

const TABS = [
  { slug: "testo", icon: "testo", label: "Testo" },
  { slug: "stile", icon: "stile", label: "Stile" },
  { slug: "personaggi", icon: "personaggi", label: "Personaggi" },
  { slug: "genera", icon: "genera", label: "Genera" },
  { slug: "impagina", icon: "impagina", label: "Impagina" },
];

export default function ProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const pathname = usePathname();

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--color-border)] bg-[var(--color-bg-elev)]/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-4">
          <Link
            href="/app"
            className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)] whitespace-nowrap"
          >
            ← I miei progetti
          </Link>
          <div className="text-sm text-[var(--color-fg-muted)] hidden md:block">
            /
          </div>
          <div className="text-sm font-medium truncate hidden md:block">
            {slug}
          </div>
        </div>
        <nav className="max-w-7xl mx-auto px-6 -mb-px overflow-x-auto">
          <div className="flex gap-1">
            {TABS.map((t) => {
              const href = `/app/projects/${slug}/${t.slug}`;
              const active = pathname?.startsWith(href);
              return (
                <Link
                  key={t.slug}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    active
                      ? "text-[var(--color-accent)] border-[var(--color-accent)]"
                      : "text-[var(--color-fg-muted)] border-transparent hover:text-[var(--color-fg)] hover:border-[var(--color-border)]"
                  }`}
                >
                  <NavIcon name={t.icon} size={16} />
                  <span>{t.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
