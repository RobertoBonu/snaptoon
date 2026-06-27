# SnapToon — Design Brief per Replit Agent

> **Dall'idea al fumetto, in uno snap.**

Questo pacchetto contiene le **specifiche funzionali** dell'app web SnapToon (MVP). Definisce *cosa* l'app deve fare; *come* deve apparire (palette, font, mood, spacing, microanimazioni) è a discrezione di Replit Agent.

## Come usare questo pacchetto

1. Carica TUTTI i file di `docs/design/` nel contesto di Replit Agent
2. Leggi prima `07_REPLIT_AGENT.md` — definisce **cosa puoi e non puoi toccare**
3. Implementa il design seguendo le specifiche
4. Le scelte estetiche (palette, tipografia, mood, iconografia, microanimazioni) sono di tua libera scelta — purché coerenti tra tutte le pagine
5. Lavora SOLO sui file autorizzati elencati in `07_REPLIT_AGENT.md`

## Stack tecnico

| Livello | Tecnologia |
|---|---|
| Frontend | **Streamlit** (Python) |
| Theme | `.streamlit/config.toml` + CSS injection da `style/custom.css` |
| Componenti extra | `streamlit-extras`, `streamlit-image-coordinates`, `streamlit-authenticator` |
| Backend | Stesso processo Streamlit + `snaptoon_core` package Python |
| DB | Replit PostgreSQL (managed) |
| Storage | Replit Object Storage |
| Auth | Email + password (custom, bcrypt) — NO OAuth |
| Hosting | Replit Reserved VM |

## Indice del pacchetto

| File | Contenuto |
|---|---|
| `00_OVERVIEW.md` | Questo file |
| `01_INFORMATION_ARCHITECTURE.md` | Mappa pagine + navigazione |
| `02_USER_FLOWS.md` | 8 flussi utente principali |
| `03_PAGE_BRIEFS/` | 10 spec di pagina (una per schermata) |
| `04_UI_COMPONENTS.md` | Componenti UI ricorrenti |
| `05_STREAMLIT_CONSTRAINTS.md` | Vincoli tecnici Streamlit |
| `06_MICROCOPY.md` | Testi obbligatori (label, errori, CTA) |
| `07_REPLIT_AGENT.md` | Confini di responsabilità — **leggere PRIMA** |

## Principi di design (vincolanti)

1. **Single-task focus per schermata**. Ogni pagina ha UNO scopo dominante.
2. **Stati espliciti**. Ogni pagina definisce esplicitamente empty / loading / success / error.
3. **Sidebar persistente** con: logo, progetto attivo, navigazione, credit badge, account.
4. **Modifiche con feedback immediato**. Salvataggi atomici. Toast/banner di conferma.
5. **Distruttivo richiede conferma**. Eliminazioni, reset, rigenerazioni costose: doppia conferma.
6. **Pagine sotto i 4 fold sullo schermo desktop 1440×900**.
7. **Microcopy in italiano formale ma asciutto**.
8. **Privacy by default**.

## Vincoli MVP

- ❌ Mobile/responsive ottimizzato (desktop-first)
- ❌ Team / multi-utente / sharing
- ❌ Marketplace stili
- ❌ Collaborazione real-time
- ❌ Export IDML / EPUB (solo PDF)
- ❌ API pubblica
- ❌ Localizzazione (solo italiano)
- ❌ Modalità chiaro/scuro user-switchable

## Definizione di "fatto"

L'MVP è completo quando 5-15 beta tester possono creare account e completare un fumetto dall'inizio alla fine (testo → script → stile → personaggi → vignette → impagina → PDF) con crediti scalati correttamente.
