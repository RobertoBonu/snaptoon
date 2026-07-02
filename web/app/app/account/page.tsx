"use client";

import { useEffect, useState } from "react";
import {
  apiFetch,
  type Account,
  type CreditEntry,
  type CreditHistory,
} from "@/lib/api";

export default function AccountPage() {
  const [account, setAccount] = useState<Account | null>(null);
  const [history, setHistory] = useState<CreditEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [newPwd, setNewPwd] = useState("");
  const [changing, setChanging] = useState(false);
  const [pwdMsg, setPwdMsg] = useState<{ ok: boolean; msg: string } | null>(
    null
  );
  const [pseudonym, setPseudonym] = useState("");
  const [savingPseudonym, setSavingPseudonym] = useState(false);
  const [pseudMsg, setPseudMsg] = useState<{ ok: boolean; msg: string } | null>(
    null,
  );

  async function handleSavePseudonym(e: React.FormEvent) {
    e.preventDefault();
    setSavingPseudonym(true);
    setPseudMsg(null);
    try {
      const acc = await apiFetch<Account>("/api/account/me", {
        method: "PATCH",
        body: JSON.stringify({ pseudonym }),
      });
      setAccount(acc);
      setPseudMsg({ ok: true, msg: "Pseudonimo aggiornato." });
    } catch (e) {
      setPseudMsg({
        ok: false,
        msg: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setSavingPseudonym(false);
    }
  }

  async function load() {
    try {
      setError(null);
      const acc = await apiFetch<Account>("/api/account/me");
      setAccount(acc);
      setPseudonym(acc.pseudonym || "");
      const h = await apiFetch<CreditHistory>("/api/account/credits-history");
      setHistory(h.entries);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    setChanging(true);
    setPwdMsg(null);
    try {
      await apiFetch("/api/account/change-password", {
        method: "POST",
        body: JSON.stringify({ new_password: newPwd }),
      });
      setPwdMsg({ ok: true, msg: "Password aggiornata." });
      setNewPwd("");
      // Ricarica account per aggiornare must_change_password
      const acc = await apiFetch<Account>("/api/account/me");
      setAccount(acc);
    } catch (e) {
      setPwdMsg({
        ok: false,
        msg: e instanceof Error ? e.message : String(e),
      });
    } finally {
      setChanging(false);
    }
  }

  if (account === null && !error) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">⚙️ Account</h1>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}

      {account && (
        <>
          {/* Profilo */}
          <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Profilo</h2>
            <dl className="grid grid-cols-3 gap-y-3 text-sm">
              <dt className="text-[var(--color-fg-muted)]">Email</dt>
              <dd className="col-span-2">{account.email}</dd>

              <dt className="text-[var(--color-fg-muted)]">Ruolo</dt>
              <dd className="col-span-2">{account.role}</dd>

              <dt className="text-[var(--color-fg-muted)]">Piano</dt>
              <dd className="col-span-2">{account.plan_label}</dd>

              <dt className="text-[var(--color-fg-muted)]">Crediti</dt>
              <dd className="col-span-2">
                <span className="text-[var(--color-accent)] font-semibold text-base">
                  {account.credits_remaining}
                </span>{" "}
                <span className="text-[var(--color-fg-muted)]">
                  rimanenti su {account.credits_total} totali · {account.credits_used} usati
                </span>
              </dd>

              <dt className="text-[var(--color-fg-muted)]">Iscritto dal</dt>
              <dd className="col-span-2 text-[var(--color-fg-muted)]">
                {new Date(account.created_at).toLocaleDateString("it-IT")}
              </dd>
            </dl>
          </section>

          {/* Pseudonimo / Brand (per Esplora) */}
          <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
            <h2 className="text-lg font-semibold mb-2">
              🎭 Pseudonimo / Brand
            </h2>
            <p className="text-sm text-[var(--color-fg-muted)] mb-4">
              Il nome che compare come autore sulle card di{" "}
              <a href="/esplora" className="underline">
                Esplora
              </a>{" "}
              quando condividi personaggi, copertine o tavole. Se lasciato
              vuoto, verrà mostrato il prefisso della tua email.
            </p>
            <form onSubmit={handleSavePseudonym} className="flex gap-3">
              <input
                type="text"
                placeholder="Es. Rob Bonu · CreaToon · Mamma di Lollo"
                value={pseudonym}
                onChange={(e) => setPseudonym(e.target.value)}
                maxLength={80}
                className="flex-1 px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
              />
              <button
                type="submit"
                disabled={savingPseudonym || pseudonym === (account.pseudonym || "")}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded transition-colors disabled:opacity-50"
              >
                {savingPseudonym ? "..." : "💾 Salva"}
              </button>
            </form>
            {pseudMsg && (
              <p
                className={`text-sm mt-3 ${
                  pseudMsg.ok ? "text-green-400" : "text-red-400"
                }`}
              >
                {pseudMsg.msg}
              </p>
            )}
          </section>

          {/* Cambio password */}
          <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Cambio password</h2>
            <form onSubmit={handleChangePassword} className="flex gap-3">
              <input
                type="password"
                placeholder="Nuova password (min 8 caratteri)"
                value={newPwd}
                onChange={(e) => setNewPwd(e.target.value)}
                minLength={8}
                required
                className="flex-1 px-3 py-2 bg-[var(--color-bg)] border border-[var(--color-border)] rounded focus:outline-none focus:border-[var(--color-accent)]"
              />
              <button
                type="submit"
                disabled={changing || newPwd.length < 8}
                className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-5 py-2 rounded transition-colors disabled:opacity-50"
              >
                {changing ? "..." : "Salva"}
              </button>
            </form>
            {pwdMsg && (
              <p
                className={`text-sm mt-3 ${
                  pwdMsg.ok ? "text-green-400" : "text-red-400"
                }`}
              >
                {pwdMsg.msg}
              </p>
            )}
          </section>

          {/* Storico crediti */}
          <section className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">Storico crediti</h2>
            {history.length === 0 ? (
              <p className="text-[var(--color-fg-muted)] text-sm">
                Nessun movimento crediti.
              </p>
            ) : (
              <ul className="divide-y divide-[var(--color-border)] -mx-2">
                {history.map((e, i) => (
                  <li
                    key={i}
                    className="flex justify-between items-center px-2 py-2.5 text-sm"
                  >
                    <div className="min-w-0 flex-1">
                      <span className="font-medium">{e.operation}</span>
                      {e.reason && (
                        <span className="text-[var(--color-fg-muted)] ml-2 truncate">
                          — {e.reason}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0">
                      <span
                        className={
                          e.delta < 0
                            ? "text-red-400 font-medium"
                            : "text-green-400 font-medium"
                        }
                      >
                        {e.delta > 0 ? "+" : ""}
                        {e.delta}
                      </span>
                      <span className="text-[var(--color-fg-muted)] text-xs">
                        {new Date(e.occurred_at).toLocaleString("it-IT")}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
