import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="it">
      <head>
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin=""
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
