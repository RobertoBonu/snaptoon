export type BookCategory =
  | "Fumetti"
  | "Graphic Novel"
  | "Libri illustrati"
  | "KIDSToons";

export interface Book {
  id: string;
  title: string;
  author: string;
  isPublisher?: boolean;
  category: BookCategory;
  /** Prezzo in euro. 0 = gratis. */
  price: number;
  /** Path immagine cover (2:3) in web/public/images/bookshop/. */
  cover: string;
  bestseller?: boolean;
  /** Ordine di pubblicazione (più alto = più recente). */
  publishedAt: number;
}

export const CATEGORIES: BookCategory[] = [
  "Fumetti",
  "Graphic Novel",
  "Libri illustrati",
  "KIDSToons",
];

export const books: Book[] = [
  // KIDSToons
  { id: "k1", title: "Il Drago che aveva paura del buio", author: "Studio Lumino", isPublisher: true, category: "KIDSToons", price: 0, cover: "/images/bookshop/kids-1.png", publishedAt: 16 },
  { id: "k2", title: "Mia e la Balena di Cristallo", author: "Elena Bossi", category: "KIDSToons", price: 3.99, cover: "/images/bookshop/kids-2.png", bestseller: true, publishedAt: 12 },
  { id: "k3", title: "Le avventure di Bun il Robot", author: "Marco Vitali", category: "KIDSToons", price: 2.99, cover: "/images/bookshop/kids-3.png", publishedAt: 9 },
  { id: "k4", title: "Il bosco dei colori", author: "Studio Lumino", isPublisher: true, category: "KIDSToons", price: 0, cover: "/images/bookshop/kids-4.png", publishedAt: 5 },

  // Graphic Novel
  { id: "g1", title: "Neo-Roma 2099", author: "Davide Conti", category: "Graphic Novel", price: 9.99, cover: "/images/bookshop/gn-1.png", bestseller: true, publishedAt: 15 },
  { id: "g2", title: "L'ultima stazione", author: "Edizioni Aurora", isPublisher: true, category: "Graphic Novel", price: 7.99, cover: "/images/bookshop/gn-2.png", publishedAt: 11 },
  { id: "g3", title: "Cenere e Neon", author: "Sara Lombardi", category: "Graphic Novel", price: 8.49, cover: "/images/bookshop/gn-3.png", publishedAt: 7 },
  { id: "g4", title: "Il Cartografo dei Sogni", author: "Edizioni Aurora", isPublisher: true, category: "Graphic Novel", price: 10.99, cover: "/images/bookshop/gn-4.png", publishedAt: 3 },

  // Fumetti
  { id: "f1", title: "Pixel Squad — Ep.1", author: "Luca Ferri", category: "Fumetti", price: 1.99, cover: "/images/bookshop/fumetto-1.png", bestseller: true, publishedAt: 14 },
  { id: "f2", title: "Detective Otto — Caso 03", author: "Giulia Marenco", category: "Fumetti", price: 2.49, cover: "/images/bookshop/fumetto-2.png", publishedAt: 10 },
  { id: "f3", title: "Aria, pilota stellare", author: "Collettivo Nova", isPublisher: true, category: "Fumetti", price: 0, cover: "/images/bookshop/fumetto-3.png", publishedAt: 6 },
  { id: "f4", title: "Kael il Mercenario", author: "Luca Ferri", category: "Fumetti", price: 1.99, cover: "/images/bookshop/fumetto-4.png", publishedAt: 2 },

  // Libri illustrati
  { id: "l1", title: "Notturno per pianoforte", author: "Edizioni Aurora", isPublisher: true, category: "Libri illustrati", price: 12.99, cover: "/images/bookshop/illustrato-1.png", publishedAt: 13 },
  { id: "l2", title: "Atlante delle creature gentili", author: "Elena Bossi", category: "Libri illustrati", price: 6.99, cover: "/images/bookshop/illustrato-2.png", bestseller: true, publishedAt: 8 },
  { id: "l3", title: "La città sottosopra", author: "Marco Vitali", category: "Libri illustrati", price: 5.99, cover: "/images/bookshop/illustrato-3.png", publishedAt: 4 },
  { id: "l4", title: "Stagioni", author: "Collettivo Nova", isPublisher: true, category: "Libri illustrati", price: 0, cover: "/images/bookshop/illustrato-4.png", publishedAt: 1 },
];

export function formatPrice(price: number): string {
  if (price === 0) return "Gratis";
  return `€${price.toFixed(2).replace(".", ",")}`;
}
