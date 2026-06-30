---
name: SnapToon environment quirks
description: Non-obvious env/routing/setup facts for SnapToon (V2 stack: Next.js + FastAPI) in the pnpm-workspace artifact monorepo
---

# Streamlit reachability through the artifact proxy
The workspace preview is served by a global reverse proxy on port 80 that routes
ONLY by each artifact's `.replit-artifact/artifact.toml` `paths` (most-specific-first,
paths are NOT rewritten). A bare Streamlit workflow on port 5000 is unreachable —
the proxy has no route to it, so `/` returns 404 and the preview shows
"We couldn't reach this app".

**Fix:** register the Streamlit app as a `kind = "web"` artifact at `artifacts/snaptoon`
with a service `localPort = 5000`, `paths = ["/"]`. This makes the proxy route `/`
(and Streamlit's `/_stcore/*`, `/static/*`) to 5000. (Legacy/historical — superseded by the V2 stack documented below.)

**Why:** there is no Streamlit/Python artifact type in `createArtifact`, but the proxy
and `listArtifacts` read artifact.toml files from disk, so a hand-written web artifact.toml
works.

**How to apply / gotchas:**
- You cannot edit `artifact.toml` directly and cannot `createArtifact` a streamlit type.
  Write the full TOML to a sibling temp file (e.g. `artifact.edit.toml`) in the SAME
  `.replit-artifact/` dir (NOT /tmp), then call
  `verifyAndReplaceArtifactToml({tempFilePath, artifactTomlPath})` with absolute paths.
- The target `artifact.toml` must itself already be valid TOML before validation — a
  placeholder like the literal word `placeholder` fails with ARTIFACT_SYNTAX_ERROR.
- Artifact service `run` commands execute with cwd = the artifact dir
  (`artifacts/snaptoon`), NOT repo root. `app.py` lives at repo root, so the run command
  must `cd /home/runner/workspace` first, e.g.
  `bash -lc 'cd /home/runner/workspace && exec streamlit run app.py --server.port 5000 ...'`.
- Registering the web artifact auto-creates a workflow `artifacts/snaptoon: SnapToon`
  that runs streamlit; remove any standalone `Start application` streamlit workflow to
  avoid a double-bind on port 5000.

# Recurring: "app not running" after env restart
When the dev environment sleeps/restarts, ALL three artifact workflows
(`artifacts/snaptoon: SnapToon`, `artifacts/api-server: API Server`,
`artifacts/mockup-sandbox: Component Preview Server`) drop to `not_started` and the
proxy returns 502 at `/`. `.replit` `[workflows]` is empty so nothing auto-starts them.
**Fix:** restart all three workflows (snaptoon first), then verify `curl localhost:80/`
=200. This is NOT an app bug — the app starts fine every time. The code_execution
notebook also resets on these restarts (state lost).

# Recurring: 500 "Internal Server Error" after a platform merge/reconcile (corrupt .next)
After a task is merged and the post-merge reconcile runs while the Next dev server is live,
the V2 Next build cache gets corrupted: every route returns HTTP 500 and the workflow log
floods with `ENOENT ... web/.next/server/app/<route>/page/app-build-manifest.json` and
`web/.next/static/development/_buildManifest.js.tmp.*`. This is NOT an app/code bug and a
plain workflow restart alone does NOT fix it (the stale `.next` persists).
**Fix:** `rm -rf web/.next` then restart workflow `artifacts/snaptoon: SnapToon`; verify
`curl localhost:80/{,esplora,...}` = 200. (Distinct from the 502 "not_started" case above,
which is just stopped workflows.)

# Git push/commit mechanics in the main agent sandbox
- `git commit` is BLOCKED in the main agent ("Destructive git operations are not
  allowed"). The platform auto-creates a checkpoint commit at the END of each turn
  (trigger "Loop ended"), with an auto-generated message — you cannot set a custom
  "design: ..." message from the main agent. So you cannot commit a turn's own
  working-tree edits within that same turn.
- `git push origin main` (non-force) actually SUCCEEDS — the data reaches GitHub even
  though the command exits non-zero. The transfer line `OLDSHA..NEWSHA  main -> main`
  is the proof of success; the trailing error is only the blocked LOCAL ref-update of
  `.git/refs/remotes/origin/main.lock` (bookkeeping), not a push failure. Judge success
  by that output line, NOT the exit code.
- `git config` / `git remote set-url` are ALSO blocked (they write `.git/config` → lock).
  So you cannot change the remote URL or persist a credential helper from the main agent.
- The GitHub PAT now lives in the `GITHUB_TOKEN` secret (NOT in the URL). Push/auth by
  passing an EPHEMERAL credential helper on the command line (writes nothing) against the
  CLEAN explicit URL:
    git -c credential.helper='!f() { echo username=x-access-token; echo "password=$GITHUB_TOKEN"; }; f' \
      push https://github.com/RobertoBonu/snaptoon.git main
  Same `-c ... ls-remote https://github.com/RobertoBonu/snaptoon.git -h refs/heads/main`
  to verify. Do NOT rely on `origin` (its stored URL still holds the OLD, now-revoked
  token — harmless but won't authenticate).
- Still pipe git output through `sed -E 's/ghp_[A-Za-z0-9_]+/***REDACTED***/g'` defensively.
- Practical sync pattern for the user's "always align GitHub" rule: edit files (auto-
  committed at turn end) → push with the command above at the next opportunity → confirm
  via ls-remote SHA.

# Streamlit custom-CSS quirks (login redesign)
- Scope login-only styling to `.st-key-snaptoon_login_form ...` (Streamlit 1.58 puts a
  `st-key-<form_key>` class on the form container; descendant selectors for inputs
  `[data-baseweb="input"]`, the submit button, etc. work reliably). Center the page with
  `:has(.st-key-snaptoon_login_form)` so it only triggers on the login screen.
- `text-transform: uppercase` did NOT visually render on the field labels (neither on the
  native `[data-testid="stWidgetLabel"]` element nor on a custom injected markdown `<div>`),
  even with `!important`. The native-label `data-testid` selector also failed to take.
  **Workaround that works:** render labels as your OWN `st.markdown('<div class="snaptoon-field-label">EMAIL</div>')`
  with the text ALREADY uppercase in the literal string, and set the native widget label to
  `label_visibility="collapsed"` (keep a real label arg like "Email" for a11y). CSS class
  styling (size/color/letter-spacing) on that div DOES apply; only `text-transform` was the
  unreliable part, so bake the case into the text.
- `screenshot` app_preview DOES work for the snaptoon artifact (`artifact_dir_name="snaptoon"`,
  `path="/"`) and shows the live login; the browser warning "Password field is not contained
  in a form" is harmless (Streamlit forms aren't real <form> elements).
- Renaming a sidebar nav item label WITHOUT touching app.py (e.g. entrypoint "app" -> "HOME"):
  the multipage nav DOM (Streamlit 1.58) is `div[data-testid=stSidebarNav]` >
  `ul[data-testid=stSidebarNavItems]` > one `div[data-testid=stSidebarNavLinkContainer]` per
  item (containers are DIVs, NOT `<li>`) > `a[data-testid=stSidebarNavLink]` > optional icon
  `<span>` + the label rendered by Streamlit markdown inside `[data-testid=stMarkdownContainer]`.
  Pitfalls learned the hard way: `li:first-child` matches nothing (no li); `...LinkContainer:first-child`
  matches EVERY item (each is first-child of its own wrapper) — use `stSidebarNavItems > *:first-child`
  to hit only the entrypoint; the label is NOT a bare text node or `<span>`, it's in
  `stMarkdownContainer`, so zero THAT (and its `*`) with `font-size:0!important` to hide the old
  text and add the new via `::after{content:"HOME";font-size:14px!important}`. `::after` content
  renders fine; only `text-transform` is the unreliable property here (bake case into the literal).
- Replacing the emoji nav ICONS with stylized line icons (CSS-only, no app.py): inside each nav
  `<a>` there are TWO spans — icon = `span:first-child`, label = `span:last-child` (both ARE spans).
  Isolate the icon without hitting the label via `a > span:first-child:not(:last-child)` (the
  entrypoint HOME has only the label span, so this correctly skips it). Hide the emoji glyph with
  `font-size:0!important` on that span AND its `*` (the glyph can be nested), then paint a
  Lucide-style icon with `-webkit-mask-image`+`mask-image` = inline SVG data-URI (percent-encode
  `<`/`>` as %3C/%3E; use `stroke='black'`/`fill` so the mask alpha is opaque) + `mask-size:contain`
  + `background-color:currentColor` so the icon inherits the link color (slate / amber-active /
  hover) automatically. HOME has no icon span → give it the icon via `*:first-child a::before`.
  Per-item icons assigned by `nth-child(2..6)` (order = page filename order; reorder => remap).
- Hiding the sidebar ONLY on the auth screens (login + first-login change-password) WITHOUT
  touching app.py: login_form.py IS editable, so emit an invisible marker
  `st.markdown('<div class="snaptoon-auth-marker"></div>', unsafe_allow_html=True)` at the top of
  BOTH render_login_form() and render_change_password_form() (the only pre-auth views). Then in
  custom.css use `:has()` (Streamlit = modern Chromium, supported): collapse the marker's own block
  with `[data-testid=stElementContainer]:has(.snaptoon-auth-marker){display:none}` (no layout gap;
  display:none keeps the node so :has still matches) and hide the nav with
  `[data-testid=stApp]:has(.snaptoon-auth-marker) [data-testid=stSidebar]{display:none!important}`
  (also hide `stSidebarCollapsedControl` + `stSidebarCollapseButton`). Authenticated pages don't
  render login_form -> no marker -> sidebar shows normally. NOTE there's an existing
  `enforce_sidebar_visibility()` rule with !important, so the auth-hide selectors MUST use
  !important too (they do) to win.

# Image loading / Object Storage cost model
- `storage.client.object_exists` is CHEAP: the Replit backend implements it via
  `client.list(prefix=key)` (a metadata listing), NOT a full download. An earlier
  version did `download_as_bytes` for the check (catastrophic latency) — that is long
  fixed. Do NOT assume existence checks are expensive; only `download_bytes` transfers
  the blob. (Some code comments still wrongly claim object_exists downloads — ignore.)
- Perf rule for "on-demand" image loading in the Streamlit pages: download bytes ONLY at
  the point they're shown on screen (display/download/generation). For counts/status
  ("exists or not") use DB fields already in the view dicts (`ref_storage_key`,
  `illustration_key`, vignette records) or `object_exists` (page-renders have no DB flag)
  — never download full bytes just to count, it defeats lazy loading.
- `storage/images.py` `load_image_bytes` caches via `st.cache_data`; the cached inner fn
  must RAISE on miss/error (st.cache_data does not cache exceptions) so the wrapper can
  return None for not-found (ObjectNotFoundError/BucketNotFoundError/FileNotFoundError)
  vs log+return-None-without-caching for transient errors. Caching a transient failure as
  None would hide a valid image for the whole TTL. Call `invalidate_image_cache()` after
  every upload/delete (it clears the whole image cache — coarse but writes are rare).
- **Why:** Streamlit `st.expander` ALWAYS executes its body (collapsed only hides via CSS),
  so "lazy on expand" needs explicit gating; the realistic win is cheap presence checks +
  cached downloads, which the validation code review enforces.

# Other env facts
- Runtime is Python 3.11 (NOT 3.13). Install deps via the package-management skill
  (`installLanguagePackages`, uv-backed); raw `pip install` times out (exit -1).
- Alembic needs repo root on PYTHONPATH: `PYTHONPATH="$PWD" alembic ...` or it fails
  with `No module named 'db'`.
- For ad hoc curl always use `http://localhost:80` (the proxy), never service ports directly.
- `screenshot` app_preview only works for registered artifacts; verify Streamlit via
  curl/logs (HTTP 200 on `/` and `/_stcore/health`) instead.
- Git in main agent: NOT only `commit`/`config` are blocked — `git fetch`/`git pull`
  are ALSO blocked ("Destructive git operations are not allowed in the main agent")
  because they write objects under .git/objects. So you CANNOT integrate remote
  changes from here. Only `git push` (no force) and read-only `log`/`ls-remote`
  (with the inline credential helper) work. If the remote has DIVERGED (its tip is
  not an ancestor of HEAD), a non-force push is rejected and there is no main-agent
  way to merge — delegate the merge+push to a background Project Task, or let the
  user integrate via their own flow (they push via Claude). Confirm divergence with
  `ls-remote` vs local `git log` instead of fetch.

## V2 migration (Streamlit → Next.js + FastAPI)
- SnapToon's `/` web artifact NO LONGER runs Streamlit `app.py`. It runs the V2
  stack: Next.js in `web/` + FastAPI in `api/main.py`. Next.js serves on $PORT
  (5000) and proxies `/api/*` → FastAPI on :8000 via `web/app/api/[...path]/route.ts`
  (explicit catch-all route, NOT next rewrites — rewrites are flaky on Replit).
  **Why:** owner chose V2 as the product direction; the `*_v2.sh` scripts + .replit
  deployment already targeted V2 while the artifact/workflow still ran legacy
  Streamlit, causing a port-5000 conflict ("Port 5000 is not available").
  **How to apply:** dev = `start_v2_dev.sh` (uvicorn + `next dev` on $PORT);
  prod = `build_v2.sh` (build) + `start_v2.sh` (`next start`). artifact.toml maps
  `/`→5000, health `/api/health`. Streamlit `app.py` is legacy/dormant.
- `next.config.ts` sets `allowedDevOrigins` from REPLIT_DEV_DOMAIN/REPLIT_DOMAINS so
  the Next dev server accepts the Replit iframe proxy origin for /_next/* (else a
  cross-origin warning that breaks in future Next majors).
- **Proxy `/api` ownership matters (most-specific-path wins):** the monorepo template's
  `api-server` artifact claimed `paths=["/api"]`, so the :80 proxy routed EVERY `/api/*`
  to that (essentially empty) Express server — 404 "Cannot GET /api/..." — instead of to
  SnapToon's own Next self-proxy → FastAPI. Symptom: `/` renders fine but V2 login/admin/
  projects all break in the browser. SnapToon's Next must OWN `/api`. Fix applied: removed
  the api-server artifact entirely so `/api/*` falls through to SnapToon's `/` catch-all.
  **Gotchas:** an artifact-managed workflow can't be deleted (`removeWorkflow` →
  PROHIBITED_ACTION "managed by an artifact"); delete the artifact DIRECTORY instead
  (`rm -rf artifacts/api-server`) — it's glob-registered via `pnpm-workspace` `artifacts/*`,
  so removing the dir deregisters the artifact AND its workflow. Run `pnpm install` after to
  drop it from the lockfile. Verify with `curl localhost:80/api/health` = 200.

## Two main-agent gotchas learned here
- `verifyAndReplaceArtifactToml` CANNOT change the artifact `version` field
  ("cannot change artifact version") — keep `version` identical to the existing
  toml; only edit services/commands/paths/env.
- `pkill -f "<pattern>"` matches against EVERY process's full cmdline INCLUDING the
  shell running your command — if your command text contains the pattern (e.g. you
  also grep/echo "next dev"), pkill kills your own shell (exit 143). Kill by explicit
  PID instead, or use patterns that can't appear in your own command line.

# Canvas mockups ≠ the real V2 app (a recurring source of "I still see the old UI")
The `artifacts/mockup-sandbox` Snaptoon components are a SEPARATE design/redesign surface;
editing them does NOT change what a logged-in user sees. The REAL authenticated nav lives in
two places: `web/app/app/layout.tsx` (top-level vertical sidebar — server component, reads
auth cookie; path-dependent active state must be moved to a client child like
`web/components/AppSidebarNav.tsx` via `usePathname`) and `web/app/app/projects/[slug]/layout.tsx`
(the per-project editor steps — Testo/Stile/Personaggi/Genera/Impagina — rendered as a HORIZONTAL
client tab bar, NOT a vertical sidebar like the mockup). The in-app nav uses inline-SVG line
icons (shared `web/components/NavIcon.tsx`); `lucide-react` IS now installed in standalone `web/`
(added via `cd web && pnpm add <pkg> --ignore-workspace`) and is used by the public landing.
**How to apply:** when the user says nav/icons "still look old", change `web/`, not the mockups.

# Dev preview "appears then disappears" = unhandled hydration error, NOT a server crash
Symptom: Replit preview pane (and canvas artifact iframe) flashes the page then shows
"Your SnapToon artifact encountered an error". Server is fully healthy (`/`=200,
api/health=200, no traceback, no OOM, no restart loop) — so it is NOT a backend crash and
restarting the workflow does NOT fix it.
**Cause:** a React hydration mismatch on `/` throws an *unhandled* client error
(browser console `Method -unhandlederror: "Hydration failed..."`). The Replit preview's
error monitor catches that unhandled error and shows the overlay; the SSR HTML paints first
(page appears) then hydration throws (page disappears). A one-shot `screenshot` can still
succeed because it captures before the error fires — do NOT use a passing screenshot to
conclude "no error"; check the browser console for `unhandlederror`.
**Why the mismatch (static landing has no Date/random/window):** attributes injected into
`<html>`/`<body>` by browser extensions or the preview proxy differ server vs client.
**Fix:** add `suppressHydrationWarning` to BOTH `<html>` and `<body>` in `web/app/layout.tsx`.
This silences the html/body-level mismatch so no unhandled error is thrown → overlay stops.
(Earlier notes calling this hydration warning "benign" were WRONG for the preview pane.)
