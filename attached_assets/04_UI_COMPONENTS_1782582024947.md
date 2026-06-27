# UI Components — Componenti riusabili

Lista di componenti che ricorrono in più pagine. Replit Agent li implementa come funzioni Python in `components/ui/*.py`, riutilizzabili.

---

## 1. `<PageHeader />`

**Dove**: in cima a ogni pagina di lavoro.

**Input**:
- `title: str` (es. "Genera vignette")
- `subtitle: str | None` (es. "Progetto: La notte del riccio · 12 vignette")
- `actions: list[Button] = []` (azioni globali della pagina, max 3)

**Esempio uso**:
```python
PageHeader(
    title="Genera vignette",
    subtitle=f"Progetto: {project.name} · {n_vignettes} vignette",
    actions=[
        Button("🚀 Genera mancanti", primary=False),
        Button("🌙 Genera TUTTO", primary=True),
    ],
)
```

**Stati**: solo "default".

---

## 2. `<CreditBadge />`

**Dove**: sidebar permanente.

**Input**:
- `current: int`
- `total: int`
- `plan_name: str` (es. "Creator")

**Comportamento**:
- Mostra `current / total` con micro-barra di progresso
- Cliccabile → naviga a `💳 Crediti & Account`
- Quando `current / total < 0.10` → indicatore visivo di "scarso" (Replit Agent decide come)
- Quando `current == 0` → indicatore visivo di "esaurito"

---

## 3. `<ProjectSelector />`

**Dove**: sidebar permanente.

**Input**:
- `current_project_slug: str | None`
- `projects: list[Project]`

**Comportamento**:
- Dropdown con tutti i progetti dell'utente
- Sopra il dropdown: label "Progetto attivo"
- Sotto il dropdown: link piccolo "+ Nuovo progetto" → modale creazione

---

## 4. `<StyleCard />`

**Dove**: pagina Stile, tab "Sfoglia libreria" (in grid).

**Input**:
- `preset: StylePreset` (id, label, category, is_handmade, is_custom, expansion)
- `is_selected: bool`

**Comportamento**:
- Card visualmente compatta (in grid 3-4 colonne)
- Header: label + badge categoria + eventuale icona 🖌 se custom
- Body: prime 2 righe di `expansion` con fade in basso
- Footer: bottone "Anteprima" + bottone "Applica" (primary se non selected)
- Card selezionata: indicatore visivo persistente

---

## 5. `<CharacterCard />`

**Dove**: pagina Personaggi.

**Input**:
- `character: CharacterSheet` (name, visual_description)
- `ref_status: "valid" | "corrupted" | "missing"`
- `n_variants: int` (slot 2-7)

**Comportamento**:
- Card in expander (default chiuso se ref valida, aperto altrimenti)
- Header: nome + indicatore status (🟢/🟠/⚪)
- Body in colonne:
  - Sinistra: thumbnail reference image principale
  - Destra: form editing visual_description + bottoni genera/upload
- Sezione opzionale: "📚 Reference aggiuntive (N/7)"

---

## 6. `<PanelCard />`

**Dove**: pagina Genera, ogni vignetta nella griglia.

**Input**:
- `panel: Panel` (number, description, dialogues, aspect_ratio, ...)
- `vignette_image_path: str | None`
- `cast_status_icon: "👥" | "🔗" | None`
- `n_refs: int`

**Comportamento**:
- Header: "Vignetta N"
- Body:
  - Immagine vignetta o placeholder "*— non ancora generata —*"
  - Caption: descrizione (max 120 char + ...)
  - Caption: cast attivo (icona + nomi)
  - Caption: scena attiva (📐 🎥 🎞 🎭 — solo emoji presenti)
- Bottoni in 2 righe:
  - Riga 1: "✨ Genera" / "🔄 Rigenera" + popover "🎬 Scena"
  - Riga 2: popover "👁 Prompt" + bottone "🎈 Balloon"
  - Riga 3 (separata): popover "📦 Sposta vignetta"

---

## 7. `<GridPicker />`

**Dove**: pagina Genera, header di ogni expander pagina.

**Input**:
- `current_grid_id: str`
- `n_panels: int`
- `is_saved: bool`

**Comportamento**:
- Layout in 2 colonne:
  - Sinistra: thumbnail della gabbia corrente (140×198 px) con caption
  - Destra: selectbox con tutte le 28 gabbie (⭐ in cima quelle con capienza esatta)
- Sotto: warning capienza mismatch + bottoni "💾 Salva gabbia" e "📐 Adatta formati vignette"

---

## 8. `<EmptyState />`

**Dove**: ovunque ci sia una lista vuota o uno stato "non hai ancora X".

**Input**:
- `icon: str` (emoji o icona)
- `title: str` (es. "Non hai ancora progetti")
- `description: str | None` (es. "Crea il tuo primo progetto per iniziare")
- `action: Button | None` (es. "+ Nuovo progetto")

**Comportamento**:
- Centrato sulla pagina
- Icona grande
- Titolo + description sotto
- CTA primaria sotto
- Mai sopra il fold

---

## 9. `<ConfirmDialog />`

**Dove**: prima di operazioni distruttive o costose.

**Input**:
- `title: str` (es. "Elimina progetto")
- `body: str` (es. "Tutti i dati verranno persi. Operazione irreversibile.")
- `confirm_label: str` (es. "🗑 Elimina definitivamente")
- `confirm_danger: bool` (se true, il bottone è rosso/critico)
- `requires_type_to_confirm: str | None` (es. "snaptoon" — utente deve scrivere)
- `cost_in_credits: int | None` (es. 1 → mostra "Costa 1 credito")

**Comportamento**:
- Modale o expander (Streamlit non ha modali native, usare expander con border)
- Mai chiudibile cliccando fuori
- Bottone secondario sempre presente "Annulla"

---

## 10. `<Toast />`

**Dove**: dopo azioni riuscite (salvataggio, generazione completata).

**Input**:
- `kind: "success" | "info" | "warning" | "error"`
- `message: str`

**Comportamento**:
- Usare `st.toast()` nativo Streamlit
- Auto-dismiss dopo ~3 secondi
- Per `error` con stack trace → no toast ma `st.error()` persistente

---

## 11. `<CostPreview />`

**Dove**: prima di operazioni AI (Genera vignetta, Adatta sceneggiatura, ecc.).

**Input**:
- `operation_label: str` (es. "Genera 24 vignette mancanti")
- `cost_credits: int`
- `remaining_after: int`

**Comportamento**:
- Caption inline sopra il bottone azione
- Formato: "Costa X crediti. Ti resteranno Y."
- Se `remaining_after < 0` → testo rosso + bottone disabilitato

---

## 12. `<SidebarNav />`

**Dove**: sidebar permanente, sezione navigazione.

**Input**:
- `current_page: str` (es. "Genera")
- `is_admin: bool`

**Comportamento**:
- Lista di link verso le 5 pagine di lavoro
- Visivamente: la pagina corrente è evidenziata
- Solo se `is_admin == True`: aggiunge "🛠 Admin" in fondo

---

## 13. `<LoginForm />`

**Dove**: pagina Login.

**Input**:
- nessuno (state interno)

**Comportamento**:
- Form: email + password + bottone "Accedi"
- Errore inline sotto il bottone se credenziali invalide
- Link disabilitato: "Password dimenticata? Contatta l'admin"
- Centrato verticalmente e orizzontalmente

---

## 14. `<OnboardingOverlay />`

**Dove**: sopra Home, al primo login.

**Input**:
- `step: 1 | 2 | 3`
- `on_skip: callable`
- `on_complete: callable`

**Comportamento**:
- 3 step:
  1. "Carica un testo, lo trasformiamo in fumetto"
  2. "Scegli stile e crea i personaggi"
  3. "Genera le vignette e impagina"
- Bottone "Salta tutorial" sempre disponibile in basso
- Bottone "Inizia con progetto demo" alla fine

---

## 15. `<AdminUserRow />`

**Dove**: pagina Admin, lista utenti.

**Input**:
- `user: User` (id, email, plan, credits_remaining, created_at, is_active)

**Comportamento**:
- Riga in tabella con:
  - Email
  - Piano attivo (badge)
  - Crediti rimasti / totali del piano
  - Data registrazione
  - Stato (attivo/disabilitato)
  - Azioni: ✏️ Modifica · 🪙 Aggiungi crediti · 🚫 Disabilita

---

## Pattern di layout ricorrenti

### Sezione "header + corpo + azioni"
```
[Header pagina]
[Subtitle/contesto]
─────────────────
[Contenuto principale]
─────────────────
[Azioni di pagina]
```

### Sezione "lista con bulk action in alto"
```
[Header con stato totale: X/Y]
[Progress bar]
[Bottoni bulk action]
─────────────────
[Lista elementi]
```

### Sezione "form in form"
```
[Form padre]
   [Form figlio 1]
   [Form figlio 2]
[Bottone submit padre]
```
Streamlit non permette form annidate. Usare expander per form figli.

---

## Naming convention

- Componenti UI: `components/ui/<snake_case>.py`
- Funzioni esportate: `def render_<nome>(...)`
- Stato componente: prefisso `_ui_` nei `st.session_state`

Esempio:
```python
# components/ui/credit_badge.py
def render_credit_badge(current: int, total: int, plan_name: str):
    ...
```
