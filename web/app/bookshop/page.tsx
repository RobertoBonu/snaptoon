"use client";

import { useEffect, useMemo, useState } from "react";
import { SiteShell } from "@/components/site";

interface UserCard {
  id: string;
  name: string;
  character_type: string;
  caption: string;
  author_display: string;
  progressive_number: number;
  image_url: string;
  category_id: string | null;
  category_label: string | null;
  category_macro: string | null;
  published_at: string | null;
}

interface WebtoonCard {
  id: string;
  title: string;
  subtitle: string;
  author_name: string;
  author_role: string;
  caption: string;
  cover_url: string;
  read_url: string;
  panels_count: number;
  published_at: string | null;
  category_id: string | null;
  category_label: string | null;
  category_macro: string | null;
}

interface Category {
  id: string;
  slug: string;
  label: string;
  description: string;
}

interface MacroGroup {
  macro: string;
  label: string;
  categories: Category[];
}

interface CategoriesData {
  macros: MacroGroup[];
}

const MACRO_LABELS: Record<string, string> = {
  kids: "KIDS",
  young: "YOUNG",
  kidult: "KIDULT",
};
const MACRO_ORDER = ["kids", "young", "kidult"];

type MacroFilter = "all" | "kids" | "young" | "kidult";

export default function BookshopPage() {
  const [webtoons, setWebtoons] = useState<WebtoonCard[] | null>(null);
  const [userCards, setUserCards] = useState<UserCard[] | null>(null);
  const [categories, setCategories] = useState<CategoriesData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [macroFilter, setMacroFilter] = useState<MacroFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("");

  useEffect(() => {
    fetch("/api/webtoons?limit=120")
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<{ webtoons: WebtoonCard[] }>;
      })
      .then((d) => setWebtoons(d.webtoons))
      .catch((e) =>
        setError(e instanceof Error ? e.message : String(e)),
      );

    fetch("/api/bookshop/cards?limit=120")
      .then(async (r) => (r.ok ? r.json() : null))
      .then((d: { cards: UserCard[] } | null) => {
        if (d) setUserCards(d.cards);
        else setUserCards([]);
      })
      .catch(() => setUserCards([]));

    fetch("/api/bookshop/categories")
      .then(async (r) => (r.ok ? r.json() : null))
      .then((d: CategoriesData | null) => setCategories(d))
      .catch(() => {});
  }, []);

  // Filtro figurine
  const filteredCards = useMemo(() => {
    if (!userCards) return null;
    let list = userCards;
    if (macroFilter !== "all")
      list = list.filter((c) => c.category_macro === macroFilter);
    if (categoryFilter)
      list = list.filter((c) => c.category_id === categoryFilter);
    return list;
  }, [userCards, macroFilter, categoryFilter]);

  // Filtro
  const filtered = useMemo(() => {
    if (!webtoons) return null;
    let list = webtoons;
    if (macroFilter !== "all")
      list = list.filter((w) => w.category_macro === macroFilter);
    if (categoryFilter)
      list = list.filter((w) => w.category_id === categoryFilter);
    return list;
  }, [webtoons, macroFilter, categoryFilter]);

  // Raggruppamento per macro (mostrato se macroFilter === "all")
  const byMacro = useMemo(() => {
    if (!filtered) return null;
    const g: Record<string, WebtoonCard[]> = {
      kids: [],
      young: [],
      kidult: [],
      _uncategorized: [],
    };
    for (const w of filtered) {
      const m = w.category_macro || "_uncategorized";
      (g[m] ||= []).push(w);
    }
    return g;
  }, [filtered]);

  // Categorie disponibili per il filtro (filtrate su macroFilter)
  const availableCategories = useMemo(() => {
    if (!categories) return [];
    if (macroFilter === "all") {
      return categories.macros.flatMap((m) => m.categories);
    }
    const g = categories.macros.find((m) => m.macro === macroFilter);
    return g ? g.categories : [];
  }, [categories, macroFilter]);

  return (
    <SiteShell active="/bookshop">
      {/* Hero */}
      <section
        className="section"
        style={{
          paddingTop: "100px",
          paddingBottom: "40px",
          textAlign: "center",
        }}
      >
        <div className="lp-container">
          <h1
            style={{
              fontSize: "clamp(1.75rem, 6vw, 3.75rem)",
              fontWeight: 800,
              color: "#F1F5F9",
              lineHeight: 1.1,
              letterSpacing: "-0.03em",
              marginBottom: "20px",
            }}
          >
            📚 BookShop SnapToon
          </h1>
          <p
            style={{
              fontSize: "1.125rem",
              color: "#94A3B8",
              lineHeight: 1.6,
              maxWidth: "720px",
              margin: "0 auto",
            }}
          >
            La libreria dei WebToon creati dalla community. Storie in stile
            fumetto verticale, tutte gratuite, tutte generate su SnapToon.
          </p>
        </div>
      </section>

      {/* Filtri */}
      <section style={{ paddingBottom: "32px" }}>
        <div
          className="lp-container"
          style={{
            display: "flex",
            gap: "12px",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {(["all", ...MACRO_ORDER] as MacroFilter[]).map((m) => (
              <button
                key={m}
                onClick={() => {
                  setMacroFilter(m);
                  setCategoryFilter("");
                }}
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  padding: "7px 14px",
                  borderRadius: 100,
                  cursor: "pointer",
                  border:
                    macroFilter === m
                      ? "1px solid #F59E0B"
                      : "1px solid #2D3748",
                  background:
                    macroFilter === m
                      ? "rgba(245,158,11,0.12)"
                      : "transparent",
                  color: macroFilter === m ? "#F59E0B" : "#94A3B8",
                }}
              >
                {m === "all" ? "Tutti" : MACRO_LABELS[m]}
              </button>
            ))}
          </div>

          {availableCategories.length > 0 && (
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              style={{
                fontSize: "13px",
                padding: "7px 12px",
                borderRadius: 100,
                background: "#0F1420",
                border: "1px solid #2D3748",
                color: "#F1F5F9",
              }}
            >
              <option value="">Tutte le categorie</option>
              {availableCategories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          )}
        </div>
      </section>

      {/* Contenuto */}
      <section style={{ paddingBottom: "80px" }}>
        <div className="lp-container">
          {error && (
            <p
              style={{
                color: "#FCA5A5",
                textAlign: "center",
                padding: "40px 0",
              }}
            >
              Errore caricamento: {error}
            </p>
          )}

          {!error && filtered === null && (
            <p
              style={{
                color: "#64748B",
                textAlign: "center",
                padding: "40px 0",
              }}
            >
              Caricamento webtoon...
            </p>
          )}

          {!error && filtered !== null && filtered.length === 0 && (
            <div
              style={{
                background: "#161B26",
                border: "1px solid #1E2436",
                borderRadius: 16,
                padding: "60px 24px",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 48, marginBottom: 12, opacity: 0.4 }}>
                📭
              </div>
              <p style={{ color: "#94A3B8", fontSize: 14, marginBottom: 20 }}>
                {macroFilter === "all" && !categoryFilter
                  ? "Nessun webtoon pubblicato ancora. Sii il primo!"
                  : "Nessun webtoon in questo filtro."}
              </p>
              <a
                href="/login"
                className="btn btn-primary"
                style={{ padding: "10px 20px", fontSize: 13 }}
              >
                Crea il tuo webtoon →
              </a>
            </div>
          )}

          {/* Se macroFilter === all, raggruppa per macro; altrimenti griglia
              piatta */}
          {!error && filtered && filtered.length > 0 && byMacro && (
            <>
              {macroFilter === "all" ? (
                MACRO_ORDER.filter((m) => byMacro[m] && byMacro[m].length > 0).map((m) => (
                  <div key={m} style={{ marginBottom: 40 }}>
                    <h2
                      style={{
                        fontSize: "1.5rem",
                        fontWeight: 700,
                        color: "#F1F5F9",
                        marginBottom: 16,
                        display: "flex",
                        alignItems: "center",
                        gap: 10,
                      }}
                    >
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          letterSpacing: "0.12em",
                          background: "rgba(245,158,11,0.12)",
                          border: "1px solid rgba(245,158,11,0.3)",
                          color: "#F59E0B",
                          padding: "3px 10px",
                          borderRadius: 100,
                        }}
                      >
                        {MACRO_LABELS[m]}
                      </span>
                      <span
                        style={{
                          fontSize: 13,
                          color: "#64748B",
                          fontWeight: 400,
                        }}
                      >
                        {byMacro[m].length} webtoon
                        {byMacro[m].length !== 1 ? "" : ""}
                      </span>
                    </h2>
                    <GridWebtoons items={byMacro[m]} />
                  </div>
                ))
              ) : (
                <GridWebtoons items={filtered} />
              )}
              {/* uncategorized in fondo se ci sono */}
              {macroFilter === "all" &&
                byMacro._uncategorized &&
                byMacro._uncategorized.length > 0 && (
                  <div style={{ marginBottom: 40 }}>
                    <h2
                      style={{
                        fontSize: "1.25rem",
                        fontWeight: 700,
                        color: "#94A3B8",
                        marginBottom: 16,
                      }}
                    >
                      Senza categoria
                      <span
                        style={{
                          fontSize: 13,
                          color: "#64748B",
                          fontWeight: 400,
                          marginLeft: 10,
                        }}
                      >
                        {byMacro._uncategorized.length} webtoon
                      </span>
                    </h2>
                    <GridWebtoons items={byMacro._uncategorized} />
                  </div>
                )}
            </>
          )}
        </div>
      </section>

      {/* Sezione Figurine */}
      {filteredCards && filteredCards.length > 0 && (
        <section
          style={{
            paddingTop: 20,
            paddingBottom: 80,
            borderTop: "1px solid #1E2436",
            background: "linear-gradient(180deg, rgba(245,158,11,0.03) 0%, rgba(13,16,23,0) 100%)",
          }}
        >
          <div className="lp-container">
            <div style={{ marginBottom: 24 }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  background: "rgba(245,158,11,0.12)",
                  border: "1px solid rgba(245,158,11,0.3)",
                  padding: "4px 10px",
                  borderRadius: 100,
                  color: "#F59E0B",
                  fontSize: 12,
                  fontWeight: 700,
                  marginBottom: 12,
                }}
              >
                🎴 Collezionabili
              </div>
              <h2
                style={{
                  fontSize: "1.5rem",
                  fontWeight: 700,
                  color: "#F1F5F9",
                  marginBottom: 6,
                }}
              >
                Figurine della community
              </h2>
              <p
                style={{
                  fontSize: "0.95rem",
                  color: "#94A3B8",
                  maxWidth: 620,
                }}
              >
                Card 9:16 con banner nome, stelline di apprezzamento e numero
                progressivo. Ogni card è unica — il numero è progressivo su
                tutte le figurine SnapToon.
              </p>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                gap: 20,
              }}
            >
              {filteredCards.map((c) => (
                <div
                  key={c.id}
                  className="lift"
                  style={{
                    background: "#0F1420",
                    border: "1px solid #1E2436",
                    borderRadius: 14,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      position: "relative",
                      aspectRatio: "9 / 16",
                      background: "#0D1017",
                    }}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={`${c.image_url}?variant=thumb`}
                      alt={c.name}
                      loading="lazy"
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                        display: "block",
                      }}
                    />
                    <span
                      style={{
                        position: "absolute",
                        top: 8,
                        right: 8,
                        background: "rgba(13,16,23,0.85)",
                        border: "1px solid #1E2436",
                        color: "#CBD5E1",
                        fontSize: 10,
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: 6,
                        fontFamily: "monospace",
                      }}
                    >
                      #{String(c.progressive_number).padStart(4, "0")}
                    </span>
                    {c.category_label && (
                      <span
                        style={{
                          position: "absolute",
                          top: 8,
                          left: 8,
                          background: "rgba(13,16,23,0.85)",
                          border: "1px solid rgba(124,58,237,0.5)",
                          color: "#A78BFA",
                          fontSize: 9,
                          fontWeight: 700,
                          padding: "2px 6px",
                          borderRadius: 100,
                          textTransform: "uppercase",
                          letterSpacing: "0.06em",
                        }}
                      >
                        {c.category_label}
                      </span>
                    )}
                  </div>
                  <div style={{ padding: 10 }}>
                    <div
                      style={{
                        fontSize: 13,
                        fontWeight: 700,
                        color: "#F1F5F9",
                        lineHeight: 1.3,
                        marginBottom: 2,
                      }}
                    >
                      {c.name}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: "#94A3B8",
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                      }}
                    >
                      {c.character_type}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: "#64748B",
                        marginTop: 4,
                      }}
                    >
                      di {c.author_display}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}
    </SiteShell>
  );
}

function GridWebtoons({ items }: { items: WebtoonCard[] }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
        gap: 24,
      }}
    >
      {items.map((w) => (
        <a
          key={w.id}
          href={w.read_url}
          className="product-card"
          style={{ textDecoration: "none" }}
        >
          <div
            style={{
              position: "relative",
              aspectRatio: "2 / 3",
              background: "#0D1017",
              overflow: "hidden",
              borderBottom: "1px solid #1E2436",
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={w.cover_url}
              alt={w.title}
              loading="lazy"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                display: "block",
              }}
            />
            {w.category_label && (
              <span
                style={{
                  position: "absolute",
                  top: 10,
                  left: 10,
                  background: "rgba(13,16,23,0.85)",
                  border: "1px solid rgba(124,58,237,0.5)",
                  color: "#A78BFA",
                  fontSize: 10,
                  fontWeight: 700,
                  padding: "3px 8px",
                  borderRadius: 100,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                }}
              >
                {w.category_label}
              </span>
            )}
            <span
              style={{
                position: "absolute",
                bottom: 10,
                right: 10,
                background: "rgba(13,16,23,0.85)",
                border: "1px solid #1E2436",
                color: "#CBD5E1",
                fontSize: 11,
                fontWeight: 600,
                padding: "3px 8px",
                borderRadius: 100,
              }}
            >
              {w.panels_count} vignette
            </span>
          </div>
          <div
            style={{
              padding: 16,
              display: "flex",
              flexDirection: "column",
              flex: 1,
            }}
          >
            <div
              style={{
                fontSize: 15,
                fontWeight: 700,
                color: "#F1F5F9",
                lineHeight: 1.3,
                marginBottom: 6,
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {w.title}
            </div>
            <div
              style={{
                fontSize: 13,
                color: "#94A3B8",
                marginBottom: 14,
                display: "flex",
                alignItems: "center",
                gap: 6,
                flexWrap: "wrap",
              }}
            >
              {w.author_name}
              {w.author_role && (
                <span
                  style={{
                    fontSize: 10,
                    color: "#A78BFA",
                    border: "1px solid rgba(124,58,237,0.4)",
                    borderRadius: 100,
                    padding: "1px 6px",
                  }}
                >
                  {w.author_role}
                </span>
              )}
            </div>
            <div style={{ marginTop: "auto" }}>
              <span
                className="btn btn-primary"
                style={{ padding: "6px 12px", fontSize: 12, width: "100%" }}
              >
                Leggi →
              </span>
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}
