# Page Brief — Home / Project list

## Scopo
Mostrare i progetti dell'utente. Punto di partenza per crearne uno nuovo o riprendere un esistente.

## Stati
| Stato | Descrizione |
|---|---|
| **Empty** | Nessun progetto. `<EmptyState />` con CTA "+ Nuovo progetto" |
| **Default** | Lista progetti, ordinata per `updated_at DESC` |
| **Creating** | Modale "Nuovo progetto" aperto |
| **Confirming delete** | Modale "Elimina progetto" aperto |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "I tuoi progetti" + bottone "+ Nuovo progetto" (primary, in alto a destra)
2. **Lista progetti**: grid responsive (3 colonne desktop)
3. **(Solo se empty)** `<EmptyState />` centrato

## Card progetto — struttura
- Thumbnail copertina (placeholder se non generata)
- Titolo progetto
- Caption: N pagine · Stile · Data creazione
- Bottoni: "📋 Duplica" · "🗑 Elimina" · "Apri →"

## Modale "Nuovo progetto"
- Campo: Titolo del fumetto
- Campo: Lunghezza (Striscia / Breve / Medio / Lungo)
- Bottone: "Crea progetto"

## Modale "Elimina progetto" (doppia conferma)
- Warning con nome progetto
- Input: utente deve riscrivere il nome del progetto
- Bottone: "🗑 Elimina definitivamente" (disabled finché testo non corrisponde)

## Componenti chiave
- `<PageHeader />`
- `<EmptyState />`
- `<ConfirmDialog />`

## Streamlit
- File: `pages/1_🏠_Home.py`
