# Streamlit Constraints

Limiti tecnici reali di Streamlit che Replit Agent deve conoscere.

## Versione target
- **Streamlit ≥ 1.40** · **Python 3.13**

## Componenti NON disponibili

- ❌ **Drag & drop** di card: usare "Sposta a pagina X" con dropdown
- ❌ **Modal native bloccanti**: usare `st.expander` con border + state esplicito
- ❌ **Routing client-side**: Streamlit ricarica l'intera pagina ad ogni interazione
- ❌ **Animazioni CSS complesse**: Streamlit ri-renderizza il DOM completamente. Max: hover semplici, transition color/background ≤200ms
- ❌ **Notifiche push / SSE / WebSocket persistenti**
- ❌ **Layout responsive vero**: desktop-first
- ❌ **Componenti React custom** per MVP
- ❌ **Sidebar collapsable programmatica**
- ❌ **Tooltips ricchi multi-riga**

## CSS Injection

```python
def inject_css():
    css = Path("style/custom.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
```

### Selettori utili

```css
[data-testid="stSidebar"] { ... }
.stButton button { ... }
.stButton button[kind="primary"] { ... }
.stTextInput input { ... }
.stTextArea textarea { ... }
.main .block-container { ... }
[data-testid="stHeader"] { display: none; }
footer { display: none; }
```

### Cosa NON fare
- `position: fixed` su elementi che Streamlit re-renderizza
- `transform` su elementi cliccabili
- `overflow: hidden` su contenitori che si espandono

## Pattern consigliati

### Conferma operazione costosa
```python
if st.button("🌙 Genera TUTTO"):
    st.session_state["confirm_gen_all"] = True

if st.session_state.get("confirm_gen_all"):
    with st.container(border=True):
        st.warning(f"Costo: {cost} crediti.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Conferma", type="primary"):
                st.session_state.pop("confirm_gen_all")
                st.rerun()
        with col2:
            if st.button("Annulla"):
                st.session_state.pop("confirm_gen_all")
                st.rerun()
```

### Loading durante operazione
```python
with st.spinner("Generazione in corso..."):
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

## Performance
- **Ogni interazione = full re-run della pagina Python**
- `st.cache_data` per query DB frequenti
- `st.cache_resource` per connessioni (DB engine, S3 client)
- Max ~30 widget interattivi per pagina senza degrado
