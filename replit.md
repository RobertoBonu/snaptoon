# [Project name]

_Replace the heading above with the project's name, and this line with one sentence describing what this app does for users._

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

_Populate as you build — short repo map plus pointers to the source-of-truth file for DB schema, API contracts, theme files, etc._

## Architecture decisions

_Populate as you build — non-obvious choices a reader couldn't infer from the code (3-5 bullets)._

## Product

_Describe the high-level user-facing capabilities of this app once they exist._

## User preferences

- Lingua: l'utente (Roberto) comunica in italiano; rispondere sempre in italiano.
- Lavoro di design: toccare SOLO `style/custom.css`, `.streamlit/config.toml`, `components/ui/login_form.py`. NON modificare `app.py` né la logica di autenticazione.
- Sync GitHub: dopo ogni modifica di file, allineare GitHub e confermare in chat con lo SHA. Vincoli reali (vedi `.agents/memory/snaptoon-env.md`): `git commit` e `git config`/`set-url` sono bloccati nel main agent (Replit committa da solo a fine turno con messaggio auto-generato). Il token GitHub è nel secret `GITHUB_TOKEN`, NON nell'URL. Push col credential helper effimero sull'URL pulito: `git -c credential.helper='!f() { echo username=x-access-token; echo "password=$GITHUB_TOKEN"; }; f' push https://github.com/RobertoBonu/snaptoon.git main` (il push trasferisce i dati anche se esce non-zero per il lock locale; successo = riga `..main -> main`). Verifica con `git ls-remote`.

## Gotchas

_Populate as you build — sharp edges, "always run X before Y" rules._

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
