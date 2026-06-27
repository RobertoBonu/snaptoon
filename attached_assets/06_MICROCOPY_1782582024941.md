# Microcopy funzionale

Testi obbligatori che compaiono nell'app. Replit Agent può rifinire il **tono** (più asciutto, più caldo) ma deve mantenere il **contenuto informativo**.

## Principi

- Italiano formale ma asciutto. Mai paternalistico. Mai "Ehi!"/"Ciao!" come opener.
- Mai più di 2 righe per microcopy informativi.
- Imperativo per le azioni dell'utente ("Carica un testo", "Genera la vignetta").
- "Tu" implicito, mai esplicito ("Vuoi rinominare?" non "Tu vuoi rinominare?").
- Numeri sempre in cifre ("1 progetto" non "un progetto").
- Niente esclamativi, salvo "Crediti esauriti.".

## Bottoni principali (CTA)

| Contesto | Testo |
|---|---|
| Primary action per pagina | (dipende dalla pagina, vedi Page Briefs) |
| Salva | `💾 Salva` |
| Annulla | `Annulla` (senza icona) |
| Conferma azione distruttiva | `🗑 Elimina definitivamente` |
| Conferma azione costosa | `Conferma e procedi` |
| Genera con AI | `✨ Genera` |
| Rigenera | `🔄 Rigenera` |
| Carica file | `📤 Carica file` |
| Scarica | `📥 Scarica` |
| Indietro | `← Indietro` |
| Avanti / Next step | `Continua →` |
| Login | `Accedi` |
| Logout | `🚪 Esci` |
| Cambia password | `Aggiorna password` |
| Crea nuovo progetto | `+ Nuovo progetto` |

## Login

| Elemento | Testo |
|---|---|
| H1 | `SnapToon` |
| Sottotitolo | `Dall'idea al fumetto, in uno snap.` |
| Label email | `Email` |
| Label password | `Password` |
| Bottone | `Accedi` |
| Errore credenziali | `Credenziali non valide.` |
| Errore account disabilitato | `Questo account non è attivo. Contatta l'amministratore.` |
| Sessione scaduta | `La sessione è scaduta. Accedi di nuovo.` |
| Password dimenticata | `Hai dimenticato la password? Contatta l'amministratore.` (testo plain, non link) |

## Cambio password obbligatorio (primo login)

| Elemento | Testo |
|---|---|
| H1 | `Imposta la tua password` |
| Description | `Hai effettuato il primo accesso. Imposta una password personale per proseguire.` |
| Label password nuova | `Nuova password` |
| Label conferma | `Conferma nuova password` |
| Errore non coincidono | `Le due password non coincidono.` |
| Errore troppo corta | `La password deve essere lunga almeno 8 caratteri.` |
| Bottone | `Aggiorna password` |
| Success | `Password aggiornata.` |

## Onboarding

| Step | Titolo | Description |
|---|---|---|
| 1 | `Dal testo al fumetto` | `Carica un racconto, un'idea o anche solo una scena. La sceneggiatura la scriviamo insieme.` |
| 2 | `Stile e personaggi` | `Scegli uno stile visivo. Crea il cast del fumetto. Le immagini di riferimento garantiscono coerenza.` |
| 3 | `Genera e impagina` | `Le vignette vengono generate una per una. Le impagini su pagina e le esporti in PDF.` |
| Bottone fine | `Inizia con un progetto demo` | (precarica un progetto di esempio) |
| Skip | `Salta tutorial` | |

## Home / Project list

| Elemento | Testo |
|---|---|
| H1 | `I tuoi progetti` |
| Subtitle se nessun progetto | `Crea il primo per iniziare.` |
| Empty state titolo | `Non hai ancora progetti` |
| Empty state CTA | `+ Nuovo progetto` |
| Card progetto: data | `Creato il [DD/MM/YYYY]` |
| Bottone duplica | `📋 Duplica` |
| Bottone elimina | `🗑 Elimina` |
| Bottone apri | `Apri →` |

### Modale "Nuovo progetto"

| Elemento | Testo |
|---|---|
| Titolo modale | `Nuovo progetto` |
| Label titolo | `Titolo del fumetto` |
| Placeholder | `Es. La notte del riccio` |
| Label lunghezza | `Lunghezza` |
| Lunghezza: striscia | `Striscia (1-2 pagine)` |
| Lunghezza: breve | `Breve (3-6 pagine)` |
| Lunghezza: medio | `Medio (8-16 pagine)` |
| Lunghezza: lungo | `Lungo (24+ pagine)` |
| Errore titolo vuoto | `Inserisci un titolo.` |
| Errore limite progetti | `Hai raggiunto il limite del tuo piano. Elimina un progetto o passa a un piano superiore.` |
| Bottone crea | `Crea progetto` |

### Modale "Elimina progetto" (doppia conferma)

| Elemento | Testo |
|---|---|
| Titolo | `Elimina progetto` |
| Warning | `Stai per eliminare il progetto «[NOME]». Tutti i dati verranno persi: sceneggiatura, personaggi, vignette generate, pagine impaginate, export PDF.` |
| Subtitle | `Questa operazione non si può annullare. Le chiamate AI già pagate non vengono rimborsate.` |
| Label conferma | `Per confermare, scrivi il nome del progetto:` |
| Bottone (disabled finché matching) | `🗑 Elimina definitivamente` |
| Toast post-eliminazione | `Progetto eliminato.` |

## 📝 Testo

| Elemento | Testo |
|---|---|
| H1 | `Testo` |
| Tab 1 | `Sorgente` |
| Tab 2 | `Sceneggiatura` |

### Tab Sorgente
| Elemento | Testo |
|---|---|
| Label upload | `Carica un file di testo (.txt, max 1 MB)` |
| O paste | `Oppure incolla il testo` |
| Placeholder paste | `Incolla qui il tuo testo...` |
| Bottone salva | `💾 Salva sorgente` |
| Sezione soggetto | `Generazione soggetto (opzionale)` |
| Label genere | `Genere` |
| Label tono | `Tono` |
| Bottone genera soggetto | `🧩 Genera soggetto` |
| Bottone adatta script | `🪄 Adatta a sceneggiatura` |
| Cost preview | `Costa X crediti. Ti resteranno Y.` |
| Empty state sceneggiatura | `Nessuna sceneggiatura ancora. Carica un testo e clicca «Adatta a sceneggiatura».` |

### Tab Sceneggiatura
| Elemento | Testo |
|---|---|
| Section logline | `Logline` |
| Section personaggi | `Personaggi del fumetto` |
| Bottone aggiungi personaggio | `+ Aggiungi personaggio` |
| Section pagine | `Pagine` |
| Bottone aggiungi pagina | `+ Aggiungi pagina` |
| Label descrizione vignetta | `Cosa succede` |
| Label tipo dialogo | `Tipo` |
| Label speaker | `Chi parla (lascia vuoto se non applicabile)` |
| Label testo dialogo | `Testo` |
| Tipo FUMETTO | `Fumetto (parlato)` |
| Tipo PENSIERO | `Pensiero` |
| Tipo DIDASCALIA | `Didascalia (narrante)` |
| Tipo SFX | `SFX (effetto sonoro)` |
| Bottone aggiungi dialogo | `+ Aggiungi dialogo` |

## 🎨 Stile

| Elemento | Testo |
|---|---|
| H1 | `Stile visivo` |
| Tab 1 | `Selezione` |
| Tab 2 | `Sfoglia libreria` |
| Tab 3 | `Personalizza` |
| Tab 4 | `Aspetto pagina` |
| Tab 5 | `Anteprima prompt` |
| Empty state nessuno stile | `Nessuno stile selezionato. Scegli un preset dalla libreria o creane uno personalizzato.` |
| Categoria Personali | `🖌 I miei stili` |
| Categoria Fumetto | `Fumetto` |
| Categoria Illustrazione | `Illustrazione` |
| Categoria Fotografia | `Fotografia` |
| Categoria Cinema | `Cinema` |
| Categoria Kids | `Kids` |
| Categoria Fot. d'autore | `Fotografia d'autore` |
| Bottone applica | `✨ Applica «[nome preset]»` |
| Bottone anteprima | `👁 Vedi prompt completo` |
| Stile attivo (badge) | `Attivo` |

### Tab Aspetto pagina
| Elemento | Testo |
|---|---|
| Section sfondo | `Sfondo pagina` |
| Section balloon | `Balloon (parlato)` |
| Section caption | `Didascalie` |
| Section sfx | `Effetti sonori (SFX)` |
| Label font | `Font` |
| Label dimensione | `Dimensione (pt)` |
| Label colore testo | `Colore testo` |
| Label colore contorno | `Colore contorno` |
| Label colore fondo | `Colore di fondo` |
| Reset aspetto | `↩️ Ripristina aspetto predefinito` |

## 👥 Personaggi

| Elemento | Testo |
|---|---|
| H1 | `Personaggi` |
| Stato globale | `[X]/[Y] personaggi hanno un'immagine di riferimento` |
| Empty state | `Non ci sono ancora personaggi. Importali dalla sceneggiatura sopra, o aggiungili manualmente in fondo.` |
| Status valido | `🟢 Reference valida` |
| Status corrotto | `🟠 File corrotto. Carica un altro file o rigenera con AI.` |
| Status mancante | `⚪ Nessuna reference` |
| Bottone genera bulk | `🚀 Genera reference per i [N] mancanti` |
| Bottone genera singolo (no ref) | `✨ Genera con AI` |
| Bottone genera singolo (con ref) | `🔄 Rigenera con AI` |
| Bottone upload | `📤 Carica file (PNG, JPG, max 4MB)` |
| Bottone elimina corrotto | `🗑 Elimina file corrotto` |
| Section descrizione | `Descrizione visiva` |
| Placeholder descrizione | `Es. uomo sui 40, barba grigia corta, occhi nocciola, giacca di pelle marrone consumata` |
| Reference aggiuntive | `📚 Reference aggiuntive ([N]/7)` |
| Variante kind: profile | `Profilo` |
| Variante kind: three_quarter | `Tre quarti` |
| Variante kind: full_body | `Figura intera` |
| Variante kind: smiling | `Sorridente` |
| Variante kind: dramatic | `Espressione drammatica` |
| Variante kind: back | `Di spalle` |
| Mini cast manager | `🗂 Archivio personaggi (globale)` |

## 🖼 Genera

| Elemento | Testo |
|---|---|
| H1 | `Genera vignette` |
| Stato globale | `[X]/[Y] vignette generate` |
| Warning ref mancanti | `⚠️ [N] personaggi senza reference. Vai su Personaggi per generarle prima.` |
| Bottone vignette mancanti | `🚀 Genera vignette mancanti ([N])` |
| Bottone tutto | `🌙 Genera TUTTO ([N+M])` |
| Tooltip tutto | `Notturno: prima reference mancanti, poi vignette mancanti. Continua anche in caso di errori.` |
| Empty state nessuna pagina | `Nessuna pagina ancora. Vai su Testo per creare la sceneggiatura.` |
| Page expander | `📖 Pagina [N] — [M] vignette` |
| Bottone aggiungi pagina | `➕ Pagina dopo` |
| Bottone elimina pagina vuota | `🗑 Elimina pagina` |
| Tooltip pagina non vuota | `Sposta o elimina prima tutte le vignette per poter rimuovere la pagina.` |
| Vignetta header | `Vignetta [N]` |
| Vignetta empty | `— non ancora generata —` |
| Popover scena | `🎬 Scena` |
| Popover prompt | `👁 Prompt` |
| Bottone balloon | `🎈 Balloon` |
| Popover sposta | `📦 Sposta vignetta` |
| Sezione gabbia | `Gabbia pagina [N]` |
| Bottone salva gabbia | `💾 Salva gabbia` |
| Bottone adatta formati | `📐 Adatta formati vignette` |

### Popover Scena
| Elemento | Testo |
|---|---|
| Header | `Parametri di regia di questa vignetta` |
| Section cast | `👥 Personaggi nella scena` |
| Section formato | `Formato vignetta` |
| Section distanza | `Distanza inquadratura` |
| Section angolo | `Angolo / inquadratura speciale` |
| Section tono | `Tono emotivo` |
| Bottone salva | `💾 Salva scena` |
| Bottone reset | `↩️ Reset scena` |
| Bottone auto cast | `🔍 Auto-rileva da descrizione ([N])` |

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
| Empty state | `Nessuna pagina ancora. Vai su Testo per creare la sceneggiatura, poi su Genera.` |
| Bottone bulk render | `📐 Renderizza tutte le pagine` |
| Bottone export PDF | `📥 Esporta PDF` |
| Tooltip PDF disabilitato | `Genera almeno una pagina renderizzata.` |
| Page caption gabbia | `Gabbia: [grid_id] · [N] vignette · [M] dialoghi` |
| Toast PDF | `PDF esportato.` |

## 💳 Crediti & Account

| Elemento | Testo |
|---|---|
| H1 | `Account e crediti` |
| Section saldo | `Saldo crediti` |
| Metric saldo | `[X]/[Y]` |
| Caption saldo | `Crediti rimasti questo mese` |
| Section piano | `Piano attivo` |
| Metric piano | `[NOME_PIANO]` |
| Caption rinnovo | `Si rinnova il [DD/MM/YYYY]` (V1.1) |
| MVP rinnovo | `Contatta l'amministratore per gestire l'abbonamento.` |
| Section storico | `Storico operazioni` |
| Tabella header: data | `Data` |
| Tabella header: operazione | `Operazione` |
| Tabella header: costo | `Costo` |
| Empty storico | `Nessuna operazione ancora.` |
| Section settings | `Impostazioni personali` |
| Label email (readonly) | `Email` |
| Bottone cambia password | `🔑 Cambia password` |
| Bottone logout | `🚪 Esci` |

## 🛠 Admin

| Elemento | Testo |
|---|---|
| H1 | `Admin` |
| Subtitle | `Solo per amministratori.` |
| Section utenti | `Utenti registrati` |
| Bottone nuovo utente | `+ Nuovo utente` |
| Section nuovo utente | `Crea nuovo utente` |
| Label email | `Email` |
| Label password temp | `Password temporanea (l'utente la cambierà al primo login)` |
| Label piano iniziale | `Piano iniziale` |
| Label crediti iniziali | `Crediti iniziali` |
| Bottone crea | `Crea account` |
| Toast creato | `Utente creato. Manda all'utente email e password temporanea fuori dall'app.` |
| Bottone aggiungi crediti | `🪙 Aggiungi crediti` |
| Bottone disabilita | `🚫 Disabilita account` |
| Bottone riabilita | `✓ Riabilita account` |
| Section log | `Log operazioni globali (ultime 100)` |

## Stati di errore globali

| Errore | Testo |
|---|---|
| 404 | `Pagina non trovata.` |
| Sessione scaduta | `La sessione è scaduta. Accedi di nuovo.` |
| Errore di rete | `Errore di connessione. Riprova.` |
| API key fallita | `Servizio temporaneamente non disponibile. Riprova tra qualche minuto.` |
| Errore generico | `Si è verificato un errore. Se persiste, contatta l'amministratore.` |
