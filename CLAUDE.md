# Contesto per agenti AI

Questo file fornisce contesto a chi (Claude, Replit Agent, altri) lavora sulla codebase.

## Prodotto

**SnapToon** è un'app web in abbonamento per creare fumetti con AI. Stack: Streamlit + Python + Replit (DB, storage, auth, hosting).

Payoff: *Dall'idea al fumetto, in uno snap.*

L'MVP porta su web il prodotto desktop Streamlit "Creative Studio" (cartella `~/Projects/creative-studio/` sul Mac di Roberto), adattato a multi-utente con auth, billing a crediti, storage cloud.

## Specifiche complete

Tutte le specifiche funzionali sono in `docs/design/`. Leggi sempre PRIMA di modificare codice:

- `docs/design/00_OVERVIEW.md` — punto di ingresso
- `docs/design/01_INFORMATION_ARCHITECTURE.md` — mappa pagine + sidebar
- `docs/design/02_USER_FLOWS.md` — 8 flussi utente
- `docs/design/03_PAGE_BRIEFS/` — spec per ogni pagina
- `docs/design/04_UI_COMPONENTS.md` — componenti riusabili
- `docs/design/05_STREAMLIT_CONSTRAINTS.md` — vincoli tecnici Streamlit
- `docs/design/06_MICROCOPY.md` — testi italiani definitivi
- `docs/design/07_REPLIT_AGENT.md` — confini di responsabilità tra agenti

## Divisione del lavoro

| Chi | Cosa |
|---|---|
| **Claude (qui)** | Logica business, DB, auth, billing, integrazione `snaptoon_core`, generator AI, layout PIL, PDF export |
| **Replit Agent (dentro Replit)** | Design visivo: theme, palette, font, CSS, componenti UI custom, layout markup delle pagine |
| **Roberto Bonu** | Product decisions, review, beta test |

Vedi `docs/design/07_REPLIT_AGENT.md` per i confini precisi.

## Regole d'oro

1. **Sceneggiatura/testi nelle immagini generate**: mai asterischi, mai testo cancellato/barrato. Usa virgolette tipografiche («»). Esplicita sempre chi parla nelle didascalie. (Vincolo proveniente da CLAUDE.md di Creative Studio.)
2. **Solo fumetti** in MVP. Niente graphic novel, niente libri illustrati.
3. **Le immagini delle vignette devono essere full-bleed**: no cornici, no margini, no carta. Il prompt builder in `snaptoon_core` lo enforce.
4. **Personaggi consistenti tra vignette**: il cast esplicito vince sul parsing automatico della descrizione.
5. **Atomic write** per ogni PNG: scrittura su `.tmp` + rename. Cache hash-based su `(prompt + refs + quality + size)`.

## Modello dati (sintesi)

| Tabella | Scopo |
|---|---|
| `users` | Utenti — auth email/password |
| `projects` | Progetti fumetto |
| `scripts` | Logline + characters + pages + panels + dialogues |
| `character_sheets` | Cast del progetto |
| `reference_images` | Reference per character (slot 1-7) |
| `styles` | Style attivo (preset id o custom yaml) |
| `vignettes` | Vignette generate (storage key) |
| `page_layouts` | Grid + balloon visibility per pagina |
| `subscriptions` | Piano attivo per utente |
| `credit_ledger` | Append-only: tutti i movimenti crediti |
| `usage_log` | Audit di ogni operazione AI |
| `admin_audit` | Audit di ogni azione admin |

Schema completo in `db/models.py` (in arrivo).

## Stato sviluppo

Fase 1 — Foundation: **in corso**.

Vedi commit history e issue su GitHub.
