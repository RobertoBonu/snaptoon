# Replit Agent — Confini di responsabilità

> **Leggere PRIMA di iniziare qualsiasi modifica al codice.**

Questo file definisce cosa Replit Agent può e non può toccare. Lo sviluppatore umano (Claude/Roberto) lavora in parallelo sulla logica; per evitare conflitti, i confini sono rigorosi.

## ✅ File che PUOI toccare liberamente

| File / Cartella | Scopo |
|---|---|
| `.streamlit/config.toml` | Theme nativo Streamlit (palette, font) |
| `style/custom.css` | CSS injection per personalizzazioni |
| `style/icons/` | SVG icone se ti servono |
| `assets/brand/` | Logo, favicon, immagini brand (puoi anche generarli) |
| `components/ui/*.py` | Componenti UI riusabili custom (vedi `04_UI_COMPONENTS.md`) |
| `components/wrappers.py` | Wrapper Streamlit per pattern ricorrenti (header pagina, card vignetta, ecc.) |

## ⚠️ File che PUOI toccare con vincoli precisi

| File | Cosa SÌ | Cosa NO |
|---|---|---|
| `app.py` | Solo lo strato di markup/layout della home | Mai modificare le funzioni `auth_required()`, `load_session()`, `check_credits()` |
| `pages/*.py` | Solo struttura visiva (`st.columns`, `st.tabs`, `st.expander`, `st.popover`, ordine sezioni, header pagina) | Mai modificare chiamate al `snaptoon_core`, mai modificare query DB, mai cambiare gli `st.session_state` keys |

**Regola d'oro**: se vedi una chiamata tipo `from snaptoon_core import ...`, `from db import ...`, `from billing import ...`, **non la tocchi**. Modifichi solo come gli elementi visivi le circondano.

## ❌ File che NON DEVI MAI toccare

| File / Cartella | Perché |
|---|---|
| `snaptoon_core/` | Logica business: generator, layout, styles, scene. Solo Claude/Roberto la modifica. |
| `db/` (modelli SQLAlchemy + migrazioni Alembic) | Schema dati e logica DB |
| `billing/` | Credit ledger, quote enforcement, subscription logic |
| `auth/` | Logica autenticazione, hashing, sessioni |
| `storage/` | Wrapper Object Storage Replit |
| `core_logic/` (se esiste) | Qualsiasi modulo Python con logica di business |
| `.env`, `.env.example` | Variabili ambiente |
| `requirements.txt`, `pyproject.toml` | Dipendenze (chiedi prima di aggiungere) |
| `tests/` | Test suite |
| `scripts/` | Script di utilità / migrazione |

## Regole di base

1. **Mai installare nuove dipendenze senza chiedere**. Se ti serve `streamlit-X`, chiedi nei commenti del commit.
2. **Mai cambiare nomi di funzioni o variabili Python esistenti**. Anche se ti sembrano brutti.
3. **Mai cambiare le chiavi `st.session_state`**. Sono il contratto con la logica.
4. **Mai cambiare l'ordine dei parametri delle funzioni `snaptoon_core`**.
5. **Sempre committare con messaggi descrittivi**: `design: header SnapToon più tipografico`, `design: tema scuro applicato a Stile`, ecc.
6. **Sempre testare visivamente** dopo ogni commit aprendo l'app nel Repl.

## Cosa decidi tu (libertà piena)

1. **Mood visivo complessivo**: chiaro o scuro, sobrio o vibrante, editorial o tech
2. **Palette completa**: primary, secondary, accent, neutrals, semantic
3. **Tipografia**: font UI, font editoriale, scala (h1-h4-body-caption)
4. **Spacing scale**: il sistema di unità (4/8/12 multipli o altro)
5. **Border radius**: tondo, squadrato, asimmetrico
6. **Shadow / depth**: piatto, soft, drammatico
7. **Iconografia**: set unico (lucide, phosphor, material, custom) — coerente ovunque
8. **Logo SnapToon**: lo crei tu (suggerimento: parti da una wordmark sobria; il fumetto è già esuberante di suo)
9. **Microcopy "voice"**: puoi rifinire il tono dei testi suggeriti in `06_MICROCOPY.md` (più asciutto, più caldo, ecc.) finché resta in italiano e non paternalistico

## Vincoli estetici minimi

Anche se hai libertà:

1. **Contrasto AA almeno** per testo su sfondo (WCAG)
2. **Niente font con costo licenza commerciale non chiarito**. Usa font open o Google Fonts.
3. **Niente animazioni che girano in loop infinito** (battery drain, distrae dall'editing)
4. **Niente effetti che richiedono >300ms per transizione**. Streamlit non li sostiene bene.
5. **Sidebar sempre visibile su desktop** (mai collapsing automatico). Su mobile può collassare.
6. **Tema dominante coerente in tutte le pagine**. Non mixare scuro/chiaro tra pagine diverse.

## Workflow di lavoro

```
1. Tu: leggi 00_OVERVIEW.md, 01_INFORMATION_ARCHITECTURE.md, 02_USER_FLOWS.md
2. Tu: leggi tutti i 10 Page Briefs in 03_PAGE_BRIEFS/
3. Tu: leggi 04_UI_COMPONENTS.md, 05_STREAMLIT_CONSTRAINTS.md, 06_MICROCOPY.md
4. Tu: scegli mood + palette + font + spacing
5. Tu: crei .streamlit/config.toml + style/custom.css di base
6. Tu: crei i componenti UI riusabili in components/ui/
7. Tu: applichi il design al markup delle pagine pages/*.py
8. Tu: committi con messaggi descrittivi
9. Tu: apri l'app, controlli, ritocchi
10. Tu: chiedi feedback specifico quando senti che serve
```

## In caso di dubbio

Se non sei sicuro se un file rientra nei tuoi "✅" o "❌":
1. Apri il file
2. Cerca commenti tipo `# OWNER: replit-agent` o `# OWNER: claude`
3. Se il file inizia con un commento "OWNER", rispetta quello
4. Se non c'è, default = NON toccare. Chiedi nei commenti del commit.

## Domande frequenti

**Posso aggiungere componenti React custom dentro Streamlit?**
No, per MVP. Solo componenti Streamlit nativi + CSS. React aggiunge complessità di build.

**Posso modificare il file `requirements.txt`?**
No. Se ti serve una libreria nuova, scrivi un TODO in `style/custom.css` con `/* TODO: ho bisogno di streamlit-extras */` e lo gestiamo manualmente.

**Posso cambiare la struttura delle cartelle?**
No. La struttura riflette i confini di responsabilità. Cambiarla rompe il workflow.

**Posso usare emoji nelle UI?**
Sì, con parsimonia. Le emoji sono cross-platform e accessibili. Già usate nella nav (📝 Testo, 🎨 Stile, ecc.). Non aggiungerne altrove se non aggiunge informazione.
