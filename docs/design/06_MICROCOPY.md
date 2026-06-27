# Microcopy funzionale

Testi obbligatori che compaiono nell'app.

## Principi
- Italiano formale ma asciutto. Mai paternalistico.
- Mai più di 2 righe per microcopy informativi.
- Imperativo per le azioni dell'utente.
- Numeri sempre in cifre ("1 progetto" non "un progetto").
- Niente esclamativi, salvo "Crediti esauriti!".

## Bottoni principali (CTA)

| Contesto | Testo |
|---|---|
| Salva | `💾 Salva` |
| Annulla | `Annulla` |
| Conferma azione distruttiva | `🗑 Elimina definitivamente` |
| Genera con AI | `✨ Genera` |
| Rigenera | `🔄 Rigenera` |
| Carica file | `📤 Carica file` |
| Scarica | `📥 Scarica` |
| Indietro | `← Indietro` |
| Avanti | `Continua →` |
| Login | `Accedi` |
| Logout | `🚪 Esci` |
| Crea nuovo progetto | `+ Nuovo progetto` |

## Login

| Elemento | Testo |
|---|---|
| H1 | `SnapToon` |
| Sottotitolo | `Dall'idea al fumetto, in uno snap.` |
| Errore credenziali | `Credenziali non valide.` |
| Errore account disabilitato | `Questo account non è attivo. Contatta l'amministratore.` |
| Sessione scaduta | `La sessione è scaduta. Accedi di nuovo.` |
| Password dimenticata | `Hai dimenticato la password? Contatta l'amministratore.` |

## Cambio password obbligatorio

| Elemento | Testo |
|---|---|
| H1 | `Imposta la tua password` |
| Description | `Hai effettuato il primo accesso. Imposta una password personale per proseguire.` |
| Errore non coincidono | `Le due password non coincidono.` |
| Errore troppo corta | `La password deve essere lunga almeno 8 caratteri.` |
| Bottone | `Aggiorna password` |

## Onboarding

| Step | Titolo | Description |
|---|---|---|
| 1 | `Dal testo al fumetto` | `Carica un racconto, un'idea o anche solo una scena. La sceneggiatura la scriviamo insieme.` |
| 2 | `Stile e personaggi` | `Scegli uno stile visivo. Crea il cast del fumetto. Le immagini di riferimento garantiscono coerenza.` |
| 3 | `Genera e impagina` | `Le vignette vengono generate una per una. Le impagini su pagina e le esporti in PDF.` |
| Bottone fine | `Inizia con un progetto demo` | |
| Skip | `Salta tutorial` | |

## Home / Project list

| Elemento | Testo |
|---|---|
| H1 | `I tuoi progetti` |
| Empty state titolo | `Non hai ancora progetti` |
| Empty state CTA | `+ Nuovo progetto` |
| Bottone duplica | `📋 Duplica` |
| Bottone elimina | `🗑 Elimina` |
| Bottone apri | `Apri →` |

### Modale "Nuovo progetto"
| Elemento | Testo |
|---|---|
| Titolo modale | `Nuovo progetto` |
| Label titolo | `Titolo del fumetto` |
| Placeholder | `Es. La notte del riccio` |
| Lunghezza: striscia | `Striscia (1-2 pagine)` |
| Lunghezza: breve | `Breve (3-6 pagine)` |
| Lunghezza: medio | `Medio (8-16 pagine)` |
| Lunghezza: lungo | `Lungo (24+ pagine)` |
| Errore titolo vuoto | `Inserisci un titolo.` |
| Bottone crea | `Crea progetto` |

### Modale "Elimina progetto"
| Elemento | Testo |
|---|---|
| Titolo | `Elimina progetto` |
| Label conferma | `Per confermare, scrivi il nome del progetto:` |
| Bottone | `🗑 Elimina definitivamente` |
| Toast post-eliminazione | `Progetto eliminato.` |

## 🎨 Stile

| Elemento | Testo |
|---|---|
| H1 | `Stile visivo` |
| Tab 1 | `Selezione` |
| Tab 2 | `Sfoglia libreria` |
| Tab 3 | `Personalizza` |
| Tab 4 | `Aspetto pagina` |
| Tab 5 | `Anteprima prompt` |
| Bottone applica | `✨ Applica «[nome preset]»` |
| Reset aspetto | `↩️ Ripristina aspetto predefinito` |

## 👥 Personaggi

| Elemento | Testo |
|---|---|
| H1 | `Personaggi` |
| Stato globale | `[X]/[Y] personaggi hanno un'immagine di riferimento` |
| Status valido | `🟢 Reference valida` |
| Status corrotto | `🟠 File corrotto. Carica un altro file o rigenera con AI.` |
| Status mancante | `⚪ Nessuna reference` |
| Bottone genera bulk | `🚀 Genera reference per i [N] mancanti` |
| Bottone upload | `📤 Carica file (PNG, JPG, max 4MB)` |

## 🖼 Genera

| Elemento | Testo |
|---|---|
| H1 | `Genera vignette` |
| Stato globale | `[X]/[Y] vignette generate` |
| Warning ref mancanti | `⚠️ [N] personaggi senza reference. Vai su Personaggi per generarle prima.` |
| Bottone vignette mancanti | `🚀 Genera vignette mancanti ([N])` |
| Bottone tutto | `🌙 Genera TUTTO ([N+M])` |
| Vignetta empty | `— non ancora generata —` |
| Popover scena | `🎬 Scena` |
| Popover prompt | `👁 Prompt` |
| Bottone balloon | `🎈 Balloon` |

### Modale crediti finiti
| Elemento | Testo |
|---|---|
| Titolo | `Crediti esauriti` |
| Body | `Hai usato tutti i crediti del tuo piano [PIANO_ATTUALE]. Per continuare a generare, passa a un piano superiore o contatta l'amministratore.` |
| CTA primaria | `Vedi piani` |
| CTA secondaria | `Chiudi` |

## 📐 Impagina

| Elemento | Testo |
|---|---|
| H1 | `Impagina` |
| Bottone bulk render | `📐 Renderizza tutte le pagine` |
| Bottone export PDF | `📥 Esporta PDF` |
| Toast PDF | `PDF esportato.` |

## 💳 Crediti & Account

| Elemento | Testo |
|---|---|
| H1 | `Account e crediti` |
| Bottone cambia password | `🔑 Cambia password` |
| Bottone logout | `🚪 Esci` |
| MVP rinnovo | `Contatta l'amministratore per gestire l'abbonamento.` |
| Empty storico | `Nessuna operazione ancora.` |

## 🛠 Admin

| Elemento | Testo |
|---|---|
| H1 | `Admin` |
| Subtitle | `Solo per amministratori.` |
| Bottone nuovo utente | `+ Nuovo utente` |
| Toast creato | `Utente creato. Manda all'utente email e password temporanea fuori dall'app.` |
| Bottone disabilita | `🚫 Disabilita account` |
| Bottone riabilita | `✓ Riabilita account` |

## Stati di errore globali

| Errore | Testo |
|---|---|
| 404 | `Pagina non trovata.` |
| Sessione scaduta | `La sessione è scaduta. Accedi di nuovo.` |
| Errore di rete | `Errore di connessione. Riprova.` |
| Errore generico | `Si è verificato un errore. Se persiste, contatta l'amministratore.` |
