# Page Brief — 🖼 Genera

## Scopo
Generare le vignette del fumetto con AI. Configurare per ogni vignetta: cast, scena, formato, balloon. Selezionare gabbie di pagina. Generare la copertina.

## Quando l'utente arriva
- Dopo Stile + Personaggi pronti
- Pagina più "operativa" dell'app

## Stati
| Stato | Descrizione |
|---|---|
| **No script** | Empty state "Crea prima la sceneggiatura su Testo" |
| **No style** | Empty state "Scegli prima uno stile su Stile" |
| **Ready** | Pagine + vignette mostrate, alcune generate, altre no |
| **Generating single** | Spinner su singola vignetta |
| **Generating bulk** | Progress bar globale + status log |
| **Balloon editor mode** | Vista alternativa (sostituisce la pagina) per editing posizioni balloon |
| **Credits exhausted** | Modale bloccante apre ad ogni tentativo gen |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Genera vignette" + caption con info Provider · Modello · Stile · Qualità + Cache toggle
2. **Warning ref mancanti** (se presenti): banner giallo
3. **Stato globale**: "[X]/[Y] vignette generate" + progress bar
4. **Bulk actions**: 3 colonne — Stato/Progress · "🚀 Genera mancanti" · "🌙 Genera TUTTO"
5. **Container "🗂 Organizzazione pagine"**: contatore + bottone "+ Nuova pagina"
6. **Copertina** (expander dedicato in cima)
7. **Per ogni pagina** (expander):
   - Azioni a livello pagina (sposta, elimina)
   - Selettore gabbia + thumbnail + adatta formati
   - Grid 3 colonne con `<PanelCard />`

## Copertina (expander)
### Layout
- 2 colonne metadati: titolo/sottotitolo/autore (readonly link a "📝 Testo") · status illustrazione
- 3 bottoni in riga:
  - "🎨 Genera illustrazione" / "♻️ Rigenera illustrazione"
  - Popover "🎬 Scena" copertina
  - "🎨 Renderizza copertina (illustrazione + testi)"
- 2 colonne preview:
  - "Illustrazione (senza testi)" — immagine raw
  - "Copertina finale (con testi sovrapposti)" — immagine renderizzata
- Sezione "Box di testo": 3 mini-editor (Title/Subtitle/Author) con font/colore/posizione/allineamento per ognuno

## Card vignetta (struttura)
Vedi `<PanelCard />` in `04_UI_COMPONENTS.md`.

## Popover "🎬 Scena"
Pattern già consolidato in Creative Studio:
- Header esplicativo
- 👥 Personaggi nella scena (multiselect)
  - Bottone "🔍 Auto-rileva da descrizione (N)" — pre-popola
  - Bottone "🧹 Reset cast"
  - Filtro difensivo: scarta personaggi non più esistenti (warning)
- Formato vignetta (selectbox 8 opzioni + default)
- Distanza inquadratura (selectbox 9 opzioni + default)
- Angolo / inquadratura speciale (selectbox 11 opzioni + default)
- Tono emotivo (selectbox 13 opzioni + default)
- Bottoni: "💾 Salva scena" + "↩️ Reset scena"
- Caption riepilogo: "Attivi adesso: 👥 X (3 ref) · 📐 ... · 🎥 ... · 🎞 ... · 🎭 ..."

## Popover "👁 Prompt"
- `st.code()` con il prompt completo ricostruito per la vignetta corrente
- Caption: "Solo per verifica. Non si salva."

## Popover "📦 Sposta vignetta"
- Selectbox "Sposta su": pagine esistenti + "Nuova pagina in fondo"
- Selectbox "Posizione": "All'inizio" / "Dopo vignetta N" (per pagine esistenti)
- Bottone "✅ Conferma sposta"

## Vista Balloon Editor (modale)
Quando utente clicca "🎈 Balloon" su una vignetta con dialoghi, la pagina commuta in modalità balloon editor (vedi `02_USER_FLOWS.md` flusso 6).

### Layout balloon editor
- Bottone "← Indietro" in alto a sinistra
- Titolo: "🎈 Balloon — Pagina N, Vignetta M"
- 2 colonne grandi:
  - **Sinistra (60%)**: Canvas con immagine vignetta + preview balloon overlay (componente `streamlit-image-coordinates`)
  - **Destra (40%)**: pannello controlli
    - Radio "Dialogo da modificare" (lista)
    - Section "Posizione" — slider X + nudge buttons + slider Y + nudge buttons
    - Preset rapidi: ⬆ Alto · ◆ Centro · ⬇ Basso
    - Section "Forma del balloon": selectbox 5 forme
    - Section "🎯 Tail" (solo per FUMETTO/PENSIERO):
      - Toggle "Mostra tail"
      - Slider tail X + nudge
      - Slider tail Y + nudge
      - Preset 4 direzioni
      - Bottone "↩️ Tail automatica"
    - In fondo: "↩️ Auto-posizione balloon" · "🧹 Reset tutti i balloon"
- Sotto caption: status posizione corrente

## Componenti chiave
- `<PanelCard />` × ogni vignetta
- `<GridPicker />` × ogni pagina
- `<CostPreview />` prima di operazioni costose
- `<ConfirmDialog />` per crediti finiti / rigenerazione

## Interazioni
- **Click "✨ Genera" su singola vignetta** → `<CostPreview />` inline → click → spinner → POST `/api/.../panels/{n}/generate` → costa N crediti → success → immagine appare
- **Click "🚀 Genera vignette mancanti"** → conferma costo bulk → progress bar → log errori finali
- **Click "🌙 Genera TUTTO"** → conferma costo (refs + vignettes) → fase 1 ref + fase 2 vignette → progress globale → log finali
- **Popover Scena → Salva** → POST cast + scene params → invalidazione cache prompt
- **Popover Sposta → Conferma** → DELETE+INSERT → rerun
- **Click "🎈 Balloon"** → session_state mode = balloon_editor → rerun
- **Click "← Indietro"** dal balloon → exit mode → rerun

## Edge case
- Vignetta cast contiene personaggi non più esistenti → caption warning + filtro automatico
- Bulk operation con errori parziali → log finale + bottone "Riprova falliti"
- Crediti insufficienti pre-operazione → modale bloccante
- Cache hit → immagine istantanea, nessun credito scalato
- Streamlit timeout durante long-running (Reserved VM ~120s) → spostare a Scheduled Deployment per batch >20 vignette in V1.1

## Streamlit
- File: `pages/4_🖼_Genera.py`
- Pattern: già completamente sviluppato in Creative Studio
- Bulk operations: usare `st.progress` + `st.empty` per status
- Balloon editor: stato in `session_state["balloon_editor"] = (page_num, panel_num)`

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "🖼 Genera".

## Performance
- Vignetta generation: 20-60s con OpenAI Media → spinner + cancellable button (V1.1)
- Bulk: rate-limit ~3 vignette/min per non saturare OpenAI tier
- Caching: hash di (prompt + ref_files + quality + size) — già implementato in `snaptoon_core`
- Mai più di 30 vignette per pagina (UI degrada)
