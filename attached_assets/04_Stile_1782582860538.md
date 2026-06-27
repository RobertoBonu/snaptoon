# Page Brief — 🎨 Stile

## Scopo
Scegliere uno stile visivo per il progetto dalla libreria 98 preset (o crearne uno custom) e personalizzare l'aspetto della pagina (sfondo, font/colori balloon, caption, SFX).

## Quando l'utente arriva
- Dopo aver creato la sceneggiatura su 📝 Testo
- Dalla sidebar
- Per cambiare stile in corsa

## Stati
| Stato | Descrizione |
|---|---|
| **No style** | `style_id == None`. Tab Selezione mostra empty state. |
| **Style selected** | Tab Selezione mostra preset attivo. |
| **Browsing library** | Tab "Sfoglia libreria" aperto, filtraggio attivo |
| **Editing custom** | Tab "Personalizza" aperto, form di edit |
| **Aspect editing** | Tab "Aspetto pagina" aperto, color/font picker |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Stile visivo" + caption "Progetto: [NOME]"
2. **Tabs**: 5 tabs in orizzontale

## Tab 1 — Selezione

### Layout
- Card grande dello stile attivo (se settato) con:
  - Nome preset
  - Categoria
  - Espansione completa (preview)
  - Bottoni: "Sfoglia libreria" + "Personalizza"
- Se nessuno stile: `<EmptyState />` "Nessuno stile selezionato. Sfoglia la libreria."

## Tab 2 — Sfoglia libreria

### Layout
- **Filtro categorie**: 7 chip orizzontali (Personali, Fumetto, Illustrazione, Fotografia, Cinema, Kids, Fot. d'autore)
- Default: prima categoria con preset (di solito "Fumetto" o "🖌 I miei stili" se ne hai)
- **Grid 3-4 colonne** con `<StyleCard />` per ogni preset

### Card preset (struttura)
```
┌────────────────────────────┐
│ Heavy Ink Noir             │
│ [Fumetto]                  │
│                            │
│ Visual style: deep ambient │
│ black inks, heavy chiaro-  │
│ scuro chiar... [fade]      │
│                            │
│ [👁 Anteprima] [✨ Applica]│
└────────────────────────────┘
```

### Interazioni
- **Click filtro categoria** → cambia grid
- **Click Anteprima** → modale con espansione completa
- **Click Applica** → PATCH `/api/projects/{slug}/style` → toast "Stile applicato" → ritorna a Tab Selezione
- **Card stile attivo**: badge "Attivo" + bordo evidenziato

## Tab 3 — Personalizza (custom)

### Layout
- Form di editing di tutti i campi tecnici dello stile (per esperti):
  - ID stile (readonly)
  - Nome
  - Descrizione
  - Technique
  - Aesthetic
  - Palette
  - Lighting
  - Line work
  - Typography constraints (vincolato da CLAUDE.md: niente asterischi, virgolette, esplicita speaker)
  - Negative prompt
- Bottone "💾 Salva personalizzazioni"
- Se utente non ha un custom: messaggio "Lavori su un preset libreria. Salva una copia personalizzata per modificarlo." + bottone "Duplica come custom"

### Interazioni
- **Salva** → PATCH stile custom in DB
- **Duplica come custom** → crea nuovo `Style` con `is_custom=true`, prefisso `[CUSTOM] [nome originale]`

## Tab 4 — Aspetto pagina

### Layout
- 4 sezioni (in `st.expander`):
  1. **Sfondo pagina**: `st.color_picker` (default bianco)
  2. **Balloon (parlato)**: font · dim · colore testo · colore contorno · colore fondo FUMETTO · colore fondo PENSIERO
  3. **Didascalie**: font · dim · colore testo · colore contorno · colore fondo
  4. **Effetti sonori (SFX)**: font · dim · colore testo · colore contorno
- In fondo: bottone "↩️ Ripristina aspetto predefinito"

### Interazioni
- **Modifica qualsiasi campo** → debounce 500ms → salva
- **Anteprima inline**: piccolo riquadro che mostra "Esempio testo" con i font/colori attuali (utile per vedere senza tornare su Genera)

## Tab 5 — Anteprima prompt

### Layout
- Caption: "Ecco come verrà costruito il prompt di una vignetta tipo del tuo progetto:"
- `st.code()` con il prompt completo generato per una vignetta esempio
- Bottone "📋 Copia"
- Caption: "Questo è solo a scopo di verifica. Non si salva nulla."

## Componenti chiave
- `<StyleCard />`
- `<EmptyState />` (se no style)
- Color pickers, font selectors

## Edge case
- Cambio stile con vignette già generate → warning "Le vignette già generate restano. Per applicare il nuovo stile, rigenerale."
- Categoria vuota (es. nessuno stile personale ancora) → empty state "Non hai ancora stili personali."
- Stile preset libreria modificato direttamente (non duplicato): blocco con messaggio "Non puoi modificare un preset libreria. Duplicalo come custom prima."

## Streamlit
- File: `pages/2_🎨_Stile.py`
- Tab: `st.tabs(["Selezione", "Sfoglia libreria", "Personalizza", "Aspetto pagina", "Anteprima prompt"])`
- Color picker nativi
- Grid card con `st.columns(3)` ciclando

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "🎨 Stile".

## Performance
- Caricare tutti i 98 preset all'avvio: ok (sono testo, leggeri)
- Filtro categoria: client-side (filtraggio Python in memoria), nessun fetch
