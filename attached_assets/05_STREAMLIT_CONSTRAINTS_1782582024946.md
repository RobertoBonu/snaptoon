# Streamlit Constraints

Limiti tecnici reali di Streamlit. Replit Agent deve conoscerli per evitare di promettere cose impossibili o costose.

## Versione target

- **Streamlit ≥ 1.40**
- **Python 3.13**

## Componenti Streamlit nativi disponibili

### Layout
- `st.set_page_config(...)` (chiamato 1 volta per pagina)
- `st.title()`, `st.header()`, `st.subheader()`, `st.markdown()`, `st.caption()`, `st.text()`
- `st.columns([2, 1])` (proporzioni o lista di int)
- `st.tabs(["A", "B"])`
- `st.expander("Titolo", expanded=False)`
- `st.popover("Apri")` (utile per panel di azioni secondarie)
- `st.sidebar` (contesto)
- `st.container(border=True)` (border opzionale)
- `st.divider()`
- `st.empty()` (placeholder dinamico)

### Input
- `st.text_input()`, `st.text_area()`, `st.number_input()`
- `st.selectbox()`, `st.multiselect()`, `st.radio()`
- `st.slider()`, `st.toggle()`
- `st.color_picker()`
- `st.file_uploader()`
- `st.form()` + `st.form_submit_button()`

### Output
- `st.write()` (universal)
- `st.image()`, `st.audio()`, `st.video()`
- `st.dataframe()`, `st.table()`
- `st.json()`, `st.code()`
- `st.metric()`, `st.progress()`
- `st.success()`, `st.info()`, `st.warning()`, `st.error()`
- `st.toast("Salvato!")` (notifica auto-dismissing)
- `st.balloons()`, `st.snow()` (decorativi, evitare in MVP)

### Stato e flow
- `st.session_state` (dict-like)
- `st.rerun()` (forza re-esecuzione)
- `st.stop()` (interrompe pagina)
- `st.cache_data`, `st.cache_resource` (caching)

## Componenti di terze parti autorizzati

| Libreria | Uso |
|---|---|
| `streamlit-extras` | `colored_header`, `add_vertical_space`, `metric_cards`, `stylable_container`, `tags` |
| `streamlit-image-coordinates` | Canvas cliccabile per balloon editor |
| `streamlit-authenticator` (opzionale) | Login form pronto. Da valutare. |
| `streamlit-elements` (opzionale) | Layout grid CSS-like, evitare se non strettamente necessario |

## Componenti NON disponibili (cose che Streamlit non sostiene bene)

### ❌ Drag & drop di card / componenti
Esiste `streamlit-sortables` ma è instabile. Per riordinare vignette → usiamo "Sposta a pagina X" con dropdown, non drag.

### ❌ Modal native bloccanti
`st.dialog` esiste ma è limitato (no overlay vero, no escape blocking). Per conferme distruttive: usare `st.expander` con border + state esplicito.

### ❌ Routing client-side
Streamlit ricarica l'intera pagina a ogni interazione. Niente "smooth transitions" tra route. Le sezioni sono pagine separate in `pages/`.

### ❌ Animazioni e transizioni CSS complesse
Streamlit ri-renderizza il DOM completamente. Le animazioni CSS si interrompono. Limitarsi a:
- Hover semplici
- Transition su color/background (max 200ms)
- No keyframe loops
- No scroll-triggered

### ❌ Notifiche push / SSE / WebSocket persistenti
Streamlit comunica solo via WebSocket interno suo. Per "stato live" durante una generazione lunga: si usa polling con `st.empty()` + `time.sleep()` (già implementato in Creative Studio).

### ❌ Layout responsive vero
Streamlit ha breakpoint molto rudimentali. Le colonne diventano stack su mobile, ma il design è desktop-first. Niente "tablet-optimized".

### ❌ Componenti React custom
Tecnicamente possibili via `streamlit-components`, ma per MVP non li usiamo. Tutto via Streamlit native + CSS.

### ❌ Sidebar collapsable programmatica
La sidebar Streamlit può solo essere mostrata/nascosta tramite `initial_sidebar_state` in `set_page_config`. Niente toggle dinamico.

### ❌ Tooltips ricchi multi-riga
Solo tooltip semplici via parametro `help=` di vari componenti.

## CSS Injection — guida

Streamlit espone selettori `[data-testid="..."]` per molti componenti. Il file `style/custom.css` viene iniettato all'avvio con:

```python
def inject_css():
    css = Path("style/custom.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
```

### Selettori utili (da testare)

```css
/* Sidebar */
[data-testid="stSidebar"] { ... }
[data-testid="stSidebarNav"] { ... }

/* Pulsanti */
.stButton button { ... }
.stButton button[kind="primary"] { ... }

/* Form */
.stTextInput input { ... }
.stTextArea textarea { ... }
.stSelectbox > div { ... }

/* Layout */
.main .block-container { ... } /* container principale */
[data-testid="column"] { ... }
[data-testid="stExpander"] { ... }
[data-testid="stPopover"] { ... }

/* Metriche e badges */
[data-testid="stMetric"] { ... }

/* Header app */
[data-testid="stHeader"] { display: none; } /* nascondere se vuoi look "app-like" */
[data-testid="stToolbar"] { display: none; } /* hamburger menu */

/* Footer "Made with Streamlit" */
footer { display: none; }
```

### Cosa NON fare

- `position: fixed` su elementi che Streamlit re-renderizza (perdono fixed dopo rerun)
- `transform` su elementi cliccabili (rompe gli event handler)
- `overflow: hidden` su contenitori che possono espandersi (taglia contenuto)

## Pattern di interazione consigliati

### Conferma operazione costosa
```python
if st.button("🌙 Genera TUTTO"):
    st.session_state["confirm_gen_all"] = True

if st.session_state.get("confirm_gen_all"):
    with st.container(border=True):
        st.warning(f"Stai per generare {N} vignette. Costo: {cost} crediti.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Conferma", type="primary"):
                # esegui
                st.session_state.pop("confirm_gen_all")
                st.rerun()
        with col2:
            if st.button("Annulla"):
                st.session_state.pop("confirm_gen_all")
                st.rerun()
```

### Loading durante operazione
```python
with st.spinner(f"Generazione in corso..."):
    result = long_operation()
st.success("Fatto!")
```

### Progress bar per bulk
```python
progress = st.progress(0)
status = st.empty()
for i, item in enumerate(items, 1):
    status.write(f"⏳ {item.name}...")
    process(item)
    progress.progress(i / len(items))
status.write("✅ Completato")
```

## Performance — vincoli reali

- **Ogni interazione = full re-run della pagina Python**. Tienilo a mente: niente UI con 100+ widget interattivi in singola pagina.
- **`st.cache_data` per le query DB lette spesso** (es. lista progetti, lista personaggi).
- **`st.cache_resource` per connessioni** (DB engine, S3 client).
- **Immagini grandi** caricate via `st.image(path)` sono ricaricate ad ogni rerun → usare `use_container_width=True` + cache lato browser.
- **Una pagina con 30 vignette + 3 popover ciascuna** (90 popover) può rallentare. Limitare densità.

## Theme nativo Streamlit (`.streamlit/config.toml`)

```toml
[theme]
primaryColor = "#..."
backgroundColor = "#..."
secondaryBackgroundColor = "#..."
textColor = "#..."
font = "sans serif"  # o "serif" o "monospace" (limitato!)

[server]
port = 8080
address = "0.0.0.0"
maxUploadSize = 10  # MB per file_uploader
```

Il `font` nativo Streamlit è limitato. Per font custom (Google Fonts, ecc.) → usare CSS injection con `@import url(...)`.
