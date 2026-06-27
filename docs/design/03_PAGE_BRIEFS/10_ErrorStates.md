# Page Brief — Stati di errore globali

## Tipi di errore

| Categoria | Quando | Visualizzazione |
|---|---|---|
| **404** | URL inesistente / progetto non più disponibile | Pagina dedicata con CTA "Torna alla Home" |
| **Sessione scaduta** | Token sessione expired | Redirect Login con toast persistente |
| **Crediti finiti** | Operazione richiede crediti > saldo | Modale bloccante sulla pagina corrente |
| **Errore di rete / API** | Fetch fallisce, timeout AI | Banner persistente con bottone "Riprova" |
| **Errore generico** | Eccezione non gestita | Banner persistente con messaggio + trace ID |

## 404
- Centrato verticalmente, icona grande
- Titolo: "Pagina non trovata."
- Description: "Il link che hai seguito non porta da nessuna parte, oppure il progetto è stato eliminato."
- CTA primary: "Torna alla home"

## Sessione scaduta
- Redirect immediato a `/login`
- Toast persistente: "La sessione è scaduta. Accedi di nuovo."

## Crediti finiti (modale)
- Titolo: "Crediti esauriti"
- Body: "Hai usato tutti i crediti del tuo piano {plan_name}. Per continuare a generare, passa a un piano superiore o contatta l'amministratore."
- CTA primary: "Vedi piani" → `💳 Account`
- CTA secondary: "Chiudi"

## Errore di rete (banner sticky)
- Colore warning
- Body: "Errore di connessione con il servizio AI. Riprova tra qualche istante."
- Bottone "Riprova" inline

## Errore generico (banner sticky)
- Colore error
- Body: "Si è verificato un errore. Se persiste, contatta l'amministratore. (ID: {trace_id})"
- Trace ID copiabile

## Implementazione centralizzata

```python
# components/error_state.py
def show_404(): ...
def show_session_expired(): ...
def show_credits_exhausted(plan_name): ...
def show_network_error(retry_callback): ...
def show_generic_error(trace_id): ...
```
