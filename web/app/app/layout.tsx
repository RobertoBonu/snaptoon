import { cookies } from "next/headers";
import Link from "next/link";
import LogoutButton from "@/components/LogoutButton";
import AppSidebarNav from "@/components/AppSidebarNav";

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
            SnapToon
          </Link>
        </div>

        <AppSidebarNav isAdmin={isAdmin} />

        <div className="p-3 border-t border-[var(--color-border)]">
          <LogoutButton />
        </div>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
