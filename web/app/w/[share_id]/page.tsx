"use client";

import { use, useEffect, useState } from "react";

interface WebtoonPanel {
  page: number;
  panel: number;
  url: string;
}

interface WebtoonReader {
  id: string;
  title: string;
  subtitle: string;
  author_name: string;
  author_role: string;
  caption: string;
  cover_url: string;
  panels: WebtoonPanel[];
}

// Larghezza massima del lettore: standard WebToon (~800px), ottimizzato
// per lettura mobile scrollando dall'alto in basso.
const READER_MAX_W = 800;
const GUTTER = 24;

export default function WebtoonReaderPage({
  params,
}: {
  params: Promise<{ share_id: string }>;
}) {
  const { share_id } = use(params);
  const [data, setData] = useState<WebtoonReader | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    fetch(`/api/webtoons/${share_id}`)
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(
            res.status === 404
              ? "WebToon non trovato o non ancora pubblicato."
              : `Errore ${res.status}`,
          );
        }
        return res.json() as Promise<WebtoonReader>;
      })
      .then(setData)
      .catch((e) =>
        setError(e instanceof Error ? e.message : String(e)),
      );
  }, [share_id]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 240);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (error) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 24,
          background: "#0D1017",
          color: "#F1F5F9",
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: 480 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>📖</div>
          <h1 style={{ fontSize: 22, marginBottom: 8 }}>WebToon non trovato</h1>
          <p style={{ color: "#94A3B8", fontSize: 14, lineHeight: 1.6 }}>
            {error}
          </p>
          <a
            href="/esplora"
            style={{
              display: "inline-block",
              marginTop: 20,
              color: "#F59E0B",
              textDecoration: "none",
              fontWeight: 600,
              fontSize: 14,
            }}
          >
            ← Torna a Esplora
          </a>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0D1017",
          color: "#94A3B8",
        }}
      >
        Caricamento webtoon...
      </div>
    );
  }

  return (
    <div
      style={{
        background: "#0D1017",
        minHeight: "100vh",
        paddingBottom: 80,
      }}
    >
      {/* Sticky header che appare in scroll */}
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          background: "rgba(13, 16, 23, 0.9)",
          backdropFilter: "blur(12px)",
          borderBottom: scrolled ? "1px solid #1E2436" : "1px solid transparent",
          padding: "12px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
          transition: "border-color 0.2s",
        }}
      >
        <a
          href="/esplora"
          style={{
            color: "#94A3B8",
            fontSize: 13,
            textDecoration: "none",
            fontWeight: 500,
            flexShrink: 0,
          }}
        >
          ← Esplora
        </a>
        {scrolled && (
          <div
            style={{
              flex: 1,
              minWidth: 0,
              textAlign: "center",
              fontSize: 14,
              fontWeight: 700,
              color: "#F1F5F9",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {data.title}
          </div>
        )}
        <div style={{ width: 60, flexShrink: 0 }} />
      </header>

      {/* Contenitore centrato con larghezza fissa max */}
      <div
        style={{
          maxWidth: READER_MAX_W,
          margin: "0 auto",
          padding: "0 8px",
        }}
      >
        {/* Testata: cover + titolo */}
        <div style={{ padding: "24px 8px 16px" }}>
          <h1
            style={{
              fontSize: "clamp(1.5rem, 5vw, 2rem)",
              fontWeight: 800,
              color: "#F1F5F9",
              lineHeight: 1.15,
              margin: "0 0 6px 0",
              textAlign: "center",
            }}
          >
            {data.title}
          </h1>
          {data.subtitle && (
            <p
              style={{
                fontSize: 14,
                color: "#94A3B8",
                textAlign: "center",
                margin: "0 0 12px 0",
              }}
            >
              {data.subtitle}
            </p>
          )}
          <p
            style={{
              fontSize: 13,
              color: "#94A3B8",
              textAlign: "center",
              margin: 0,
            }}
          >
            di <strong style={{ color: "#F1F5F9" }}>{data.author_name}</strong>
            {data.author_role && (
              <span style={{ marginLeft: 8, color: "#7C3AED", fontSize: 12 }}>
                {data.author_role}
              </span>
            )}
          </p>
          {data.caption && (
            <p
              style={{
                fontSize: 14,
                color: "#CBD5E1",
                fontStyle: "italic",
                textAlign: "center",
                margin: "16px auto 0",
                maxWidth: 560,
                lineHeight: 1.5,
              }}
            >
              &quot;{data.caption}&quot;
            </p>
          )}
        </div>

        {/* Cover full-width */}
        <div style={{ marginBottom: GUTTER }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={data.cover_url}
            alt={`Copertina di ${data.title}`}
            style={{
              width: "100%",
              height: "auto",
              display: "block",
              borderRadius: 8,
            }}
            loading="eager"
          />
        </div>

        {/* Panels impilati */}
        {data.panels.map((p) => (
          <div
            key={`${p.page}-${p.panel}`}
            style={{ marginBottom: GUTTER }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={p.url}
              alt={`Vignetta pagina ${p.page} panel ${p.panel}`}
              style={{
                width: "100%",
                height: "auto",
                display: "block",
                borderRadius: 4,
              }}
              loading="lazy"
            />
          </div>
        ))}

        {/* Footer: firma + CTA */}
        <div
          style={{
            marginTop: 40,
            padding: "32px 16px",
            textAlign: "center",
            borderTop: "1px solid #1E2436",
          }}
        >
          <p
            style={{
              color: "#64748B",
              fontSize: 13,
              margin: "0 0 20px 0",
            }}
          >
            🎨 Creato con SnapToon
          </p>
          <a
            href="/login"
            style={{
              display: "inline-block",
              background: "#F59E0B",
              color: "#0D1017",
              padding: "12px 24px",
              borderRadius: 8,
              textDecoration: "none",
              fontWeight: 700,
              fontSize: 14,
            }}
          >
            Crea il tuo webtoon →
          </a>
        </div>
      </div>
    </div>
  );
}
