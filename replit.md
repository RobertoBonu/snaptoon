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
- Sync GitHub: dopo ogni modifica di file, allineare il remote `origin/main` su GitHub e confermare in chat con lo SHA del commit. Vincoli reali dell'ambiente (vedi Gotchas): `git commit` diretto è bloccato (Replit committa in automatico a fine turno via checkpoint, con messaggio auto-generato, non personalizzabile in "design: ..."); `git push origin main` invece funziona e raggiunge GitHub. Poiché il commit automatico avviene a fine turno, il push delle modifiche del turno va eseguito all'opportunità successiva, riconciliando sempre così GitHub combaci col workspace.

## Gotchas

_Populate as you build — sharp edges, "always run X before Y" rules._

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
