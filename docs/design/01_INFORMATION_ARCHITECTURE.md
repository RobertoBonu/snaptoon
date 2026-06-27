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
│   └── Tab 2: Sceneggiatura
│
├── 🎨 Stile                           [progetto attivo richiesto]
│   ├── Tab 1: Selezione stile
│   ├── Tab 2: Sfoglia libreria (7 categorie)
│   ├── Tab 3: Modifica stile custom
│   ├── Tab 4: Aspetto (sfondo, font, colori balloon/caption/SFX)
│   └── Tab 5: Anteprima prompt
│
├── 👥 Personaggi                      [progetto attivo richiesto]
│
├── 🖼 Genera                          [progetto attivo richiesto]
│   ├── Copertina (expander dedicato)
│   └── Per pagina: gabbia + vignette
│
├── 📐 Impagina                        [progetto attivo richiesto]
│
├── 💳 Crediti & Account               [richiede login]
│
├── 🛠 Admin                           [solo admin: aicreator.info@gmail.com]
│
└── 🚧 Error State
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

Solo per admin: voce "🛠 Admin" aggiuntiva.

## Navigazione — regole

1. **La sidebar è sempre presente** post-login. Sempre.
2. **Il progetto attivo è uno solo per sessione**.
3. **Le 5 sezioni di lavoro sono ordinate per workflow naturale**.
4. **L'utente può sempre tornare alla Home** cliccando sul logo.
5. **Il credit badge nella sidebar è cliccabile** → porta a Crediti & Account.
6. **Niente breadcrumb**. Gerarchia semplice: Home → Pagina di lavoro.
7. **Niente menu hamburger**. Sidebar sempre espansa su desktop.

## Pagine "speciali"

| Pagina | Caratteristica |
|---|---|
| **Login** | Niente sidebar. Solo form al centro. |
| **Onboarding** | Overlay modale sopra Home. Skippabile. |
| **Genera (balloon editor mode)** | Sostituisce temporaneamente la vista normale di Genera. |
| **Error generico** | Banner persistente in cima alla pagina. |
| **Crediti finiti** | Modale bloccante con CTA "Vedi piani". |
