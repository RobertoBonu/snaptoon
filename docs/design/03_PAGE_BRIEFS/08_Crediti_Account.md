# Page Brief — 💳 Crediti & Account

## Scopo
Vista personale dell'utente: saldo crediti, storico operazioni, piano attivo, gestione password, logout.

## Stati
| Stato | Descrizione |
|---|---|
| **Default** | Tutte le info visibili |
| **Editing password** | Form cambio password attivo |
| **Logging out** | Conferma → redirect Login |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Account e crediti" + caption email utente
2. **Saldo crediti**: Metric `X/Y` + caption piano + progress bar
3. **Piano attivo**: nome (badge) + features incluse + info rinnovo
4. **Storico operazioni**: tabella ultime 50 (Data · Operazione · Costo · Saldo dopo)
5. **Impostazioni personali**: email (readonly) + bottone "🔑 Cambia password"
6. **Esci**: bottone "🚪 Esci" isolato in basso

## Dati richiesti dal backend

```python
# GET /api/me/account
{
    "email": str,
    "plan": "free_trial" | "creator" | "pro",
    "plan_features": list[str],
    "credits_remaining": int,
    "credits_total": int,
    "renews_at": datetime | None,
    "is_admin": bool,
}

# GET /api/me/credit_history?limit=50
[{"occurred_at": datetime, "operation": str, "operation_label": str, "delta": int, "balance_after": int}]
```

## Streamlit
- File: `pages/6_💳_Account.py`
- Tabella storico con `st.dataframe()`
- Form password con `st.form()`
