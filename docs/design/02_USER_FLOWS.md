# User Flows

8 flussi principali. Ognuno definisce: **trigger**, **passi**, **stato finale**, **edge case**.

---

## Flusso 1 — Primo login (beta tester)

**Trigger**: Roberto ha creato l'utente da Admin → ha mandato credenziali.

```
Utente apre snaptoon.art
   ↓ Pagina Login
   ↓ Submit → backend valida → genera sessione
   ↓ Pagina "Cambia password" obbligatoria (primo login)
   ↓ Cambia password → atterra su Home
   ↓ Overlay Onboarding (welcome + 3-step tutorial)
   ↓ Click "Inizia con il progetto demo" → Sample project → Testo
   ↓ OPPURE Click "Salta tutorial" → Home con empty state
```

**Edge case**: password sbagliata / account disabilitato / email non trovata → errore generico "Credenziali non valide" (no enumeration)

---

## Flusso 2 — Creazione nuovo progetto

```
Click "Nuovo progetto"
   ↓ Modale: Titolo + Lunghezza
   ↓ Submit → DB crea record `projects`
   ↓ Redirect a 📝 Testo, tab Sorgente
```

**Edge case**: titolo vuoto / limite progetti raggiunto

---

## Flusso 3 — Dalla sorgente alla sceneggiatura

```
Upload .txt o paste testo → Salva sorgente
   ↓ [Opzionale] Generazione soggetto guidata
   ↓ Click "🪄 Adatta a sceneggiatura"
   ↓ Modale conferma costo crediti
   ↓ Confirm → Claude Opus → Script JSON (logline + personaggi + pagine + copertina)
   ↓ Tab Sceneggiatura si attiva e si popola
```

---

## Flusso 4 — Setup stile + personaggi

```
🎨 Stile → Sfoglia libreria → Click preset → "✨ Applica"
   ↓ [Opzionale] Tab Aspetto → personalizza sfondo + balloon
   ↓ Tab Anteprima prompt → verifica
   ↓
👥 Personaggi → cast pre-popolato da Claude
   ↓ Per ogni personaggio: modifica descrizione → "✨ Genera con AI" → reference
   ↓ Quando tutti hanno reference → procedi a 🖼 Genera
```

---

## Flusso 5 — Generazione vignette

```
🖼 Genera → per ogni vignetta:
   - 🎬 Scena (cast + formato + distanza + angolo + mood)
   - 👁 Prompt (preview)
   - Click "✨ Genera" → CostPreview → Confirm → OpenAI/Gemini → PNG
   ↓
Bulk: "🚀 Genera mancanti" / "🌙 Genera TUTTO"
```

---

## Flusso 6 — Balloon editor

```
Click "🎈 Balloon" su vignetta con dialoghi
   ↓ Vista Balloon Editor
   ↓ Seleziona dialogo → Slider X/Y → forma → tail
   ↓ Auto-save al rilascio slider
   ↓ Click "← Indietro" → torna a Genera
```

---

## Flusso 7 — Impaginazione + export PDF

```
📐 Impagina → per ogni pagina: "🎨 Renderizza pagina"
   ↓ Bulk: "📐 Renderizza tutte le pagine"
   ↓ "📥 Esporta PDF" → download automatico
```

**Costi**: render e PDF sono gratuiti (operazioni locali Python).

---

## Flusso 8 — Esaurimento crediti

```
Click "Genera vignetta" con saldo 0
   ↓ Modale bloccante: "Crediti esauriti"
   ↓ "Vedi piani" → 💳 Account
   ↓ [MVP] "Contatta admin per upgrade"
```

---

## Flussi NON in scope MVP

- Condivisione progetto in sola lettura
- Reset password via email (in MVP: contatta admin)
- Versioning / cronologia modifiche
- Export EPUB / IDML
