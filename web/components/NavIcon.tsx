import type { CSSProperties, ReactElement } from "react";

const PATHS: Record<string, ReactElement> = {
  home: (
    <path d="M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />
  ),
  star: (
    <path d="M12 3.5 14.6 9l5.9.6-4.4 4 1.2 5.8L12 16.6 6.7 19.4l1.2-5.8-4.4-4 5.9-.6z" />
  ),
  account: (
    <>
      <rect x="2" y="5" width="20" height="14" rx="2" />
      <path d="M2 10h20" />
    </>
  ),
  admin: (
    <path d="M12 22c4.5-1.4 8-5 8-10V5l-8-3-8 3v7c0 5 3.5 8.6 8 10z" />
  ),
  testo: (
    <>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4z" />
    </>
  ),
  stile: (
    <>
      <circle cx="13.5" cy="6.5" r="1" />
      <circle cx="17.5" cy="10.5" r="1" />
      <circle cx="8.5" cy="7.5" r="1" />
      <circle cx="6.5" cy="12.5" r="1" />
      <path d="M12 2C6.5 2 2 6 2 11a6 6 0 0 0 6 6c1 0 1.5-.8 1.5-1.5 0-.4-.2-.7-.4-1-.2-.3-.4-.6-.4-1 0-.8.7-1.5 1.5-1.5H12a5 5 0 0 0 5-5c0-3.9-4-7-9-7z" />
    </>
  ),
  personaggi: (
    <>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </>
  ),
  genera: (
    <>
      <path d="M12 3 13.6 8.4 19 10l-5.4 1.6L12 17l-1.6-5.4L5 10l5.4-1.6z" />
      <path d="M19 3v3" />
      <path d="M20.5 4.5h-3" />
      <path d="M5 16v2" />
      <path d="M6 17H4" />
    </>
  ),
  impagina: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M9 3v18" />
      <path d="M9 12h12" />
    </>
  ),
};

export function NavIcon({
  name,
  active = false,
  size = 18,
}: {
  name: string;
  active?: boolean;
  size?: number;
}) {
  if (active) {
    const style: CSSProperties = {
      display: "inline-block",
      width: size,
      height: size,
      borderRadius: 5,
      background: "var(--color-accent)",
      flexShrink: 0,
    };
    return <span style={style} aria-hidden />;
  }
  const path = PATHS[name] ?? PATHS.account;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ flexShrink: 0 }}
      aria-hidden
    >
      {path}
    </svg>
  );
}
