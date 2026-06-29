import Link from "next/link";
import LogoutButton from "@/components/LogoutButton";

/**
 * Layout per la zona autenticata (/app/*).
 *
 * Sidebar persistente a sinistra (240px), main content che scrolla.
 * Server component pure — LogoutButton è il client component isolato.
 */
export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 flex-shrink-0 bg-[#0A0E17] border-r border-[var(--color-border)] flex flex-col sticky top-0 h-screen">
        <div className="p-5">
          <Link
            href="/app"
            className="text-xl font-bold text-[var(--color-accent)] hover:text-[var(--color-accent-hover)] transition-colors"
          >
            📚 SnapToon
          </Link>
        </div>

        <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
          <SidebarLink href="/app" icon="📚" label="I miei progetti" />
          <div className="my-2 border-t border-[var(--color-border)]" />
          <SidebarLink href="/app/kids" icon="⭐" label="KIDS" />
          <div className="my-2 border-t border-[var(--color-border)]" />
          <SidebarLink href="/app/account" icon="⚙️" label="Account" />
        </nav>

        <div className="p-3 border-t border-[var(--color-border)]">
          <LogoutButton />
        </div>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}

function SidebarLink({
  href,
  icon,
  label,
}: {
  href: string;
  icon: string;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-[var(--color-fg-muted)] hover:bg-[var(--color-bg-elev)] hover:text-[var(--color-fg)] rounded-md transition-colors"
    >
      <span className="text-base">{icon}</span>
      <span>{label}</span>
    </Link>
  );
}
