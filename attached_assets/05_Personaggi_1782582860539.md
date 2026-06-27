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
| **All complete** | Tutti i personaggi hanno reference valida → pronti per Genera |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Personaggi" + caption progetto
2. **Stato globale**: "[X]/[Y] personaggi hanno un'immagine di riferimento" + progress bar
3. **Bulk action** (se ci sono mancanti): bottone "🚀 Genera reference per i [N] mancanti"
4. **Lista personaggi**: ogni personaggio in un expander (auto-aperto se reference mancante o corrotta)
5. **Mini cast manager**: expander in fondo "🗂 Archivio personaggi (globale)" — per importare personaggi salvati in archivi precedenti
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
│                                                        │
│                     [📤 Carica file]                  │
│                     [🔄 Rigenera con AI]              │
│                                                        │
│                     [👁 Vedi prompt]                  │
│                                                        │
│                     [📚 Reference aggiuntive (3/7)]   │
└────────────────────────────────────────────────────────┘
```

### Indicatori status
- 🟢 reference valida + integra
- 🟠 file presente ma PNG corrotto → bottone "🗑 Elimina file corrotto"
- ⚪ nessuna reference ancora

## Popover/Expander "Reference aggiuntive"
- Slot 1 = reference principale (sopra)
- Slot 2-7 = varianti

### Layout dentro al popover
- Caption esplicativa
- Bulk action "✨ Genera [N] varianti mancanti (profilo, 3/4, full-body, sorriso...)" — solo se slot1 valida
- Per ogni slot 2-7:
  - Indicatore status
  - Thumb (se valida)
  - Selectbox "Tipo variante" (6 opzioni)
  - Bottone genera variante + upload manuale
  - Bottone elimina

## Componenti chiave
- `<CharacterCard />` per ogni personaggio
- `<CostPreview />` prima di generare
- `<ConfirmDialog />` per eliminazioni

## Interazioni
- **Modifica visual_description** → form + salva esplicito
- **Genera reference** → POST `/api/projects/{slug}/characters/{name}/reference` → costa 1 credito → success → immagine appare
- **Upload file** → POST upload → backend valida PNG/JPG → atomic save
- **Bulk genera mancanti** → loop reference mancanti → progress bar → log errori
- **Genera variante slot N** → POST `/api/.../reference/slot/{N}` con kind → costa 1 credito
- **Elimina personaggio** → DELETE → conferma
- **Aggiungi personaggio manuale** → POST → lista aggiornata
- **Importa da archivio**: utente sceglie character da `cast_archive` globale → POST `/api/projects/{slug}/characters/import`

## Edge case
- Personaggio senza visual_description al click "Genera" → errore "Aggiungi prima una descrizione visiva."
- Cast vuoto + script con personaggi nei dialoghi → mostrare suggerimento "Importali dalla sceneggiatura" (auto-import bottone)
- Upload PNG > 4 MB → errore
- Upload file non immagine → errore
- API OpenAI fallita → errore retry-friendly

## Streamlit
- File: `pages/3_👥_Personaggi.py`
- Expander per personaggio
- File uploader per upload manuale
- Atomic write per save PNG (già implementato)
- Difensiva su file corrotti (già implementata)

## Layout
- Personaggi in lista verticale (no grid)
- Spazio verticale tra expander generoso
- Thumbnail uniforme (es. 200x300)

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "👥 Personaggi".

## Performance
- Reference image salvate in Object Storage Replit con `storage_key`
- Caricamento lazy: thumb mostrata solo quando expander aperto
- Validazione PNG difensiva all'apertura per detect file troncati
