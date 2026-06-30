import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

// next/font/google ottimizza il caricamento del font (preload, no FOIT/FOUT)
// e — soprattutto — non aggiunge <link> manuali al <head>, evitando l'errore
// di hydration mismatch causato dagli script che Replit Dev inietta nello
// stesso head dopo il render del server.
const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SnapToon — Dall'idea al fumetto, in uno snap.",
  description:
    "Crea fumetti illustrati con l'AI in pochi minuti. Modalità KIDS per libretti per bambini.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="it" className={inter.variable} suppressHydrationWarning>
      <body className={inter.className}>{children}</body>
    </html>
  );
}
