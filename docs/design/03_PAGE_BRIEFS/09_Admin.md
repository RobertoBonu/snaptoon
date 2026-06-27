# Page Brief — 🛠 Admin

## Scopo
Pannello di amministrazione per Roberto (l'unico admin). Creare utenti, gestire crediti, monitorare consumi.

## Quando l'utente arriva
- Solo se `user.is_admin == true`

## Stati
| Stato | Descrizione |
|---|---|
| **Non admin** | Redirect Home con toast "Non hai i permessi" |
| **Default** | Lista utenti + metriche globali |
| **Creating user** | Form nuovo utente attivo |
| **Editing user** | Form modifica utente attivo |
| **Granting credits** | Modale aggiungi crediti |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Admin" + caption "Solo per amministratori."
2. **Metriche globali** (4 metric cards): Utenti totali · Utenti attivi 7gg · Crediti consumati/mese · Costo API stimato
3. **Nuovo utente** (expander): form email + password temp + piano + crediti
4. **Utenti registrati**: tabella con azioni inline ✏️ 🪙 🚫
5. **Log operazioni globali** (expander): ultime 100 operazioni AI

## Sicurezza
- Solo admin può accedere (check frontend + backend)
- Password temporanea: bcrypt hash immediato, mai loggata in chiaro
- Log audit in `admin_audit` table

## Streamlit
- File: `pages/99_🛠_Admin.py`
- Check all'apertura: `if not user.is_admin: st.error(...); st.stop()`
