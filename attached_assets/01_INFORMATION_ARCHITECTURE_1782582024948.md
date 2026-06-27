# Information Architecture

## Mappa delle pagine

```
🌐 SnapToon (snaptoon.art)
│
├── 🔐 Login                           [pubblica]
│
├── 🏠 Home / Project list             [richiede login]
│   ├── Lista progetti utente
│   ├── CTA "Nuovo progetto"
│   ├── Duplica / Elimina progetto
│   └── Switch progetto attivo
│
├── 🎓 Onboarding (overlay/modal)      [solo al primo login]
│   └── Welcome + 3-step tutorial + Sample project
│
├── 📝 Testo                           [progetto attivo richiesto]
│   ├── Tab 1: Sorgente
│   │   ├── Upload .txt / paste testo
│   │   ├── Generazione soggetto (opzionale)
│   │   └── Adattamento in sceneggiatura (Claude)
│   └── Tab 2: Sceneggiatura
│       ├── Logline editabile
│       ├── Personaggi editabili (cast bible)
│       ├── Pagine editabili (descrizione + dialoghi + copertina)
│       └── Salvataggio incrementale
│
├── 🎨 Stile                           [progetto attivo richiesto]
│   ├── Tab 1: Selezione stile
│   ├── Tab 2: Sfoglia libreria (7 categorie)
│   ├── Tab 3: Modifica stile custom
│   ├── Tab 4: Aspetto (sfondo, font, colori balloon/caption/SFX)
│   └── Tab 5: Anteprima prompt
│
├── 👥 Personaggi                      [progetto attivo richiesto]
│   ├── Cast del progetto
│   ├── Sheet per personaggio
│   ├── Reference image principale (slot 1)
│   ├── Reference variants (slot 2-7)
│   ├── Cast manager (archivio globale)
│   └── Import character da archivio
│
├── 🖼 Genera                          [progetto attivo richiesto]
│   ├── Header con grid selector pagina
│   ├── Copertina (expander dedicato)
│   ├── Per pagina:
│   │   ├── Selettore gabbia + anteprima
│   │   └── Per vignetta: Genera/Rigenera + Scena + Prompt + Balloon + Sposta
│   ├── Bulk: Genera vignette mancanti
│   └── Bulk: Genera TUTTO (notturno)
│
├── 📐 Impagina                        [progetto attivo richiesto]
│   ├── Lista pagine renderizzate
│   ├── Bulk render
│   └── Export PDF
│
├── 💳 Crediti & Account               [richiede login]
│   ├── Saldo crediti corrente
│   ├── Storico operazioni
│   ├── Piano attivo
│   ├── Settings personali (email, password)
│   └── Logout
│
├── 🛠 Admin                           [solo admin: roberto@snaptoon.art]
│   ├── Lista utenti
│   ├── Crea nuovo utente
│   ├── Modifica crediti
│   ├── Modifica piano
│   ├── Log operazioni
│   └── Metriche globali
│
└── 🚧 Error State                     [stati di errore globali]
    ├── 404
    ├── Sessione scaduta
    ├── Crediti finiti (overlay/modal)
    └── Errore generico (banner)
```

## Sidebar persistente (visibile in tutte le pagine post-login)

```
┌──────────────────────────┐
│   [Logo SnapToon]        │
│                          │
│   Progetto attivo:       │
│   ▼ [Nome progetto]      │
│                          │
│   ─── Navigazione ───    │
│   📝 Testo               │
│   🎨 Stile               │
│   👥 Personaggi          │
│   🖼 Genera              │
│   📐 Impagina            │
│                          │
│   ─── Account ───        │
│   💳 Crediti: 142/200    │
│   ⚙️  Impostazioni       │
│   🚪 Esci                │
└──────────────────────────┘
```

### Solo per admin (Roberto):
Subito dopo "Impostazioni" appare anche:
```
   🛠 Admin
```

## Navigazione — regole

1. **La sidebar è sempre presente** post-login. Sempre.
2. **Il progetto attivo è uno solo per sessione**. Lo switch da dropdown sidebar.
3. **Le 5 sezioni di lavoro (Testo, Stile, Personaggi, Genera, Impagina) sono ordinate per workflow naturale** — non in ordine alfabetico, non per importanza.
4. **L'utente può sempre tornare alla Home** cliccando sul logo.
5. **Il credit badge nella sidebar è cliccabile** → porta a Crediti & Account.
6. **Niente breadcrumb**. La gerarchia è semplice: Home → Pagina di lavoro.
7. **Niente menu hamburger**. Sidebar sempre espansa su desktop.

## Gerarchia di importanza visiva (per ogni pagina)

In ordine, dall'alto verso il basso, la pagina presenta:

1. **Header pagina** (titolo + sottotitolo + eventuali azioni globali della pagina)
2. **Contesto** (nome progetto, stile attivo, ecc. — secondario)
3. **Contenuto principale** (il lavoro)
4. **Azioni di pagina** (in linea con il contenuto)
5. **Footer di stato** (nessuno per ora — Streamlit non lo gestisce bene)

## Pagine "speciali"

| Pagina | Caratteristica |
|---|---|
| **Login** | Niente sidebar. Solo form al centro. |
| **Onboarding** | Overlay modale sopra Home. Skippabile. |
| **Genera (balloon editor mode)** | Sostituisce temporaneamente la vista normale di Genera. Solo bottone "← Indietro" per uscire. |
| **Error generico** | Banner persistente in cima alla pagina. |
| **Crediti finiti** | Modale bloccante con CTA "Vedi piani". |

## Stati globali dell'utente

| Stato | Cosa vede |
|---|---|
| **Non loggato** | Solo pagina Login |
| **Loggato, primo accesso** | Onboarding overlay + Home |
| **Loggato, nessun progetto** | Home con empty state + CTA |
| **Loggato, progetto selezionato** | Tutta la sidebar attiva + ultima pagina visitata |
| **Loggato, crediti finiti** | Sidebar mostra "0 crediti" rosso. Modale bloccante a ogni tentativo di generazione. |
| **Loggato, sessione scaduta** | Redirect Login con messaggio "Sessione scaduta, accedi di nuovo" |
| **Loggato, admin** | Tutto come utente normale + voce "🛠 Admin" in sidebar |
