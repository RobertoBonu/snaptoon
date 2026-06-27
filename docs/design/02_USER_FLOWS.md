# User Flows

8 flussi principali. Ognuno definisce: **trigger**, **passi**, **stato finale**, **edge case**.

---

## Flusso 1 — Primo login (beta tester)

**Trigger**: Roberto ha creato l'utente da Admin → ha mandato credenziali via WhatsApp/email manuale.

```
Utente apre snaptoon.art
   ↓
Pagina Login (form: email + password)
   ↓
Submit → backend valida → genera sessione
   ↓
Pagina "Cambia password" obbligatoria (primo login)
   ↓
Cambia password → conferma → atterra su Home
   ↓
Overlay Onboarding (welcome + 3-step tutorial)
   ↓
Click "Inizia con il progetto demo" → Sample project creato → Pagina Testo
   ↓ OPPURE
Click "Salta tutorial" → resta su Home con empty state
```

**Stato finale**: utente loggato, sessione attiva, ha visto l'onboarding (flag `has_seen_onboarding=true` in DB).

**Edge case**:
- Password sbagliata → errore inline
- Account disabilitato → errore "Account non attivo. Contatta admin."
- Email non trovata → errore generico "Credenziali non valide" (no enumeration)

---

## Flusso 2 — Creazione nuovo progetto

**Trigger**: utente clicca "Nuovo progetto" dalla Home.

```
Click "Nuovo progetto"
   ↓
Modale: campo "Titolo" + selettore "Lunghezza"
   ↓
Lunghezza:
   ◯ Striscia (1-2 pagine)
   ◯ Breve (3-6 pagine)
   ◉ Medio (8-16 pagine) [default]
   ◯ Lungo (24+ pagine)
   ↓
Submit → DB crea record `projects` con `length_target`
   ↓
Redirect a 📝 Testo, tab Sorgente
```

**Stato finale**: progetto attivo nuovo, script vuoto, redirect su Testo.

**Edge case**:
- Titolo vuoto → errore inline "Serve un titolo"
- Limite progetti raggiunto (Free Trial = 1, Creator = 5, Pro = ∞) → modale "Hai raggiunto il limite. Elimina un progetto o aggiorna il piano."

---

## Flusso 3 — Dalla sorgente alla sceneggiatura

**Trigger**: utente su 📝 Testo, tab Sorgente, progetto vuoto.

```
Opzione A: Upload .txt
   ↓
Opzione B: Paste testo nel textarea
   ↓
Salva sorgente
   ↓
[Opzionale] Generazione soggetto guidata
   - Lunghezza (deriva da progetto)
   - Genere
   - Tono
   - Click "Genera soggetto" → Claude → soggetto popolato in textarea
   ↓
Click "🪄 Adatta a sceneggiatura"
   ↓
Modale di conferma (mostra costo crediti stimato)
   ↓
Confirm → backend chiama Claude Opus → produce Script JSON
   - logline
   - personaggi
   - pagine (descrizione + dialoghi per ogni vignetta)
   - copertina (descrizione)
   ↓
Tab Sceneggiatura viene popolato
   ↓
Tab Sceneggiatura si attiva
```

**Stato finale**: progetto ha `script` completo, salvato in DB.

**Edge case**:
- File caricato non `.txt` o > 1 MB → errore
- Crediti insufficienti → modale crediti
- Claude API timeout → errore retry-friendly
- Claude restituisce JSON malformato → errore "Adattamento non riuscito, riprova"

---

## Flusso 4 — Setup stile + personaggi

**Trigger**: script pronto, utente naviga su 🎨 Stile.

```
🎨 Stile
   ↓
Default: tab "Sfoglia libreria"
   ↓
Utente filtra per categoria (Fumetto, Illustrazione, Cinema, ecc.)
   ↓
Click preset → Anteprima espansione prompt
   ↓
Click "✨ Applica" → progetto.style_id = preset_id
   ↓
[Opzionale] Tab "Aspetto" → personalizza sfondo + font/colori balloon
   ↓
Tab "Anteprima prompt" → verifica come verrà il prompt finale
   ↓
Navigazione a 👥 Personaggi
   ↓
Default: cast pre-popolato dalla sceneggiatura (Claude)
   ↓
Per ogni personaggio:
   - Modifica visual_description se necessario
   - Click "✨ Genera con AI" → reference image principale (slot 1)
   - [Opzionale] "📚 Reference aggiuntive" → varianti (slot 2-7)
   ↓
Quando tutti i personaggi hanno reference → procedi a 🖼 Genera
```

**Stato finale**: progetto ha style scelto + tutti i character sheets hanno reference image valida.

**Edge case**:
- Reference fallita (rete giù, API key OpenAI invalida) → riprovi pulsante
- Personaggio senza reference → indicatore ⚪ + warning su Genera "X personaggi senza reference"
- Carico file PNG corrotto → errore + bottone "Elimina file corrotto"

---

## Flusso 5 — Generazione vignette

**Trigger**: stile + personaggi pronti, utente su 🖼 Genera.

```
🖼 Genera
   ↓
Header pagina: Provider · Modello · Qualità · Stile · Cache toggle
   ↓
Per ogni pagina del progetto (expander):
   ↓
   Header pagina: thumbnail gabbia + selettore + "Salva gabbia"
   ↓
   Per ogni vignetta (card in colonna):
      ↓
      Stato attuale: ✨ Genera | 🔄 Rigenera
      ↓
      Bottoni: 
         🎬 Scena (popover: cast + formato + distance + angolo + mood)
         👁 Prompt (popover: preview prompt completo)
         🎈 Balloon (apre editor dedicato)
         📦 Sposta vignetta (popover: cambio pagina)
      ↓
Bulk in alto:
   - 🚀 Genera vignette mancanti (N)
   - 🌙 Genera TUTTO (N+M) — fa anche reference mancanti
   ↓
Click su genera singola/bulk → modale conferma costo crediti
   ↓
Confirm → backend chiama OpenAI/Gemini → salva PNG → decrementa crediti
   ↓
Vignetta appare con immagine
```

**Stato finale**: progetto ha vignette generate per N pagine.

**Edge case**:
- Crediti insufficienti → modale bloccante a inizio operazione
- Generazione fallisce mid-batch → continua il bulk, log errori a fine + bottone "Riprova falliti"
- Cache hit → vignetta apparire istante (no decremento crediti)

---

## Flusso 6 — Balloon editor

**Trigger**: utente clicca "🎈 Balloon" su una vignetta che ha dialoghi.

```
Stato switch: pagina Genera → vista Balloon Editor (sostituisce vista normale)
   ↓
Layout:
   - [← Indietro] in alto
   - Canvas con immagine vignetta + balloon overlay (a sinistra)
   - Controlli (a destra):
      - Radio: dialogo da modificare (lista)
      - Slider X/Y per posizione
      - Frecce nudge ±2%
      - Preset rapidi (Alto/Centro/Basso)
      - Forma balloon (5 opzioni)
      - Toggle tail + Slider tail X/Y (se FUMETTO/PENSIERO)
      - Preset tail (4 direzioni)
      - Reset / Reset tutti
   ↓
Modifiche salvate automaticamente al rilascio slider/click
   ↓
Click "← Indietro" → torna a vista Genera
```

**Stato finale**: posizioni e forme balloon salvate per la vignetta.

**Edge case**:
- Vignetta senza dialoghi → bottone "🎈 Balloon" disabilitato
- Cambio dialogo nella radio → mantiene posizione corrente del precedente, mostra del selezionato

---

## Flusso 7 — Impaginazione + export PDF

**Trigger**: vignette generate, utente su 📐 Impagina.

```
📐 Impagina
   ↓
Header: nome progetto + N pagine
   ↓
Per ogni pagina:
   - Anteprima rendered (se esiste) o "Renderizza" button
   - Caption: gabbia + N vignette + N dialoghi
   ↓
Bulk: "📐 Renderizza tutte le pagine"
   ↓
Click → backend rendering pipeline → salva PNG ad alta risoluzione
   ↓
Quando tutte le pagine hanno render valido:
   "📥 Esporta PDF" si abilita
   ↓
Click → backend genera PDF multipagina (copertina inclusa se presente)
   ↓
Download automatico del PDF
```

**Stato finale**: PDF scaricato dall'utente.

**Edge case**:
- Pagina con vignette mancanti → render skipped, warning "Pagina X: N vignette mancanti"
- Render fallisce → errore + bottone "Riprova"
- PDF export non costa crediti (operazione locale)

---

## Flusso 8 — Esaurimento crediti

**Trigger**: utente tenta operazione AI che richiede più crediti di quelli disponibili.

```
Click "Genera vignetta" (richiede 1 credito)
Saldo: 0 crediti
   ↓
Modale bloccante apre:
   - Titolo: "Crediti esauriti"
   - Body: "Hai usato tutti i crediti del tuo piano [PIANO_ATTUALE]."
   - CTA primaria: "Vedi piani"
   - CTA secondaria: "Chiudi"
   ↓
Click "Vedi piani" → naviga a 💳 Crediti & Account
   ↓
Mostra confronto piani (Creator vs Pro) + bottone upgrade
   ↓
[V1.0: il bottone "upgrade" è MOCK e mostra "Contatta admin per upgrade"]
[V1.1: bottone reale → Stripe Checkout]
```

**Stato finale**: utente sa cosa fare per riprendere a lavorare. Admin (Roberto) può aggiungere crediti manualmente dal pannello.

**Edge case**:
- Utente con BYO key (out of scope MVP per nostra scelta) → non applicabile
- Utente in trial con crediti rimasti ma scaduto da 7 giorni → modale diverso "Trial scaduto"

---

## Flussi NON in scope MVP (notati per dopo)

- Condivisione progetto in sola lettura
- Inviti team
- Pubblicazione progetti pubblici
- Esportazione singole vignette
- Versioning / cronologia modifiche
- Restore progetto eliminato
- Reset password via email (in MVP: contatta admin)
