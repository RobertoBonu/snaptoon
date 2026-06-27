# Page Brief — 📝 Testo

## Scopo
Caricare il testo sorgente del fumetto e generare/editare la sceneggiatura (script).

## Stati
| Stato | Descrizione |
|---|---|
| **Empty (no source)** | Nessun testo sorgente caricato. Tab Sceneggiatura disabilitata. |
| **Source loaded** | Testo caricato. Bottone "Adatta a sceneggiatura" attivo. |
| **Adapting** | Spinner durante chiamata Claude. |
| **Script ready** | Sceneggiatura popolata. Tab Sceneggiatura attiva. |
| **Editing** | Utente sta modificando un campo. |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Testo" + nome progetto
2. **Tabs**: "Sorgente" / "Sceneggiatura"

## Tab 1 — Sorgente
1. **Upload + paste**: file_uploader + text_area
2. **Generazione soggetto (opzionale)**: collapsibile con form
3. **Bottone primario**: "🪄 Adatta a sceneggiatura" + `<CostPreview />`

## Tab 2 — Sceneggiatura
1. **Logline**: text_area editabile
2. **Personaggi del fumetto**: lista editabile (nome + descrizione visiva)
3. **Copertina** (expander): descrizione copertina
4. **Pagine**: per ogni pagina, per ogni vignetta: descrizione + dialoghi

## Componenti chiave
- `<PageHeader />`
- `<CostPreview />` prima di "Adatta a sceneggiatura"
- `<ConfirmDialog />` prima di sovrascrivere script esistente

## Streamlit
- File: `pages/2_📝_Testo.py`
