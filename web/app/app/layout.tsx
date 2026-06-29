import { cookies } from "next/headers";
import Link from "next/link";
import LogoutButton from "@/components/LogoutButton";

/**
 * Layout per la zona autenticata (/app/*).
 *
 * Server component: legge il cookie e decide se mostrare Admin link.
 * Fetch a /api/auth/me via cookie forwarding per ricavare is_admin.
 */
async function getCurrentUser(): Promise<{ is_admin: boolean } | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get("snaptoon_token");
  if (!token) return null;
  try {
    const res = await fetch("http://localhost:8000/api/auth/me", {
      headers: { Cookie: `snaptoon_token=${token.value}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  const isAdmin = user?.is_admin ?? false;

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
          {isAdmin && (
            <>
              <div className="my-2 border-t border-[var(--color-border)]" />
              <SidebarLink href="/app/admin" icon="🛠" label="Admin" />
            </>
          )}
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
