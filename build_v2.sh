#!/usr/bin/env bash
# Build del nuovo stack: installa deps Python + Node, build Next.js.
set -e

# Python deps API
pip install --upgrade fastapi 'uvicorn[standard]' 'python-jose[cryptography]' python-multipart sse-starlette

# Frontend
cd web
pnpm install --frozen-lockfile || pnpm install
pnpm build
