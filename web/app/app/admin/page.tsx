"use client";

import { useEffect, useState } from "react";
import {
  apiFetch,
  type AdminRoleInfo,
  type AdminStats,
  type AdminUser,
  type AdminUserList,
} from "@/lib/api";

export default function AdminPage() {
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [roles, setRoles] = useState<AdminRoleInfo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [working, setWorking] = useState<string | null>(null);

  // Form crea utente
  const [newEmail, setNewEmail] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [newRole, setNewRole] = useState("autore_base");

  async function load() {
    try {
      setError(null);
      const [u, st, rs] = await Promise.all([
        apiFetch<AdminUserList>("/api/admin/users"),
        apiFetch<AdminStats>("/api/admin/stats"),
        apiFetch<{ roles: AdminRoleInfo[] }>("/api/admin/roles"),
      ]);
      setUsers(u.users);
      setStats(st);
      setRoles(rs.roles);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setWorking("create");
    setError(null);
    try {
      await apiFetch<AdminUser>("/api/admin/users", {
        method: "POST",
        body: JSON.stringify({
          email: newEmail,
          password: newPwd,
          role: newRole,
          must_change_password: true,
        }),
      });
      setNewEmail("");
      setNewPwd("");
      setShowCreate(false);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function changeRole(userId: string, role: string, resetCredits: boolean) {
    setWorking(userId);
    try {
      await apiFetch(`/api/admin/users/${userId}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role, reset_credits: resetCredits }),
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function grantCredits(userId: string) {
    const amount = prompt("Quanti crediti aggiungere?");
    if (!amount) return;
    const num = parseInt(amount, 10);
    if (Number.isNaN(num) || num < 1) {
      alert("Valore invalido");
      return;
    }
    const reason = prompt("Motivo (opzionale)") || "Admin grant";
    setWorking(userId);
    try {
      await apiFetch(`/api/admin/users/${userId}/grant-credits`, {
        method: "POST",
        body: JSON.stringify({ amount: num, reason }),
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function resetPassword(userId: string, email: string) {
    const newPwd = prompt(
      `Nuova password per ${email} (min 8 caratteri).\nL'utente dovrà cambiarla al prossimo login.`
    );
    if (!newPwd || newPwd.length < 8) {
      alert("Password troppo corta o annullato");
      return;
    }
    setWorking(userId);
    try {
      await apiFetch(`/api/admin/users/${userId}/reset-password`, {
        method: "POST",
        body: JSON.stringify({ new_password: newPwd }),
      });
      await load();
      alert("Password aggiornata. L'utente dovrà cambiarla al prossimo login.");
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  async function toggleActive(userId: string, currentActive: boolean) {
    const verb = currentActive ? "disabilitare" : "riattivare";
    if (!confirm(`Sicuro di voler ${verb} questo utente?`)) return;
    setWorking(userId);
    try {
      await apiFetch(
        `/api/admin/users/${userId}/active?active=${!currentActive}`,
        { method: "PATCH" }
      );
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setWorking(null);
    }
  }

  if (users === null && !error) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">🛠 Pannello admin</h1>
          <p className="text-sm text-[var(--color-fg-muted)]">
            Gestione utenti, ruoli, crediti.
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2.5 rounded-lg"
        >
          + Nuovo utente
        </button>
      </header>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard label="Utenti totali" value={stats.total_users} />
          <StatCard label="Attivi" value={stats.active_users} />
          <StatCard label="Attivi (7gg)" value={stats.active_last_7_days} />
          <StatCard label="Progetti totali" value={stats.total_projects} />
        </div>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5 mb-6 space-y-3"
        >
          <h3 className="font-semibold">Nuovo utente</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <input
              type="email"
              placeholder="email@esempio.it"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              required
              className="px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
            <input
              type="text"
              placeholder="Password (min 8)"
              value={newPwd}
              onChange={(e) => setNewPwd(e.target.value)}
              minLength={8}
              required
              className="px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            />
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded"
            >
              {roles.map((r) => (
                <option key={r.key} value={r.key}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={working === "create"}
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded disabled:opacity-50"
            >
              {working === "create" ? "..." : "Crea"}
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="text-[var(--color-fg-muted)] px-5 py-2"
            >
              Annulla
            </button>
          </div>
        </form>
      )}

      {/* Users table */}
      <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--color-bg)] text-xs uppercase tracking-wider text-[var(--color-fg-muted)]">
            <tr>
              <th className="px-4 py-3 text-left">Email</th>
              <th className="px-4 py-3 text-left">Ruolo</th>
              <th className="px-4 py-3 text-right">Crediti</th>
              <th className="px-4 py-3 text-right">Progetti</th>
              <th className="px-4 py-3 text-left">Stato</th>
              <th className="px-4 py-3 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--color-border)]">
            {users?.map((u) => (
              <tr
                key={u.id}
                className={`hover:bg-[var(--color-border)]/20 ${
                  !u.is_active ? "opacity-50" : ""
                }`}
              >
                <td className="px-4 py-3">
                  <div className="font-medium">{u.email}</div>
                  <div className="text-xs text-[var(--color-fg-muted)]">
                    {new Date(u.created_at).toLocaleDateString("it-IT")}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={u.role}
                    onChange={(e) =>
                      changeRole(u.id, e.target.value, false)
                    }
                    disabled={working === u.id}
                    className="px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-xs"
                  >
                    {roles.map((r) => (
                      <option key={r.key} value={r.key}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3 text-right">
                  <div>
                    <span className="text-[var(--color-accent)] font-medium">
                      {u.credits_remaining}
                    </span>
                    <span className="text-[var(--color-fg-muted)]">
                      {" "}
                      / {u.credits_total}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right">{u.project_count}</td>
                <td className="px-4 py-3">
                  {u.is_active ? (
                    <span className="text-green-400 text-xs">Attivo</span>
                  ) : (
                    <span className="text-red-400 text-xs">Disattivato</span>
                  )}
                  {u.must_change_password && (
                    <span className="block text-[10px] text-amber-400">
                      Cambio pwd
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-right space-x-1">
                  <button
                    onClick={() => grantCredits(u.id)}
                    disabled={working === u.id}
                    title="Aggiungi crediti"
                    className="text-xs px-2 py-1 hover:bg-[var(--color-accent)]/10 hover:text-[var(--color-accent)] rounded"
                  >
                    💰
                  </button>
                  <button
                    onClick={() => resetPassword(u.id, u.email)}
                    disabled={working === u.id}
                    title="Reset password"
                    className="text-xs px-2 py-1 hover:bg-[var(--color-accent)]/10 rounded"
                  >
                    🔑
                  </button>
                  <button
                    onClick={() => toggleActive(u.id, u.is_active)}
                    disabled={working === u.id}
                    title={u.is_active ? "Disattiva" : "Riattiva"}
                    className="text-xs px-2 py-1 hover:bg-red-950/30 hover:text-red-400 rounded"
                  >
                    {u.is_active ? "🚫" : "✓"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Distribuzione ruoli */}
      {stats && (
        <div className="mt-6 bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-5">
          <h3 className="font-semibold mb-3">Distribuzione ruoli</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
            {Object.entries(stats.users_by_role).map(([role, count]) => (
              <div key={role} className="text-center">
                <div className="text-2xl font-bold text-[var(--color-accent)]">
                  {count}
                </div>
                <div className="text-xs text-[var(--color-fg-muted)] uppercase tracking-wider">
                  {role}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4">
      <div className="text-3xl font-bold text-[var(--color-accent)]">
        {value}
      </div>
      <div className="text-xs text-[var(--color-fg-muted)] uppercase tracking-wider mt-1">
        {label}
      </div>
    </div>
  );
}
