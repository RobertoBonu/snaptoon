# Page Brief — 📝 Testo

## Scopo
Caricare il testo sorgente del fumetto e generare/editare la sceneggiatura (script).

## Quando l'utente arriva
- Subito dopo creazione progetto
- Dalla sidebar navigando a "📝 Testo"
- Dal sample project precaricato dall'onboarding

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
3. **(Tab Sorgente)** vedi sotto
4. **(Tab Sceneggiatura)** vedi sotto

## Tab 1 — Sorgente

### Sezioni
1. **Upload + paste**: file_uploader + text_area (mutualmente esclusivi, l'ultimo salvato vince)
2. **Generazione soggetto (opzionale)**: collapsibile, contiene form per generare un soggetto da zero
3. **Adatta a sceneggiatura**: bottone primary + cost preview

### Componenti chiave
- `st.file_uploader(type=["txt"])`
- `st.text_area(height=300)`
- `<CostPreview />` per costo crediti

### Interazioni
- **Upload file** → salva contenuto in DB → mostra in textarea
- **Salva sorgente** → POST `/api/projects/{slug}/source`
- **Generazione soggetto** → POST `/api/projects/{slug}/soggetto` → consuma 5 crediti → testo popolato
- **Adatta a sceneggiatura** → modale conferma costo → confirm → POST `/api/projects/{slug}/adapt` → consuma N crediti → script popolato → switch a tab Sceneggiatura

### Edge case
- File > 1 MB → errore
- File non testuale → errore
- Crediti insufficienti per adattamento → modale `<ConfirmDialog />` non si apre, errore inline
- Adattamento esistente → modale di conferma sovrascrittura "Hai già una sceneggiatura. Vuoi sovrascriverla?"

## Tab 2 — Sceneggiatura

### Sezioni (in ordine)
1. **Logline** (sezione)
2. **Personaggi del fumetto** (sezione con expander per personaggio)
3. **Copertina** (expander)
4. **Pagine** (expander per pagina, contiene expander per vignetta)

### Sezione Logline
- `st.text_area(value=script.logline, height=80)`
- Bottone "💾 Salva logline" inline (visibile solo se modificato)
- Salva su blur o explicit click

### Sezione Personaggi
- Lista di expander, uno per personaggio
- Ogni expander:
  - Header: nome personaggio
  - Body:
    - Form: nome (text_input) + visual_bible (text_area)
    - Bottoni: "💾 Salva" + "🗑 Elimina"
- In fondo: form "+ Aggiungi personaggio" (nome + visual_bible + bottone)

### Sezione Copertina (expander dedicato)
- Form:
  - Titolo del fumetto (text_input)
  - Sottotitolo (text_input)
  - Autore (text_input)
  - Descrizione visiva della copertina (text_area)
- Salva esplicito

### Sezione Pagine
Per ogni pagina (numerata):
- Expander header: "Pagina N — M vignette"
- All'interno, per ogni vignetta (numerata):
  - Card con border:
    - Cosa succede (text_area)
    - Sotto: "Dialoghi (N)" → mini-expander per ogni dialogo
      - Tipo (selectbox: FUMETTO/PENSIERO/DIDASCALIA/SFX)
      - Speaker (text_input, disabled se DIDASCALIA/SFX)
      - Testo (text_input)
      - Bottoni: 💾 Salva · 🗑 Elimina
    - In fondo: "+ Aggiungi dialogo"

### Componenti chiave
- Tutto con `st.expander`, `st.text_input`, `st.text_area`, `st.selectbox`
- Salvataggio: pattern explicit save (bottone "Salva" per ogni form)

### Interazioni
- **Modifica logline** → text_area modificato → bottone "Salva logline" appare → click → PATCH `/api/projects/{slug}/script/logline`
- **Modifica personaggio** → form per personaggio → click "Salva" → PATCH `/api/projects/{slug}/script/characters/{name}`
- **Aggiungi personaggio** → form + click → POST → lista aggiornata
- **Elimina personaggio** → click → `<ConfirmDialog />` → conferma → DELETE
- **Stesse logiche** per pagine, vignette, dialoghi

### Edge case
- Modifica concorrente (utente apre 2 tab) → ultimo salva vince
- Cancellazione personaggio referenziato in vignetta → warning "Questo personaggio è citato in N vignette. Eliminarlo non rimuove le citazioni."
- Sceneggiatura vuota (no pagine) → empty state "Nessuna pagina ancora. Aggiungi la prima."

## Streamlit
- File: `pages/1_📝_Testo.py`
- Pattern: forms con explicit submit, salvataggio backend
- Componenti pesanti (script di 24+ pagine): valutare lazy-loading degli expander pagina

## Layout
- Padding container ~32px
- Spazio verticale generoso tra sezioni
- Personaggi: card visualmente distinte
- Pagine: gerarchia visiva chiara (pagina > vignetta > dialogo)

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "📝 Testo".

## Performance
- Sceneggiatura lunga (24+ pagine): tutti gli expander **chiusi di default**
- Salvataggio incrementale: salvare solo il campo modificato (non l'intero script)
- `st.cache_data` su `load_script(slug)` con TTL breve
