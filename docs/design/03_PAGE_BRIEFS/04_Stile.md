# Page Brief — 🎨 Stile

## Scopo
Scegliere uno stile visivo per il progetto dalla libreria preset (o crearne uno custom) e personalizzare l'aspetto della pagina (sfondo, font, colori balloon, caption, SFX).

## Stati
| Stato | Descrizione |
|---|---|
| **No style** | Tab Selezione mostra empty state |
| **Style selected** | Tab Selezione mostra preset attivo |
| **Browsing library** | Tab "Sfoglia libreria" aperto |
| **Editing custom** | Tab "Personalizza" aperto |
| **Aspect editing** | Tab "Aspetto pagina" aperto |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Stile visivo" + caption "Progetto: [NOME]"
2. **Tabs**: 5 tabs in orizzontale

## Tab 1 — Selezione
- Card grande dello stile attivo (se settato)
- Warning: "Le vignette già generate restano. Per applicare il nuovo stile, rigenerale su 🖼 Genera."

## Tab 2 — Sfoglia libreria
- Chip bar categorie: I miei stili / Fumetto / Illustrazione / Fotografia / Cinema / Kids / Fotografia d'autore
- Grid 3 colonne `<StyleCard />`

## Tab 3 — Personalizza
- Form campi tecnici: technique, aesthetic, palette, lighting, line work, negative prompt
- Bottone "💾 Salva personalizzazioni"

## Tab 4 — Aspetto pagina
- Expander: Sfondo pagina
- Expander: Balloon (parlato)
- Expander: Didascalie
- Expander: Effetti sonori (SFX)
- Bottone "↩️ Ripristina aspetto predefinito"

## Tab 5 — Anteprima prompt
- Blocco di codice con prompt completo ricostruito
- Caption: "Solo a scopo di verifica."

## Streamlit
- File: `pages/3_🎨_Stile.py`
