# Page Brief — 👥 Personaggi

## Scopo
Gestire il cast del progetto: descrivere ogni personaggio e creare le reference image che garantiranno coerenza visiva tra una vignetta e l'altra.

## Quando l'utente arriva
- Dopo aver scelto uno stile su 🎨 Stile
- Dalla sidebar
- Prima di generare le vignette su 🖼 Genera

## Stati
| Stato | Descrizione |
|---|---|
| **Empty** | Nessun personaggio nel progetto. Empty state + form rapido "+ Aggiungi" |
| **Cast loaded** | Lista personaggi visibile, alcuni con/senza reference |
| **Generating ref** | Spinner mentre genera reference (per quel personaggio) |
| **Ref corrupted** | Status 🟠 per personaggi con file PNG corrotto |
| **All complete** | Tutti i personaggi hanno reference valida |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Personaggi" + caption progetto
2. **Stato globale**: "[X]/[Y] personaggi hanno un'immagine di riferimento" + progress bar
3. **Bulk action** (se ci sono mancanti): bottone "🚀 Genera reference per i [N] mancanti"
4. **Lista personaggi**: ogni personaggio in un expander (auto-aperto se reference mancante o corrotta)
5. **Mini cast manager**: expander in fondo "🗂 Archivio personaggi (globale)"
6. **Aggiungi manualmente**: form "+ Aggiungi personaggio" in fondo

## Layout expander personaggio
```
┌────────────────────────────────────────────────────────┐
│ 🟢 Marco Riccio                                        │
├────────────────────────────────────────────────────────┤
│  [thumb 200x300]    Descrizione visiva                 │
│                     ┌──────────────────────────────┐  │
│                     │ Uomo sui 40, barba grigia,   │  │
│                     │ giacca pelle marrone.        │  │
│                     └──────────────────────────────┘  │
│                     [💾 Salva descrizione]            │
│                     [📤 Carica file]                  │
│                     [🔄 Rigenera con AI]              │
│                     [👁 Vedi prompt]                  │
│                     [📚 Reference aggiuntive (3/7)]   │
└────────────────────────────────────────────────────────┘
```

### Indicatori status
- 🟢 reference valida + integra
- 🟠 file presente ma PNG corrotto
- ⚪ nessuna reference ancora

## Componenti chiave
- `<CharacterCard />` per ogni personaggio
- `<CostPreview />` prima di generare
- `<ConfirmDialog />` per eliminazioni

## Streamlit
- File: `pages/3_👥_Personaggi.py`
