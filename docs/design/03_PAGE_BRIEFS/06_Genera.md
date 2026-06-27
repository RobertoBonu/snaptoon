# Page Brief — 🖼 Genera

## Scopo
Generare le vignette del fumetto con AI. Configurare per ogni vignetta: cast, scena, formato, balloon. Selezionare gabbie di pagina. Generare la copertina.

## Stati
| Stato | Descrizione |
|---|---|
| **No script** | Empty state "Crea prima la sceneggiatura su Testo" |
| **No style** | Empty state "Scegli prima uno stile su Stile" |
| **Ready** | Pagine + vignette mostrate |
| **Generating single** | Spinner su singola vignetta |
| **Generating bulk** | Progress bar globale + status log |
| **Balloon editor mode** | Vista alternativa per editing posizioni balloon |
| **Credits exhausted** | Modale bloccante |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo + caption Provider · Modello · Stile · Qualità
2. **Warning ref mancanti** (se presenti): banner giallo
3. **Stato globale**: "[X]/[Y] vignette generate" + progress bar
4. **Bulk actions**: "🚀 Genera mancanti" · "🌙 Genera TUTTO"
5. **Copertina** (expander dedicato in cima)
6. **Per ogni pagina** (expander): selettore gabbia + grid `<PanelCard />`

## Copertina (expander)
- 2 colonne metadati (readonly): titolo/sottotitolo/autore
- 3 bottoni: "🎨 Genera illustrazione" · popover "🎬 Scena" · "🎨 Renderizza copertina"
- 2 colonne preview: illustrazione raw + copertina finale con testi
- Sezione "Box di testo": 3 mini-editor (Title/Subtitle/Author)

## Vista Balloon Editor
Layout 2 colonne:
- **Sinistra (60%)**: Canvas con immagine + overlay balloon (streamlit-image-coordinates)
- **Destra (40%)**: pannello controlli
  - Radio dialogo da modificare
  - Slider X/Y posizione + nudge buttons + preset (Alto/Centro/Basso)
  - Forma balloon (5 forme)
  - Toggle tail + Slider tail X/Y + preset direzioni
  - Reset / Reset tutti

## Componenti chiave
- `<PanelCard />` × ogni vignetta
- `<GridPicker />` × ogni pagina
- `<CostPreview />` prima di operazioni costose
- `<ConfirmDialog />`

## Streamlit
- File: `pages/4_🖼_Genera.py`
- Balloon editor: stato in `session_state["balloon_editor"] = (page_num, panel_num)`
