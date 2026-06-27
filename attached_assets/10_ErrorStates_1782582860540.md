# Page Brief — Stati di errore globali

Stati gestiti centralmente. Replit Agent definisce l'estetica di banner/modali; il comportamento è specificato qui.

## Tipi di errore

| Categoria | Quando | Visualizzazione |
|---|---|---|
| **404** | URL inesistente / progetto non più disponibile | Pagina dedicata con CTA "Torna alla Home" |
| **Sessione scaduta** | Token sessione expired | Redirect Login con toast persistente |
| **Crediti finiti** | Operazione richiede crediti > saldo | Modale bloccante sulla pagina corrente |
| **Errore di rete / API** | Fetch fallisce, OpenAI/Anthropic timeout | Banner persistente sulla pagina con bottone "Riprova" |
| **Errore generico** | Eccezione non gestita | Banner persistente con messaggio + tracking ID |

## 404

### Layout
- Centrato verticalmente
- Icona/emoji grande
- Titolo H1: "Pagina non trovata."
- Description: "Il link che hai seguito non porta da nessuna parte, oppure il progetto è stato eliminato."
- CTA primary: "Torna alla home"
- Sidebar normale (non nascosta)

### Trigger
- URL pages non riconosciuto
- Progetto eliminato in tab parallela
- ID progetto inesistente nei params

## Sessione scaduta

### Layout
- Redirect immediato a `/login`
- Toast persistente in cima alla pagina Login: "La sessione è scaduta. Accedi di nuovo."

### Trigger
- Token scaduto (TTL: 7 giorni rolling)
- Backend invalida sessione (es. admin disabilita utente)

## Crediti finiti

### Layout (modale)
- Overlay parziale (no Streamlit native, simulato con CSS)
- Titolo: "Crediti esauriti"
- Body: `"Hai usato tutti i crediti del tuo piano {plan_name}. Per continuare a generare, passa a un piano superiore o contatta l'amministratore."`
- CTA primary: "Vedi piani" → naviga a `💳 Account`
- CTA secondary: "Chiudi" → chiude modale, resta su pagina corrente

### Trigger
- Pre-flight check su ogni operazione che consuma crediti
- Risposta backend `402 Payment Required` con campo `kind: "insufficient_credits"`

### Bloccante
- L'utente NON può procedere con l'operazione che ha richiesto crediti
- Può comunque navigare e usare l'app per altre azioni (modifica script, ecc.)

## Errore di rete / API

### Layout (banner)
- Banner sticky in cima alla pagina, colore warning
- Body: "Errore di connessione con il servizio AI. Riprova tra qualche istante."
- Bottone "Riprova" inline
- Auto-dismiss dopo successo

### Trigger
- OpenAI/Anthropic API restituisce 5xx
- Timeout (>120s)
- Errore di rete locale

### Comportamento
- L'operazione fallita rimane "in stallo" — vignetta resta "non generata"
- Bottone Riprova rilancia la stessa operazione

## Errore generico

### Layout (banner)
- Banner sticky in cima alla pagina, colore error
- Body: `"Si è verificato un errore. Se persiste, contatta l'amministratore. (ID: {trace_id})"`
- Trace ID copiabile (per debug)

### Trigger
- Eccezione Python non gestita catturata dal middleware
- DB query fallisce
- Bug imprevisto

### Comportamento
- L'operazione viene abortita
- Stato dell'app è "best-effort safe": salvataggi parziali rimangono in DB
- L'utente può continuare a usare l'app

## Stati "Loading"

Non sono errori ma sono globali. Pattern:

### Skeleton loading (per liste e card)
- Replit Agent decide se usare skeleton CSS o spinner semplice
- Default: spinner Streamlit `st.spinner("...")` con caption esplicativa

### Inline loading per singola operazione
- Bottone si trasforma in spinner durante esecuzione
- Bottone disabilitato durante operazione

## Stati "Empty"

Già gestiti per pagina (vedi Page Briefs). Pattern unificato `<EmptyState />`:
- Icona/emoji grande
- Titolo asciutto
- Description 1-2 righe
- CTA primaria

## Toast (notifiche success)

Stati di successo non sono errori, ma rientrano nella "comunicazione globale":

- `st.toast()` nativo Streamlit
- Auto-dismiss ~3s
- Mai bloccanti

Esempi:
- "Salvato."
- "Progetto duplicato in «Nuovo nome»."
- "Stile applicato."
- "Vignetta generata."
- "PDF esportato."

## Implementazione

### Centralizzata
- `components/error_state.py` con funzioni:
  - `show_404()`
  - `show_session_expired()`
  - `show_credits_exhausted(plan_name)`
  - `show_network_error(retry_callback)`
  - `show_generic_error(trace_id)`

### Wrapper di pagina
Ogni pagina importa e usa un decoratore o wrapper:

```python
from auth import auth_required
from components.error_state import error_boundary

@auth_required
@error_boundary
def render_page():
    # contenuto pagina
    ...
```

## Microcopy
Vedi `06_MICROCOPY.md` sezione "Stati di errore globali".
