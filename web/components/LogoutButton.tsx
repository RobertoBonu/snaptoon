"use client";

export default function LogoutButton() {
  async function handleLogout() {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } finally {
      window.location.href = "/";
    }
  }

  return (
    <button
      onClick={handleLogout}
      className="w-full text-left px-3 py-2 text-sm text-[var(--color-fg-muted)] hover:text-red-400 transition-colors rounded"
    >
      🚪 Esci
    </button>
  );
}
