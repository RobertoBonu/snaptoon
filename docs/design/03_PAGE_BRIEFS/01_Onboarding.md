# Page Brief — Onboarding

## Scopo
Mostrare al primo login un tutorial 3-step + offrire la creazione di un progetto demo precaricato.

## Quando l'utente arriva
- Primo login post-cambio-password
- Flag DB `users.has_seen_onboarding == false`

## Stati
| Stato | Descrizione |
|---|---|
| **Step 1** | Dal testo al fumetto |
| **Step 2** | Stile e personaggi |
| **Step 3** | Genera e impagina |
| **Skipped** | Utente ha chiuso → flag `has_seen_onboarding = true` → Home con empty state |
| **Completed con demo** | Sample project creato → redirect su Testo del demo |

## Sezioni (ordine verticale)
1. **Header overlay**: titolo step + numero step (es. "1 di 3")
2. **Visual / illustrazione**: una semplice illustrazione per ogni step (Replit Agent decide)
3. **Titolo step**: H2 (vedi microcopy)
4. **Description step**: paragrafo di 1-2 righe
5. **Bottoni di navigazione**:
   - Step 1, 2: `← Indietro` (disabled in step 1) + `Continua →`
   - Step 3: `← Indietro` + `Inizia con un progetto demo` (primary)
6. **Skip link in basso**: `Salta tutorial` (sempre presente, piccolo, secondario)

## Componenti chiave
- `<OnboardingOverlay step={1|2|3} />`

## Interazioni
- **Click Continua** → step successivo
- **Click Indietro** → step precedente
- **Click "Inizia con progetto demo"** → backend crea progetto `nome="Demo: La notte del riccio"` precaricato con script + style + cast → flag `has_seen_onboarding = true` → redirect a `📝 Testo` del demo
- **Click "Salta tutorial"** → flag `has_seen_onboarding = true` → resta su Home

## Edge case
- Utente refresh pagina durante onboarding → riprende dallo step 1 (state non persistito)
- Utente chiude tab → riprende al prossimo login (`has_seen_onboarding` ancora false)

## Streamlit
- Implementazione: overlay sopra Home tramite `st.container` con `border=True` e CSS injection per renderlo "modal-like"
- Niente vero modal bloccante (Streamlit non lo supporta)
- File del progetto: `components/ui/onboarding.py`

## Layout
- Overlay centrato che oscura parzialmente lo sfondo
- Larghezza overlay: ~600px
- Altezza fissa (per evitare "salti" tra step)
- Steps indicator in alto (3 dot, quello attivo evidenziato)

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "Onboarding".

## Progetto demo precaricato

Il sample project deve contenere:
- Script con 1 pagina e 4 vignette
- Logline esempio
- 2 personaggi con visual_description e reference già generata (immagini bundled in `assets/demo/`)
- Stile applicato: `Heavy Ink Noir` o similare
- Vignette NON ancora generate (per dare all'utente la soddisfazione di generarle lui)

Questo permette all'utente di arrivare subito su `🖼 Genera` e fare il suo primo "wow" senza dover scrivere niente.
