---
name: Esplora assets (public DB-driven gallery)
description: How the public /esplora gallery is backed by DB + storage, and the access-control rule for hidden assets.
---

# Esplora assets

The public `/esplora` page (copertine/tavole/personaggi) is DB-driven, not static files.
Assets live in `esplora_assets` (model `EsploraAsset`), images in object storage under
`esplora/{section}/{id}.png`. Public read endpoints are **intentionally unauthenticated**
(`/api/esplora/assets`, `/api/esplora/assets/{id}/image`); management is admin-only under
`/api/admin/esplora/*`.

## Access-control rule (easy to re-break)
`is_active=False` (hidden) assets must be blocked in **both** the public list **and** the
public direct image-serve endpoint — not just the list. A hidden asset's image must 404
publicly even if the direct UUID URL is known.

**Why:** filtering only the list still leaks images via shared/cached direct URLs.

**How to apply:** any new public serve path for these assets must check `is_active`. Admin
previews of hidden assets use a separate admin-gated image endpoint
(`/api/admin/esplora/assets/{id}/image`), so `_to_out(admin=True)` points image_url there.

## Card metadata fields
Each asset carries 5 display fields shown on the public card: `asset_type` (gray uppercase
label e.g. KIDSTOONS), `title` (bold), `caption` (didascalia), `author_name`, `author_role`
(rendered as a purple pill, e.g. "Editore"). All default to empty string (non-null) at DB +
API level; frontend conditionally renders each block so empty fields simply disappear.
Admin edits all 5 inline (Salva/Annulla); `saveMeta` returns a boolean so the form stays
open on PATCH failure (no lost edits).

## Conventions
- Uploads are re-encoded to **WebP** (PIL, quality 85, method 6), preserving pixel
  dimensions — lighter files, same size. AI-generated images stay PNG. So storage holds a
  **mix of formats**: serving must NOT hardcode a MIME. `_serve_image` sniffs magic bytes
  (`_detect_media_type`: RIFF/WEBP, PNG, JPEG) and sets Content-Type at runtime. Storage
  keys still end `.png` (cosmetic; the extension is not used for serving).
- Public card images are click-to-zoom (Lightbox overlay): ESC / backdrop / ✕ to close,
  body scroll locked while open. The Lightbox MUST render via `createPortal(..., document.body)`:
  the card uses `.lift:hover { transform: translateY(-4px) }`, and a `transform` on an
  ancestor re-bases `position: fixed` to that ancestor — the overlay then jumps and, because
  it steals hover, toggles the transform in a rapid mouseenter/leave loop → continuous flicker.
- Cache-bust: `image_url` carries `?v={updated_at epoch}`; upload/generate explicitly set
  `updated_at = utcnow()` so the URL changes even when the storage key is unchanged.
- CREA page images (`/crea`) reuse this exact pattern but as **fixed slots**, not a dynamic
  list: model `CreaImage` (unique `slot`), router `api/routers/crea.py` with a `SLOTS` config
  (6 keys: dashboard, step-testo, step-stile, step-personaggi, step-genera, step-impagina),
  reusing esplora's `_serve_image`/`_detect_media_type` + PNG→WebP. Admin uploads override the
  static default in `web/public/images/crea/`; the public page (`web/app/crea/page.tsx`) starts
  from static defaults then swaps to uploaded URLs via `GET /api/crea/images`. Delete reverts to
  default (clears storage_key). Admin UI: `web/app/app/admin/crea/page.tsx`.
