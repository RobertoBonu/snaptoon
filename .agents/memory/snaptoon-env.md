---
name: SnapToon env & preview quirks
description: How the root Streamlit app runs/previews inside this pnpm-workspace artifact monorepo, plus alembic/pip gotchas
---

# SnapToon environment quirks

SnapToon is a **root-level Streamlit app** (`app.py`, `pages/`, `db/`, `auth/`, ...) living inside a pnpm-workspace artifact monorepo that also contains template artifacts (`artifacts/api-server`, `artifacts/mockup-sandbox`).

## Preview / routing
- There is **no Streamlit artifact type** — SnapToon cannot be registered via `createArtifact`. It runs as a plain **webview workflow** ("Start application") via `streamlit run app.py --server.port 5000 ...`. The Run button (`runButton = "Project"`) drives this.
- The public dev domain (`$REPLIT_DEV_DOMAIN`) `/` is served by the **artifact proxy → api-server (returns 404)**, NOT Streamlit. The Streamlit webview on port 5000 is only reachable through the workspace Run/preview, not the artifact dev-domain root.
- **`screenshot` app_preview only targets registered artifacts** (api-server, mockup-sandbox). It CANNOT screenshot the Streamlit webview. To verify Streamlit, curl `localhost:5000/_stcore/health` (200) and check workflow logs; verify data/logic headlessly instead of via screenshot.
- Use port **5000** (in supported workflow ports). `.streamlit/config.toml` pins 8501 which is NOT a supported workflow port — override with `--server.port 5000`.

## Python deps
- `pip install -r requirements.txt` via bash **times out / returns exit -1 with no output**. Use the package-management skill (`installLanguagePackages({language:"python", packages:[...]})`, uv-backed) instead. Installs land in `.pythonlibs/lib/python3.11/...`. Runtime is **Python 3.11**, not 3.13.

## Alembic
- Migrations live in `db/migrations` (`script_location = db/migrations` in `alembic.ini`); `env.py` imports `from db.base import Base`. Running `alembic` fails with `ModuleNotFoundError: No module named 'db'` unless you prefix `PYTHONPATH="$PWD"`. Always run: `PYTHONPATH="$PWD" alembic revision --autogenerate ...` / `upgrade head`.

## Ownership boundary
- Replit Agent owns ONLY the visual layer + `app.py` markup/wiring. NEVER modify `auth/`, `db/`, `billing/`, `storage/`, `snaptoon_core/`, `scripts/`, `requirements.txt` — only **call** their functions. See `docs/design/07_REPLIT_AGENT.md`. All git ops are blocked in the agent sandbox; the user runs git in Shell.
