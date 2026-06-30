"use client";

import { useMemo, useState } from "react";
import { SiteShell, MediaFrame } from "@/components/site";
import { books, formatPrice, type Book, type BookCategory } from "@/data/bookshop";

type CategoryFilter = "Tutti" | BookCategory;
type PriceFilter = "Tutti" | "Gratuiti" | "A pagamento";
type SortKey = "recenti" | "venduti" | "prezzo";

function ProductCard({ book, onBuy }: { book: Book; onBuy: () => void }) {
  return (
    <div className="product-card">
      <MediaFrame src={book.cover} label={book.title} aspect="2 / 3" rounded={0} />
      <div style={{ padding: "16px", display: "flex", flexDirection: "column", flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <span style={{ fontSize: "11px", color: "#64748B", textTransform: "uppercase", letterSpacing: "0.04em" }}>{book.category}</span>
          {book.bestseller && <span style={{ fontSize: "10px", color: "#F59E0B", border: "1px solid rgba(245,158,11,0.3)", borderRadius: "100px", padding: "1px 8px" }}>Più venduto</span>}
        </div>
        <div style={{ fontSize: "15px", fontWeight: 700, color: "#F1F5F9", lineHeight: 1.3, marginBottom: "6px" }}>{book.title}</div>
        <div style={{ fontSize: "13px", color: "#94A3B8", marginBottom: "14px", display: "flex", alignItems: "center", gap: "6px" }}>
          {book.author}
          {book.isPublisher && <span style={{ fontSize: "10px", color: "#7C3AED", border: "1px solid rgba(124,58,237,0.4)", borderRadius: "100px", padding: "1px 6px" }}>Editore</span>}
        </div>
        <div style={{ marginTop: "auto", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
          <span style={{ fontSize: "16px", fontWeight: 700, color: book.price === 0 ? "#10B981" : "#F1F5F9" }}>{formatPrice(book.price)}</span>
          <div style={{ display: "flex", gap: "6px" }}>
            <button className="btn btn-ghost" style={{ padding: "6px 10px", fontSize: "12px" }} onClick={onBuy}>Anteprima</button>
            <button className="btn btn-primary" style={{ padding: "6px 12px", fontSize: "12px" }} onClick={onBuy}>Acquista</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Pill({ active, children, onClick }: { active: boolean; children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        fontSize: "13px", fontWeight: 600, padding: "7px 14px", borderRadius: "100px", cursor: "pointer",
        border: active ? "1px solid #F59E0B" : "1px solid #2D3748",
        background: active ? "rgba(245,158,11,0.12)" : "transparent",
        color: active ? "#F59E0B" : "#94A3B8", transition: "all 0.2s",
      }}
    >
      {children}
    </button>
  );
}

function ThemedSection({ title, caption, items, onBuy }: { title: string; caption: string; items: Book[]; onBuy: () => void }) {
  return (
    <section className="section" style={{ paddingTop: "40px", paddingBottom: "20px" }}>
      <div className="lp-container">
        <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#F1F5F9", marginBottom: "6px" }}>{title}</h2>
        <p style={{ fontSize: "0.95rem", color: "#94A3B8", marginBottom: "24px" }}>{caption}</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "24px" }}>
          {items.slice(0, 3).map((b) => <ProductCard key={b.id} book={b} onBuy={onBuy} />)}
        </div>
      </div>
    </section>
  );
}

export default function BookshopPage() {
  const [category, setCategory] = useState<CategoryFilter>("Tutti");
  const [price, setPrice] = useState<PriceFilter>("Tutti");
  const [sort, setSort] = useState<SortKey>("recenti");
  const [toastOpen, setToastOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const filtered = useMemo(() => {
    let list = [...books];
    if (category !== "Tutti") list = list.filter((b) => b.category === category);
    if (price === "Gratuiti") list = list.filter((b) => b.price === 0);
    if (price === "A pagamento") list = list.filter((b) => b.price > 0);
    if (sort === "recenti") list.sort((a, b) => b.publishedAt - a.publishedAt);
    if (sort === "venduti") list.sort((a, b) => Number(b.bestseller || 0) - Number(a.bestseller || 0));
    if (sort === "prezzo") list.sort((a, b) => a.price - b.price);
    return list;
  }, [category, price, sort]);

  const openToast = () => { setSubscribed(false); setToastOpen(true); };

  return (
    <SiteShell active="/bookshop">
      {/* Hero */}
      <section className="section" style={{ paddingTop: "100px", paddingBottom: "40px", textAlign: "center" }}>
        <div className="lp-container">
          <h1 style={{ fontSize: "clamp(2.5rem, 5vw, 3.75rem)", fontWeight: 800, color: "#F1F5F9", lineHeight: 1.1, letterSpacing: "-0.03em", marginBottom: "20px" }}>Bookshop SnapToon</h1>
          <p style={{ fontSize: "1.125rem", color: "#94A3B8", lineHeight: 1.6, maxWidth: "720px", margin: "0 auto" }}>
            Fumetti, graphic novel, libri illustrati e libretti KIDS firmati da autori e editori indipendenti. Tutto creato con SnapToon.
          </p>
        </div>
      </section>

      {/* Filtri sticky */}
      <div style={{ position: "sticky", top: "72px", zIndex: 50, background: "rgba(13,16,23,0.92)", backdropFilter: "blur(12px)", borderTop: "1px solid #1E2436", borderBottom: "1px solid #1E2436", padding: "16px 0" }}>
        <div className="lp-container" style={{ display: "flex", flexWrap: "wrap", gap: "20px", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
            {(["Tutti", "Fumetti", "Graphic Novel", "Libri illustrati", "KIDSToons"] as CategoryFilter[]).map((c) => (
              <Pill key={c} active={category === c} onClick={() => setCategory(c)}>{c}</Pill>
            ))}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "16px", alignItems: "center" }}>
            <div style={{ display: "flex", gap: "8px" }}>
              {(["Tutti", "Gratuiti", "A pagamento"] as PriceFilter[]).map((p) => (
                <Pill key={p} active={price === p} onClick={() => setPrice(p)}>{p}</Pill>
              ))}
            </div>
            <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)} style={{ background: "#161B26", color: "#E2E8F0", border: "1px solid #2D3748", borderRadius: "8px", padding: "8px 12px", fontSize: "13px", cursor: "pointer" }}>
              <option value="recenti">Più recenti</option>
              <option value="venduti">Più venduti</option>
              <option value="prezzo">Prezzo crescente</option>
            </select>
          </div>
        </div>
      </div>

      {/* Grid prodotti */}
      <section className="section" style={{ paddingTop: "40px", paddingBottom: "20px" }}>
        <div className="lp-container">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "24px" }}>
            {filtered.map((b) => <ProductCard key={b.id} book={b} onBuy={openToast} />)}
          </div>
          {filtered.length === 0 && <p style={{ color: "#64748B", textAlign: "center", padding: "40px 0" }}>Nessun risultato con questi filtri.</p>}
        </div>
      </section>

      {/* Sezioni tematiche */}
      <ThemedSection title="⭐ KIDSToons — Per i più piccoli" caption="Libretti illustrati 5-8 anni, formato 16 pagine + copertina" items={books.filter((b) => b.category === "KIDSToons")} onBuy={openToast} />
      <ThemedSection title="📕 Graphic Novel" caption="Storie lunghe, narrazione adulta, stile cinematografico" items={books.filter((b) => b.category === "Graphic Novel")} onBuy={openToast} />
      <ThemedSection title="📚 Fumetti" caption="Episodi 6-16 pagine, perfetti per il binge reading" items={books.filter((b) => b.category === "Fumetti")} onBuy={openToast} />
      <ThemedSection title="📖 Libri illustrati" caption="Tradizione picture-book con il twist dell'AI" items={books.filter((b) => b.category === "Libri illustrati")} onBuy={openToast} />

      {/* Callout editori */}
      <section className="section" style={{ paddingTop: "60px", paddingBottom: "40px" }}>
        <div className="lp-container">
          <div style={{ background: "#0A0E17", border: "1px solid #1E2436", borderRadius: "20px", padding: "40px" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: 700, color: "#F1F5F9", marginBottom: "12px" }}>Sei un editore? Vendi sul Bookshop</h2>
            <p style={{ fontSize: "1.0625rem", color: "#94A3B8", lineHeight: 1.7, marginBottom: "24px", maxWidth: "760px" }}>
              Con il piano Editore pubblichi senza commissioni fisse, ricevi report dettagliati sulle vendite e mantieni il 100% del ricavato. SnapToon resta in background.
            </p>
            <a href="/abbonamenti#editore" className="btn btn-primary" style={{ padding: "12px 22px" }}>Diventa editore →</a>
          </div>
        </div>
      </section>

      {/* CTA finale */}
      <section className="section" style={{ paddingTop: "20px", paddingBottom: "100px" }}>
        <div className="lp-container" style={{ textAlign: "center" }}>
          <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 800, color: "#F1F5F9", marginBottom: "20px" }}>Hai creato qualcosa di bello? Mettilo in vetrina.</h2>
          <a href="mailto:info@snaptoon.art" className="btn btn-secondary" style={{ padding: "14px 28px", fontSize: "15px" }}>Pubblica un&apos;opera →</a>
        </div>
      </section>

      {/* Toast lancio */}
      {toastOpen && (
        <div style={{ position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%)", zIndex: 200, width: "min(520px, calc(100% - 32px))", background: "#161B26", border: "1px solid #2D3748", borderRadius: "16px", boxShadow: "0 24px 64px rgba(0,0,0,0.5)", padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: "15px", fontWeight: 700, color: "#F1F5F9", marginBottom: "4px" }}>Lancio Bookshop in arrivo 🚀</div>
              {!subscribed ? (
                <>
                  <p style={{ fontSize: "13px", color: "#94A3B8", marginBottom: "12px" }}>Iscriviti alla newsletter per essere avvisato.</p>
                  <form
                    onSubmit={(e) => { e.preventDefault(); if (email.trim()) setSubscribed(true); }}
                    style={{ display: "flex", gap: "8px" }}
                  >
                    <input
                      type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="La tua email"
                      style={{ flex: 1, background: "#0D1017", border: "1px solid #2D3748", borderRadius: "8px", padding: "10px 12px", color: "#E2E8F0", fontSize: "13px" }}
                    />
                    <button type="submit" className="btn btn-primary" style={{ padding: "10px 16px", fontSize: "13px" }}>Avvisami</button>
                  </form>
                </>
              ) : (
                <p style={{ fontSize: "13px", color: "#10B981", marginTop: "4px" }}>Grazie! Ti avviseremo al lancio. 🎉</p>
              )}
            </div>
            <button onClick={() => setToastOpen(false)} style={{ background: "transparent", border: "none", color: "#64748B", fontSize: "20px", cursor: "pointer", lineHeight: 1 }} aria-label="Chiudi">×</button>
          </div>
        </div>
      )}
    </SiteShell>
  );
}
