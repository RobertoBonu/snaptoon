# Page Brief — 📐 Impagina

## Scopo
Renderizzare le pagine complete (vignette + balloon + sfondo) e esportarle in PDF stampabile.

## Quando l'utente arriva
- Dopo aver generato le vignette su 🖼 Genera
- Dalla sidebar
- Per riesportare un PDF dopo modifiche

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
3. **Bulk actions**: 2 colonne
   - "📐 Renderizza tutte le pagine"
   - "📥 Esporta PDF" (disabled finché almeno 1 pagina renderizzata)
4. **Lista pagine** (lista verticale, una per pagina):
   - Header pagina
   - Caption: gabbia attiva + N vignette + N dialoghi
   - Anteprima pagina renderizzata (se esiste) o placeholder
   - Bottoni inline:
     - "🎨 Renderizza pagina" / "♻️ Rigenera pagina"
     - "📥 Scarica PNG" (solo se renderizzata)

## Layout per pagina
```
┌─────────────────────────────────────────────────────┐
│ Pagina 1                                            │
│ Gabbia: 1+2+3 crescendo · 6 vignette · 4 dialoghi   │
│                                                     │
│ ┌───────────────────────────────────────┐           │
│ │                                       │           │
│ │     [Anteprima pagina renderizzata]   │           │
│ │           o placeholder               │           │
│ │                                       │           │
│ └───────────────────────────────────────┘           │
│                                                     │
│ [🎨 Renderizza pagina]   [📥 Scarica PNG]           │
└─────────────────────────────────────────────────────┘
```

## Componenti chiave
- `<PageHeader />` (con azioni globali render+export)
- Card per pagina (struttura sopra)

## Interazioni
- **Click "Renderizza tutte le pagine"** → loop pagine → render → progress bar → log
- **Click "Renderizza pagina" singola** → POST `/api/.../pages/{n}/render` → spinner → success → preview appare
- **Click "Esporta PDF"** → POST `/api/.../export/pdf` → spinner → download automatico file PDF
- **Click "Scarica PNG"** → download diretto da Object Storage

## Edge case
- Pagina con vignette non tutte generate → render con buchi (placeholder grigio nelle celle vuote) + warning sulla card "X vignette mancanti su questa pagina"
- Render fallisce (errore PIL, file corrotto) → toast errore + bottone "Riprova"
- PDF con 0 pagine renderizzate → bottone disabilitato + tooltip
- Streamlit timeout durante render bulk di >20 pagine → spostare a Scheduled Deployment (V1.1)
- Export PDF di 50+ pagine: spinner lungo (10-30s) → mostrare progress se possibile

## Streamlit
- File: `pages/5_📐_Impagina.py`
- Pattern già consolidato
- Download file: `st.download_button` per PDF
- Atomic save PNG con scrittura `.tmp` + rename

## Layout
- Padding standard
- Anteprima pagina ridimensionata (max 500px height)
- Bottoni inline e simmetrici

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "📐 Impagina".

## Costi crediti
- **Render pagina**: gratuito (operazione locale Python)
- **Export PDF**: gratuito (operazione locale Python)
- L'unica spesa è stata generare le vignette su 🖼 Genera

## Performance
- Render pagina: 2-10s con `render_page()` in `snaptoon_core/layout.py`
- Supersampling 2× per qualità stampa
- PDF multipagina: solo concatenazione PIL → veloce
- Cache: pagina renderizzata salvata in Object Storage, ri-renderizzare solo su esplicita richiesta utente

## Note tecniche stampa
- DPI target: 300 DPI per stampa
- Risoluzione pagina: dipende da formato (A4 a 300DPI = 2480×3508 px)
- Per MVP: usare `render_page()` esistente di Creative Studio (output ~2000×3000 px), sufficiente per stampa "amatoriale" e ottimo per digitale
- V1.1: pipeline render print-grade con bleed marks
