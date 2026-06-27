# Page Brief — 📐 Impagina

## Scopo
Renderizzare le pagine complete (vignette + balloon + sfondo) e esportarle in PDF stampabile.

## Stati
| Stato | Descrizione |
|---|---|
| **No vignettes** | Empty state "Nessuna vignetta ancora. Vai su Genera." |
| **Some pages ready** | Alcune pagine renderizzate, altre no |
| **All rendered** | Tutte le pagine renderizzate → bottone PDF abilitato |
| **Rendering** | Progress bar durante render bulk |
| **Exporting PDF** | Spinner durante creazione PDF |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Impagina" + caption "Progetto: [NOME] · [N] pagine"
2. **Stato globale**: "[X]/[Y] pagine renderizzate" + progress bar
3. **Bulk actions**: "📐 Renderizza tutte le pagine" · "📥 Esporta PDF"
4. **Lista pagine** (lista verticale):
   - Header + caption (gabbia + N vignette + N dialoghi)
   - Anteprima pagina o placeholder
   - Bottoni: "🎨 Renderizza pagina" / "📥 Scarica PNG"

## Costi crediti
- **Render pagina**: gratuito (operazione locale Python)
- **Export PDF**: gratuito (operazione locale Python)

## Performance
- Render pagina: 2-10s con `render_page()` in `snaptoon_core/layout.py`
- DPI target: 300 DPI per stampa

## Streamlit
- File: `pages/5_📐_Impagina.py`
- Download: `st.download_button` per PDF
