# Page Brief — Home / Project list

## Scopo
Mostrare i progetti dell'utente. Punto di partenza per crearne uno nuovo o riprendere un esistente.

## Quando l'utente arriva
- Default dopo login (se onboarding completato)
- Click sul logo SnapToon dalla sidebar
- Dopo creazione/eliminazione progetto

## Stati
| Stato | Descrizione |
|---|---|
| **Empty** | Nessun progetto. Mostra `<EmptyState />` con CTA "+ Nuovo progetto" |
| **Default** | Lista progetti, ordinata per `updated_at DESC` |
| **Creating** | Modale "Nuovo progetto" aperto |
| **Confirming delete** | Modale "Elimina progetto" aperto |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "I tuoi progetti" + bottone "+ Nuovo progetto" (primary, in alto a destra)
2. **Lista progetti**: grid responsive (3 colonne desktop, fallback stack mobile)
3. **(Solo se empty)** `<EmptyState />` centrato

## Componenti chiave
- `<PageHeader />`
- `<EmptyState />`
- Card progetto (può essere componente nuovo `<ProjectCard />`)
- `<ConfirmDialog />` per eliminazione

## Card progetto — struttura
```
┌─────────────────────────────┐
│  [Thumbnail copertina]      │ ← se generata, altrimenti placeholder
│                             │
│  Titolo progetto            │
│  Lunghezza · N pagine       │
│  Creato il DD/MM/YYYY       │
│                             │
│  [📋 Duplica] [🗑] [Apri →] │
└─────────────────────────────┘
```

Comportamento card:
- **Hover**: lieve elevation/sottolineatura titolo (Replit Agent decide effetto)
- **Click sulla card (non sui bottoni)**: equivale a "Apri" → carica progetto attivo → naviga a `📝 Testo`
- **Click Duplica**: apre modale "Nuovo nome" con default `[titolo] — copia`
- **Click Elimina**: apre `<ConfirmDialog />` con doppia conferma (scrivere il nome)
- **Click Apri**: imposta `current_project_slug` in session + naviga a `📝 Testo`

## Interazioni
- **Click "+ Nuovo progetto"** → modale apertura
- **Submit modale** → POST `/api/projects` → success → naviga a `📝 Testo`
- **Click duplica** → modale con default nome → submit → backend duplica → success → toast + lista aggiornata
- **Click elimina** → conferma → backend elimina → toast + lista aggiornata

## Edge case
- **Limite progetti raggiunto al click "+ Nuovo"**: modale errore "Hai raggiunto il limite (X progetti). Elimina un progetto o passa a Pro."
- **Duplica di progetto con vignette generate**: il duplicato eredita TUTTO tranne le vignette generate (vedi `core/project.py:duplicate_project`)
- **Eliminazione del progetto attivo**: backend imposta `current_project_slug = null` → utente atterra su empty state

## Streamlit
- Pagina: `app.py` (è la home post-login)
- Grid: `st.columns(3)` ciclando sui progetti
- Card: `st.container(border=True)` per ogni progetto
- Modali: `st.container` con CSS injection (no vero modal)
- File suggerito: `pages/00_Home.py` o direttamente `app.py`

## Layout
- Padding generoso ai lati (~64px desktop)
- Spaziatura tra card (~24px gap)
- Thumbnail copertina ~16:9 o 2:3 (decide Replit Agent in base a estetica)
- Bottone "+ Nuovo progetto" sempre visibile (anche con molti progetti)

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "Home / Project list".

## Dati richiesti dal backend

```python
# Per ogni progetto:
{
    "slug": str,
    "name": str,
    "length_target": "striscia" | "breve" | "medio" | "lungo",
    "n_pages": int,
    "n_panels_generated": int,
    "n_panels_total": int,
    "cover_thumbnail_url": str | None,
    "created_at": datetime,
    "updated_at": datetime,
}
```
