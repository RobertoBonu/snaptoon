"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NavIcon } from "@/components/NavIcon";

type Item = {
  href: string;
  icon: string;
  label: string;
  isActive: (path: string) => boolean;
};

// Item base "I MIEI PROGETTI" (flusso Pro), nascosto agli account con
// role="kids" perché non hanno accesso al flusso Pro.
const PROGETTI_ITEM: Item = {
  href: "/app",
  icon: "home",
  label: "I MIEI PROGETTI",
  isActive: (p) => p === "/app" || p.startsWith("/app/projects"),
};

const ITEMS_COMUNI: Item[] = [
  {
    href: "/app/kids",
    icon: "star",
    label: "KIDS",
    isActive: (p) => p.startsWith("/app/kids"),
  },
  {
    href: "/app/my-characters",
    icon: "personaggi",
    label: "I MIEI PERSONAGGI",
    isActive: (p) => p.startsWith("/app/my-characters"),
  },
  {
    href: "/app/my-cards",
    icon: "personaggi",
    label: "LE MIE FIGURINE",
    isActive: (p) => p.startsWith("/app/my-cards"),
  },
  {
    href: "/app/account",
    icon: "account",
    label: "Account",
    isActive: (p) => p.startsWith("/app/account"),
  },
];

export default function AppSidebarNav({
  isAdmin,
  role,
}: {
  isAdmin: boolean;
  role?: string;
}) {
  const pathname = usePathname() ?? "";

  // Gli account KIDS vedono solo: KIDS, I MIEI PERSONAGGI, Account (+ Admin
  // se admin, ma un utente KIDS non può essere admin nella pratica).
  // Gli altri ruoli vedono anche "I MIEI PROGETTI" (flusso Pro).
  const isKidsOnly = role === "kids";
  const baseItems: Item[] = isKidsOnly
    ? ITEMS_COMUNI
    : [PROGETTI_ITEM, ...ITEMS_COMUNI];

  const items: Item[] = isAdmin
    ? [
        ...baseItems,
        {
          href: "/app/admin",
          icon: "admin",
          label: "Admin",
          isActive: (p) => p.startsWith("/app/admin"),
        },
      ]
    : baseItems;

  return (
    <nav className="flex-1 px-2 py-2 space-y-1 overflow-y-auto">
      {items.map((item) => {
        const active = item.isActive(pathname);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-3 pl-3 pr-3 py-2.5 text-sm font-medium rounded-md border-l-[3px] transition-colors ${
              active
                ? "text-[var(--color-accent)] bg-[#1A2035] border-[var(--color-accent)]"
                : "text-[var(--color-fg-muted)] border-transparent hover:bg-[var(--color-bg-elev)] hover:text-[var(--color-fg)]"
            }`}
          >
            <NavIcon name={item.icon} active={active} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
