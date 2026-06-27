# Page Brief — Login

## Scopo
Autenticare l'utente con email + password (account creato manualmente dall'admin).

## Quando l'utente arriva
- Non è loggato
- Ha ricevuto credenziali dall'admin (via WhatsApp/email)
- Oppure la sua sessione è scaduta

## Stati
| Stato | Descrizione |
|---|---|
| **Default** | Form vuoto |
| **Submitting** | Bottone disabilitato + spinner |
| **Error: credenziali** | Messaggio "Credenziali non valide." sotto il bottone |
| **Error: account disabilitato** | Messaggio "Questo account non è attivo. Contatta l'amministratore." |
| **Success** | Redirect immediato → `/cambia_password` se primo login, altrimenti `/home` |

## Sezioni (ordine verticale)
1. **Header centrato**: Logo SnapToon + payoff *Dall'idea al fumetto, in uno snap.*
2. **Form login**: email + password + bottone "Accedi"
3. **Footer minimo**: "Hai dimenticato la password? Contatta l'amministratore." (testo plain, non link)

## Componenti chiave
- `<LoginForm />` (componente custom)

## Interazioni
- **Click Accedi (o Enter su password)** → POST `/api/auth/login` → success → redirect
- **Email malformata** → validazione inline al blur

## Edge case
- Email caso-insensitive (lowercase a backend)
- Password troppo corta → errore generico "Credenziali non valide" (no enumeration)
- Più di 5 tentativi falliti in 10 min → blocco temporaneo (V1.1, in MVP non implementare)

## Streamlit
- Pagina dedicata (non in `pages/`, ma in app.py condizionale)
- Niente sidebar
- Form con `st.form()` + `st.form_submit_button()`
- File del progetto: `app.py` o `auth/login.py`

## Layout
- Centrato verticalmente e orizzontalmente sullo schermo
- Larghezza form: ~400px
- Padding generoso (~80px) attorno al form
- Logo grande sopra il form (non grande quanto un hero, ma evidente)

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "Login".
