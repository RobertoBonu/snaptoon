---
name: SnapToon environment quirks
description: Non-obvious env/routing/setup facts for the SnapToon Streamlit app in the pnpm-workspace artifact monorepo
---

# Streamlit reachability through the artifact proxy
The workspace preview is served by a global reverse proxy on port 80 that routes
ONLY by each artifact's `.replit-artifact/artifact.toml` `paths` (most-specific-first,
paths are NOT rewritten). A bare Streamlit workflow on port 5000 is unreachable —
the proxy has no route to it, so `/` returns 404 and the preview shows
"We couldn't reach this app".

**Fix:** register the Streamlit app as a `kind = "web"` artifact at `artifacts/snaptoon`
with a service `localPort = 5000`, `paths = ["/"]`. This makes the proxy route `/`
(and Streamlit's `/_stcore/*`, `/static/*`) to 5000 while `/api` still hits the api-server.

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

# Other env facts
- Runtime is Python 3.11 (NOT 3.13). Install deps via the package-management skill
  (`installLanguagePackages`, uv-backed); raw `pip install` times out (exit -1).
- Alembic needs repo root on PYTHONPATH: `PYTHONPATH="$PWD" alembic ...` or it fails
  with `No module named 'db'`.
- For ad hoc curl always use `http://localhost:80` (the proxy), never service ports directly.
- `screenshot` app_preview only works for registered artifacts; verify Streamlit via
  curl/logs (HTTP 200 on `/` and `/_stcore/health`) instead.
