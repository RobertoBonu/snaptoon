# Page Brief — 💳 Crediti & Account

## Scopo
Vista personale dell'utente: saldo crediti, storico operazioni, piano attivo, gestione password, logout.

## Quando l'utente arriva
- Click su credit badge nella sidebar
- Click su "⚙️ Impostazioni" nella sidebar
- Click "Vedi piani" dal modale crediti esauriti

## Stati
| Stato | Descrizione |
|---|---|
| **Default** | Tutte le info visibili |
| **Editing password** | Form cambio password attivo |
| **Logging out** | Conferma "Sei sicuro di voler uscire?" → success → redirect Login |

## Sezioni (ordine verticale)
1. **Header pagina**: titolo "Account e crediti" + caption email utente
2. **Saldo crediti** (sezione evidenziata):
   - Metric: `X/Y` crediti rimasti
   - Caption: nome piano attivo
   - Progress bar
3. **Piano attivo**:
   - Nome piano (badge)
   - Lista features incluse (es. "200 crediti/mese · 5 progetti · Qualità Media")
   - Rinnovo: "Contatta l'amministratore per gestire l'abbonamento." (MVP) / data rinnovo (V1.1)
4. **Storico operazioni** (tabella):
   - Ultime 50 operazioni
   - Colonne: Data · Operazione · Costo · Saldo dopo
5. **Impostazioni personali**:
   - Email (readonly)
   - Bottone "🔑 Cambia password"
6. **Esci** (sezione separata):
   - Bottone "🚪 Esci" (secondary, isolato in basso)

## Layout
```
┌──────────────────────────────────────────────────────────┐
│  Account e crediti                                       │
│  marco.rossi@example.com                                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────┐                         │
│  │  Saldo crediti              │                         │
│  │  142 / 200                  │                         │
│  │  ━━━━━━━━━━━━━░░░ 71%       │                         │
│  │  Piano Creator              │                         │
│  └─────────────────────────────┘                         │
│                                                          │
│  Piano attivo: Creator                                   │
│  ✓ 200 crediti al mese                                   │
│  ✓ 5 progetti                                            │
│  ✓ Qualità Bassa + Media                                 │
│                                                          │
│  Contatta l'amministratore per gestire l'abbonamento.    │
├──────────────────────────────────────────────────────────┤
│  Storico operazioni                                      │
│                                                          │
│  Data        Operazione              Costo    Saldo      │
│  03/07 14:23 Genera vignetta         -1       142        │
│  03/07 14:10 Genera variante         -1       143        │
│  03/07 12:50 Adatta sceneggiatura    -5       144        │
│  ...                                                     │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  Impostazioni personali                                  │
│                                                          │
│  Email: marco.rossi@example.com                          │
│  [🔑 Cambia password]                                    │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  [🚪 Esci]                                               │
└──────────────────────────────────────────────────────────┘
```

## Componenti chiave
- `<CreditBadge />` (versione "grande" della sidebar)
- Form cambio password
- `<ConfirmDialog />` per logout

## Interazioni
- **Click "Cambia password"** → form con: vecchia password + nuova + conferma nuova → submit → backend valida → success → toast
- **Click "Esci"** → ConfirmDialog "Vuoi uscire da SnapToon?" → backend invalida sessione → redirect Login

## Edge case
- Saldo 0/Y → metric in rosso, caption "Nessun credito rimasto"
- Vecchia password sbagliata al cambio → errore inline
- Nuove password non coincidenti → errore inline
- Storico vuoto (mai operato) → empty state piccolo "Nessuna operazione ancora."

## Streamlit
- File: `pages/9_💳_Account.py` o `pages/6_💳_Account.py`
- Tabella storico con `st.dataframe()` (paginazione client-side)
- Form password con `st.form()`

## Microcopy chiave
Vedi `06_MICROCOPY.md` sezione "💳 Crediti & Account".

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
[
    {
        "occurred_at": datetime,
        "operation": str,  # es. "generate_panel" / "adapt_script"
        "operation_label": str,  # es. "Genera vignetta"
        "delta": int,  # negativo per consumo, positivo per accredito
        "balance_after": int,
    },
    ...
]
```
