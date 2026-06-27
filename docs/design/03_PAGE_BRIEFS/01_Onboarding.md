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
| **Skipped** | Flag `has_seen_onboarding = true` → Home con empty state |
| **Completed con demo** | Sample project creato → redirect su Testo del demo |

## Sezioni (ordine verticale)
1. **Header overlay**: titolo step + numero step (es. "1 di 3")
2. **Visual / illustrazione**: una semplice illustrazione per ogni step
3. **Titolo step**: H2
4. **Description step**: paragrafo di 1-2 righe
5. **Bottoni di navigazione**: Indietro / Continua (Step 3: "Inizia con un progetto demo")
6. **Skip link in basso**: `Salta tutorial` (sempre presente)

## Microcopy step
| Step | Titolo | Description |
|---|---|---|
| 1 | Dal testo al fumetto | Carica un racconto, un'idea o anche solo una scena. La sceneggiatura la scriviamo insieme. |
| 2 | Stile e personaggi | Scegli uno stile visivo. Crea il cast del fumetto. |
| 3 | Genera e impagina | Le vignette vengono generate una per una. Le impagini su pagina e le esporti in PDF. |

## Componenti chiave
- `<OnboardingOverlay step={1|2|3} />`
