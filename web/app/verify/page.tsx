"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

type State =
  | { kind: "loading" }
  | { kind: "success"; email: string }
  | { kind: "error"; message: string };

function VerifyInner() {
  const params = useSearchParams();
  const token = params?.get("token") || "";

  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!token) {
      setState({ kind: "error", message: "Link non valido: token mancante." });
      return;
    }
    (async () => {
      try {
        const res = await fetch("/api/auth/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          let msg = `Errore ${res.status} durante la verifica.`;
          if (typeof data?.detail === "string") msg = data.detail;
          else if (data?.detail?.message) msg = data.detail.message;
          setState({ kind: "error", message: msg });
          return;
        }
        setState({ kind: "success", email: data.email || "" });
      } catch {
        setState({
          kind: "error",
          message: "Errore di connessione. Riprova più tardi.",
        });
      }
    })();
  }, [token]);

  return (
    <main className="min-h-screen flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md text-center">
        <Link href="/" className="block mb-8">
          <div className="text-4xl mb-1">📚</div>
          <h1 className="text-2xl font-bold text-[var(--color-accent)]">
            SnapToon
          </h1>
        </Link>

        {state.kind === "loading" && (
          <>
            <div className="text-6xl mb-4">⏳</div>
            <p className="text-[var(--color-fg-muted)]">
              Sto verificando il tuo indirizzo...
            </p>
          </>
        )}

        {state.kind === "success" && (
          <>
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-3xl font-bold mb-4">Il tuo account è pronto!</h2>
            <p className="text-[var(--color-fg-muted)] mb-2">
              Abbiamo verificato{" "}
              <b className="text-[var(--color-fg)]">
                {state.email || "il tuo indirizzo email"}
              </b>
              .
            </p>
            <p className="text-[var(--color-fg-muted)] mb-6">
              Ti abbiamo appena mandato una seconda email di benvenuto.
              Ora puoi fare login e iniziare a creare!
            </p>
            <Link
              href="/login"
              className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-bold px-8 py-3 rounded-lg text-lg"
            >
              Vai al login →
            </Link>
          </>
        )}

        {state.kind === "error" && (
          <>
            <div className="text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold mb-4">Verifica non riuscita</h2>
            <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-6">
              {state.message}
            </p>
            <div className="flex flex-col gap-3">
              <Link
                href="/login"
                className="inline-block bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold px-6 py-2.5 rounded-lg"
              >
                Vai al login
              </Link>
              <Link
                href="/register"
                className="text-sm text-[var(--color-fg-muted)] hover:text-[var(--color-fg)]"
              >
                Registrati di nuovo
              </Link>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

export default function VerifyPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          Caricamento...
        </div>
      }
    >
      <VerifyInner />
    </Suspense>
  );
}
