# UI Components — Componenti riusabili

Lista di componenti che ricorrono in più pagine. Implementati come funzioni Python in `components/ui/*.py`.

---

## 1. `<PageHeader />`
**File**: `components/ui/page_header.py`
- Input: `title`, `subtitle`, `actions: list[Button]`

## 2. `<CreditBadge />`
**File**: `components/ui/credit_badge.py`
- Input: `current`, `total`, `plan_name`
- Cliccabile → naviga a 💳 Account
- Quando `current/total < 0.10` → indicatore "scarso"
- Quando `current == 0` → indicatore "esaurito"

## 3. `<ProjectSelector />`
**File**: `components/ui/project_selector.py`
- Input: `current_project_slug`, `projects: list[Project]`
- Dropdown + link "+ Nuovo progetto"

## 4. `<StyleCard />`
**File**: `components/ui/style_card.py`
- Input: `preset`, `is_selected`
- Card compatta in grid 3-4 colonne
- Footer: "Anteprima" + "Applica"

## 5. `<CharacterCard />`
**File**: `components/ui/character_card.py`
- Input: `character`, `ref_status: "valid"|"corrupted"|"missing"`, `n_variants`
- Card in expander, indicatori status 🟢🟠⚪

## 6. `<PanelCard />`
**File**: `components/ui/panel_card.py`
- Input: `panel`, `vignette_image_path`, `cast_status_icon`, `n_refs`
- Bottoni: Genera/Rigenera · Scena · Prompt · Balloon · Sposta

## 7. `<GridPicker />`
**File**: `components/ui/grid_picker.py`
- Input: `current_grid_id`, `n_panels`, `is_saved`
- 2 colonne: thumbnail gabbia + selectbox 28 gabbie

## 8. `<EmptyState />`
**File**: `components/ui/empty_state.py`
- Input: `icon`, `title`, `description`, `action`
- Centrato, mai sopra il fold

## 9. `<ConfirmDialog />`
**File**: `components/ui/confirm_dialog.py`
- Input: `title`, `body`, `confirm_label`, `confirm_danger`, `requires_type_to_confirm`, `cost_in_credits`
- Simulato con expander + border (Streamlit non ha modali native)
- Bottone secondario "Annulla" sempre presente

## 10. `<Toast />`
- Usare `st.toast()` nativo Streamlit
- Auto-dismiss ~3 secondi
- Per `error` con stack trace → `st.error()` persistente

## 11. `<CostPreview />`
**File**: `components/ui/cost_preview.py`
- Input: `operation_label`, `cost_credits`, `remaining_after`
- Se `remaining_after < 0` → testo rosso + bottone disabilitato

## 12. `<SidebarNav />`
**File**: `components/ui/sidebar_nav.py`
- Input: `current_page`, `is_admin`
- Solo se `is_admin`: aggiunge "🛠 Admin"

## 13. `<LoginForm />`
**File**: `components/ui/login_form.py`
- Form: email + password + bottone "Accedi"
- Errore inline sotto il bottone

## 14. `<OnboardingOverlay />`
**File**: `components/ui/onboarding_overlay.py`
- Input: `step: 1|2|3`, `on_skip`, `on_complete`
- 3 step con bottoni navigazione

## 15. `<AdminUserRow />`
**File**: `components/ui/admin_user_row.py`
- Input: `user: User`
- Azioni: ✏️ Modifica · 🪙 Aggiungi crediti · 🚫 Disabilita

## Naming convention

```python
# components/ui/credit_badge.py
def render_credit_badge(current: int, total: int, plan_name: str):
    ...
```

Funzioni esportate: `def render_<nome>(...)`
Stato componente: prefisso `_ui_` nei `st.session_state`
