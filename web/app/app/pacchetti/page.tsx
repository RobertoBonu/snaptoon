"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

interface ExtraPackageOption {
  package_type: string;
  quota_type: string;
  quota_type_label: string;
  quantity: number;
  quality: string | null;
  price_eur: number;
  unit_price_eur: number;
}

interface PrintPricingOut {
  copies: number;
  price_eur: number;
  unit_price_eur: number;
}

interface ExportPricingOut {
  format_type: string;
  label: string;
  price_eur: number;
  description: string;
}

interface Catalog {
  extra_packages: Record<string, ExtraPackageOption[]>;
  print_pricing: PrintPricingOut[];
  export_pricing: ExportPricingOut[];
}

interface QuotaStatus {
  quota_type: string;
  quota_type_label: string;
  month_available: number;
  month_max: number;
  extra_available: number;
}

interface MyQuotas {
  plan: string;
  plan_label: string;
  quotas: QuotaStatus[];
}

const QUOTA_EMOJI: Record<string, string> = {
  libretti_kids: "📕",
  progetti_pro: "📗",
  cover: "🖼️",
  card: "🎴",
};

const QUOTA_ORDER = ["libretti_kids", "progetti_pro", "cover", "card"];

const QUALITY_BADGE: Record<string, { bg: string; color: string; label: string }> = {
  medium: { bg: "rgba(100,116,139,0.15)", color: "#94A3B8", label: "Medium" },
  high: { bg: "rgba(245,158,11,0.15)", color: "#FDE047", label: "High ⚡" },
};

function packageTitle(o: ExtraPackageOption): string {
  const label = o.quota_type_label;
  const q = o.quantity;
  return q === 1 ? `+1 ${label}` : `${q} ${label}`;
}

export default function PacchettiPage() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [quotas, setQuotas] = useState<MyQuotas | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [buying, setBuying] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [c, q] = await Promise.all([
        apiFetch<Catalog>("/api/packages/catalog"),
        apiFetch<MyQuotas>("/api/packages/my-quotas"),
      ]);
      setCatalog(c);
      setQuotas(q);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function buy(packageType: string) {
    if (buying) return;
    setBuying(packageType);
    setError(null);
    setSuccess(null);
    try {
      await apiFetch("/api/packages/buy", {
        method: "POST",
        body: JSON.stringify({
          package_type: packageType,
          mock_stripe_token: "mock_" + Math.random().toString(36).slice(2),
        }),
      });
      setSuccess("Pacchetto acquistato! Le quote sono state aggiunte.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBuying(null);
    }
  }

  if (!catalog || !quotas) {
    return (
      <div className="p-8">
        <p className="text-[var(--color-fg-muted)]">Caricamento...</p>
        {error && <p className="text-red-400 mt-2">{error}</p>}
      </div>
    );
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-1">📦 Pacchetti Extra</h1>
      <p className="text-sm text-[var(--color-fg-muted)] mb-6">
        Aggiungi quote extra al tuo piano <b>{quotas.plan_label}</b>. Le quote extra <b>non scadono</b>.
      </p>

      {error && (
        <p className="text-red-400 text-sm bg-red-950/30 border border-red-900/50 rounded px-3 py-2 mb-4">
          {error}
        </p>
      )}
      {success && (
        <p className="text-green-400 text-sm bg-green-950/30 border border-green-900/50 rounded px-3 py-2 mb-4">
          {success}
        </p>
      )}

      {/* Situazione quote correnti */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Le tue quote</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {QUOTA_ORDER.map((qt) => {
            const q = quotas.quotas.find((x) => x.quota_type === qt);
            if (!q) return null;
            return (
              <div
                key={qt}
                className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4"
              >
                <div className="text-2xl mb-1">{QUOTA_EMOJI[qt]}</div>
                <div className="font-medium text-sm mb-2">{q.quota_type_label}</div>
                <div className="text-xs text-[var(--color-fg-muted)]">
                  Mensile: <span className="text-[var(--color-fg)] font-semibold">{q.month_available}/{q.month_max}</span>
                </div>
                <div className="text-xs text-[var(--color-fg-muted)]">
                  Extra: <span className="text-[var(--color-accent)] font-semibold">+{q.extra_available}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Pacchetti Extra per tipo */}
      {QUOTA_ORDER.map((qt) => {
        const options = catalog.extra_packages[qt] || [];
        if (options.length === 0) return null;
        return (
          <section key={qt} className="mb-8">
            <h2 className="text-lg font-semibold mb-3">
              {QUOTA_EMOJI[qt]} {options[0].quota_type_label}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {options.map((o) => {
                const isBusy = buying === o.package_type;
                const badge = o.quality ? QUALITY_BADGE[o.quality] : null;
                return (
                  <div
                    key={o.package_type}
                    className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4 flex flex-col"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="text-sm font-medium">{packageTitle(o)}</div>
                      {badge && (
                        <span
                          className="text-[10px] px-1.5 py-0.5 rounded font-bold"
                          style={{ background: badge.bg, color: badge.color }}
                        >
                          {badge.label}
                        </span>
                      )}
                    </div>
                    <div className="text-2xl text-[var(--color-accent)] font-bold mt-2">
                      €{o.price_eur.toFixed(2).replace(".", ",")}
                    </div>
                    {o.quantity > 1 && (
                      <div className="text-xs text-[var(--color-fg-muted)] mt-1 mb-3">
                        €{o.unit_price_eur.toFixed(2).replace(".", ",")}/cad
                      </div>
                    )}
                    <button
                      onClick={() => buy(o.package_type)}
                      disabled={isBusy}
                      className="mt-auto bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-bg)] font-semibold py-2 rounded text-sm disabled:opacity-40"
                    >
                      {isBusy ? "Acquisto..." : "Acquista"}
                    </button>
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}

      {/* Stampa fisica */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">🖨️ Stampa fisica</h2>
        <p className="text-xs text-[var(--color-fg-muted)] mb-3">
          Ordina copie stampate di un libretto o fumetto. Per 100+ copie contatta <a href="mailto:info@snaptoon.art" className="underline">info@snaptoon.art</a>
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {catalog.print_pricing.map((p) => (
            <div
              key={p.copies}
              className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4 text-center"
            >
              <div className="text-2xl font-bold">{p.copies}</div>
              <div className="text-xs text-[var(--color-fg-muted)] mb-2">copie</div>
              <div className="text-lg text-[var(--color-accent)] font-bold">
                €{p.price_eur.toFixed(0)}
              </div>
              <div className="text-xs text-[var(--color-fg-muted)]">
                €{p.unit_price_eur.toFixed(2).replace(".", ",")}/cad
              </div>
              <p className="text-xs text-[var(--color-fg-muted)] mt-3 italic">
                Ordina dal singolo progetto
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Export */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">📤 Esportazione professionale</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {catalog.export_pricing.map((e) => (
            <div
              key={e.format_type}
              className="bg-[var(--color-bg-elev)] border border-[var(--color-border)] rounded-xl p-4"
            >
              <div className="font-semibold">{e.label}</div>
              <div className="text-lg text-[var(--color-accent)] font-bold my-1">
                €{e.price_eur.toFixed(2).replace(".", ",")}
              </div>
              <p className="text-xs text-[var(--color-fg-muted)]">{e.description}</p>
              <p className="text-xs text-[var(--color-fg-muted)] mt-3 italic">
                Ordina dal singolo progetto
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
