# Page Brief — Login

## Scopo
Autenticare l'utente con email + password (account creato manualmente dall'admin).

## Stati
| Stato | Descrizione |
|---|---|
| **Default** | Form vuoto |
| **Submitting** | Bottone disabilitato + spinner |
| **Error: credenziali** | Messaggio "Credenziali non valide." sotto il bottone |
| **Error: account disabilitato** | Messaggio "Questo account non è attivo. Contatta l'amministratore." |
| **Success** | Redirect → `/cambia_password` se primo login, altrimenti `/home` |

## Sezioni (ordine verticale)
1. **Header centrato**: Logo SnapToon + payoff *Dall'idea al fumetto, in uno snap.*
2. **Form login**: email + password + bottone "Accedi"
3. **Footer minimo**: "Hai dimenticato la password? Contatta l'amministratore." (testo plain)

## Componenti chiave
- `<LoginForm />`

## Note
- Nessuna sidebar
- Centrato verticalmente e orizzontalmente
