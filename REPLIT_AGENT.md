# Replit Agent — istruzioni rapide

> **Leggere `docs/design/07_REPLIT_AGENT.md` per la versione completa.**

Questo file è un puntatore visibile nella root del repo. Le istruzioni complete (cosa puoi/non puoi toccare, regole, workflow) stanno in `docs/design/07_REPLIT_AGENT.md`.

## In sintesi

**✅ Puoi toccare**:
- `.streamlit/config.toml`
- `style/custom.css`
- `style/icons/`
- `assets/brand/`
- `components/ui/*.py`
- Markup visivo dentro `app.py` e `pages/*.py` (NON la logica)

**❌ Non toccare mai**:
- `snaptoon_core/` (logica generator + styles + layout)
- `db/`, `auth/`, `billing/`, `storage/`
- `requirements.txt`, `.env`, `pyproject.toml`

## Le scelte estetiche sono TUE

Palette, tipografia, mood, iconografia, microanimazioni: le decidi tu. Le specifiche in `docs/design/` definiscono **cosa** l'app fa, non **come appare**.

## Workflow

1. Leggi tutto in `docs/design/` (parti da `00_OVERVIEW.md`)
2. Scegli mood + palette + font
3. Crea `.streamlit/config.toml` + `style/custom.css` di base
4. Crea componenti UI riusabili in `components/ui/`
5. Applica il design al markup delle pagine
6. Committa con messaggi descrittivi (`design: header pagina X`, `design: theme tokens`)
7. Apri l'app, controlla, ritocca
