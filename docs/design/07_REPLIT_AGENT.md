# Replit Agent — Confini di responsabilità

> **Leggere PRIMA di iniziare qualsiasi modifica al codice.**

## ✅ File che PUOI toccare liberamente

| File / Cartella | Scopo |
|---|---|
| `.streamlit/config.toml` | Theme nativo Streamlit (palette, font) |
| `style/custom.css` | CSS injection per personalizzazioni |
| `style/icons/` | SVG icone se ti servono |
| `assets/brand/` | Logo, favicon, immagini brand |
| `components/ui/*.py` | Componenti UI riusabili custom |
| `components/wrappers.py` | Wrapper Streamlit per pattern ricorrenti |

## ⚠️ File che PUOI toccare con vincoli precisi

| File | Cosa SÌ | Cosa NO |
|---|---|---|
| `app.py` | Solo lo strato di markup/layout della home | Mai modificare le funzioni `auth_required()`, `load_session()`, `check_credits()` |
| `pages/*.py` | Solo struttura visiva (`st.columns`, `st.tabs`, `st.expander`, ordine sezioni, header pagina) | Mai modificare chiamate al `snaptoon_core`, mai modificare query DB, mai cambiare gli `st.session_state` keys |

**Regola d'oro**: se vedi una chiamata tipo `from snaptoon_core import ...`, `from db import ...`, `from billing import ...`, **non la tocchi**.

## ❌ File che NON DEVI MAI toccare

| File / Cartella | Perché |
|---|---|
| `snaptoon_core/` | Logica business: generator, layout, styles, scene |
| `db/` | Schema dati e logica DB |
| `billing/` | Credit ledger, quota enforcement |
| `auth/` | Logica autenticazione, hashing, sessioni |
| `storage/` | Wrapper Object Storage Replit |
| `.env`, `.env.example` | Variabili ambiente |
| `requirements.txt`, `pyproject.toml` | Dipendenze |
| `tests/` | Test suite |
| `scripts/` | Script di utilità / migrazione |

## Regole di base

1. **Mai installare nuove dipendenze senza chiedere**.
2. **Mai cambiare nomi di funzioni o variabili Python esistenti**.
3. **Mai cambiare le chiavi `st.session_state`**.
4. **Mai cambiare l'ordine dei parametri delle funzioni `snaptoon_core`**.
5. **Sempre committare con messaggi descrittivi**: `design: header SnapToon`, `design: tema scuro applicato a Stile`.
6. **Sempre testare visivamente** dopo ogni commit aprendo l'app nel Repl.

## Cosa decidi tu (libertà piena)

1. **Mood visivo complessivo**: chiaro o scuro, sobrio o vibrante
2. **Palette completa**: primary, secondary, accent, neutrals, semantic
3. **Tipografia**: font UI, font editoriale, scala
4. **Spacing scale**
5. **Border radius**
6. **Shadow / depth**
7. **Iconografia**: set unico coerente
8. **Logo SnapToon**
9. **Microcopy "voice"**: puoi rifinire il tono dei testi in `06_MICROCOPY.md`

## Vincoli estetici minimi

1. **Contrasto AA almeno** (WCAG)
2. **Niente font con costo licenza commerciale non chiarito**
3. **Niente animazioni in loop infinito**
4. **Niente effetti >300ms per transizione**
5. **Sidebar sempre visibile su desktop**
6. **Tema dominante coerente in tutte le pagine**

## In caso di dubbio

Cerca commenti `# OWNER: replit-agent` o `# OWNER: claude` nel file. Se non c'è: default = NON toccare.
