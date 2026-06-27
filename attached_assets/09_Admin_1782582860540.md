# Page Brief — 🛠 Admin

## Scopo
Pannello di amministrazione per Roberto (l'unico admin). Creare utenti, gestire crediti, monitorare consumi.

## Quando l'utente arriva
- Solo se `user.is_admin == true`
- Voce in sidebar visibile solo per admin
- Naviga a `/admin`

## Stati
| Stato | Descrizione |
|---|---|
| **Non admin** | Pagina non accessibile (redirect Home con toast "Non hai i permessi") |
| **Default** | Lista utenti + metriche globali |
| **Creating user** | Form nuovo utente attivo |
| **Editing user** | Form modifica utente attivo |
| **Granting credits** | Modale aggiungi crediti aperto |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Admin" + caption "Solo per amministratori."
2. **Metriche globali** (4 metric cards in riga):
   - Utenti totali
   - Utenti attivi (ultimi 7 giorni)
   - Crediti consumati questo mese
   - Costo stimato API questo mese
3. **Nuovo utente** (expander):
   - Form: email + password temp + piano iniziale + crediti iniziali
   - Bottone "Crea account"
4. **Utenti registrati** (lista/tabella):
   - Per ogni utente: email · piano · crediti rimasti/totali · creato il · stato · azioni
5. **Log operazioni globali** (expander, in fondo):
   - Ultime 100 operazioni AI: timestamp · utente · operazione · costo · success/error

## Layout — Tabella utenti
```
┌─────────────────────────────────────────────────────────────────────┐
│  Email              Piano   Crediti  Creato     Stato   Azioni      │
├─────────────────────────────────────────────────────────────────────┤
│  marco@example.com  Creator 142/200  01/07/26   ✓      ✏️ 🪙 🚫   │
│  laura@example.com  Pro     580/600  28/06/26   ✓      ✏️ 🪙 🚫   │
│  test@example.com   Trial   12/30    25/06/26   🚫     ✓ rabili.   │
│  ...                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Azioni inline per utente
- **✏️ Modifica**: apre form (email readonly, piano, attivo/disabilitato)
- **🪙 Aggiungi crediti**: modale con `st.number_input` → motivazione (text) → conferma → grant
- **🚫 Disabilita** / **✓ Riabilita**: toggle stato attivo

## Componenti chiave
- `<AdminUserRow />` per ogni utente
- `st.metric` per le 4 metriche globali
- Form di creazione utente
- `<ConfirmDialog />` per disabilitazione

## Interazioni
- **Click "Crea account"**:
  - Validazione email + lunghezza password ≥ 8
  - POST `/api/admin/users` con: email, password_temp (hashata), plan, initial_credits
  - Success → toast "Utente creato. Manda all'utente email e password temporanea fuori dall'app."
  - Email e password rimangono visibili in chiaro nel form post-submit per 30s (per copia-incolla) — poi clean
- **Click "Aggiungi crediti"** → modale → input numero + motivazione → POST `/api/admin/users/{id}/grant_credits` → log immutabile in `credit_ledger`
- **Click "Disabilita"** → ConfirmDialog → PATCH `is_active=false` → utente non potrà più loggarsi
- **Click "Modifica"** → form inline → salva
- **Refresh metriche**: ogni X secondi (no realtime, no WebSocket)

## Edge case
- Email già esistente → errore "Esiste già un utente con questa email."
- Piano selezionato non valido → backend rifiuta
- Crediti negativi non ammessi (anche grant in negativo per "ritiro" possibile? V1.1)
- Auto-disabilitazione (admin disabilita sé stesso) → blocco "Non puoi disabilitare il tuo account."

## Streamlit
- File: `pages/99_🛠_Admin.py` (numero alto per essere in fondo nella nav Streamlit)
- All'apertura: check `if not user.is_admin: st.error(...); st.stop()`
- Tabella: `st.dataframe()` con `st.column_config` per azioni inline (se troppo complesso → riga per riga con expander)

## Layout
- Dense layout (admin è "lavoro tecnico", non "esperienza")
- Metriche in alto sempre visibili
- Tabella scrollabile

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "🛠 Admin".

## Sicurezza
- Solo admin può accedere (check sia frontend che backend)
- Password temporanea: bcrypt hash immediato; mai loggata in chiaro
- Log audit di ogni azione admin: `admin_audit` table (chi · quando · cosa · su chi)
- Eventuali rate-limit su creazione utente (max 100/giorno)

## Dati richiesti dal backend

```python
# GET /api/admin/users
[
    {
        "id": uuid,
        "email": str,
        "plan": "free_trial" | "creator" | "pro",
        "credits_remaining": int,
        "credits_total": int,
        "created_at": datetime,
        "last_login_at": datetime | None,
        "is_active": bool,
    },
    ...
]

# GET /api/admin/metrics
{
    "users_total": int,
    "users_active_7d": int,
    "credits_consumed_this_month": int,
    "estimated_api_cost_eur": float,
}

# POST /api/admin/users
{
    "email": str,
    "password_temp": str,  # plain, hashata server-side
    "plan": str,
    "initial_credits": int,
}

# POST /api/admin/users/{id}/grant_credits
{
    "amount": int,  # positivo per accredito
    "reason": str,  # es. "manual_test_credit"
}

# PATCH /api/admin/users/{id}
{
    "plan": str,
    "is_active": bool,
}
```
