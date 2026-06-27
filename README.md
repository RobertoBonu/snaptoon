# SnapToon

> Dall'idea al fumetto, in uno snap.

App web in abbonamento per realizzare fumetti con AI: testo → sceneggiatura → stile → personaggi → vignette → impaginazione → PDF.

## Stato

🚧 **In sviluppo attivo** — MVP in costruzione.

## Stack tecnico

| Livello | Tecnologia |
|---|---|
| Frontend | Streamlit (Python 3.13) |
| Backend | Stesso processo Streamlit + package `snaptoon_core` |
| DB | Replit PostgreSQL |
| Object Storage | Replit Object Storage |
| Auth | Email + password (bcrypt), gestiti da admin |
| Hosting | Replit Reserved VM |
| Provider AI | OpenAI gpt-image-2, Anthropic Claude Opus, Google Gemini 3 |

## Struttura del repo

```
snaptoon/
├── app.py                    # Entry Streamlit
├── pages/                    # Pagine Streamlit
├── snaptoon_core/            # Logica business (gen, layout, styles, scene)
├── db/                       # Modelli SQLAlchemy + migrazioni Alembic
├── auth/                     # Login, hashing, sessioni
├── billing/                  # Credit ledger, quote enforcement
├── storage/                  # Wrapper Object Storage Replit
├── components/               # Componenti UI custom
│   └── ui/                   # Componenti riusabili
├── style/                    # Theme Streamlit + CSS injection
├── assets/                   # Logo, font, immagini brand
├── scripts/                  # Utility (migrazione, seed, ecc.)
├── tests/                    # Test suite
├── docs/                     # Documentazione interna
│   └── design/               # Specifiche design (per Replit Agent)
├── .replit                   # Configurazione Replit
├── replit.nix                # Dipendenze di sistema (Replit)
├── requirements.txt          # Dipendenze Python
└── .streamlit/
    └── config.toml           # Theme Streamlit
```

## Sviluppo

Vedi `docs/design/` per le specifiche complete dell'app.

Vedi `CLAUDE.md` e `REPLIT_AGENT.md` per le linee guida di chi sviluppa.

## License

Proprietario — © 2026 Roberto Bonu. Tutti i diritti riservati.
