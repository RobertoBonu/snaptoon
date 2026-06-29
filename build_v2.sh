#!/usr/bin/env bash
# Build SnapToon V2: deps Python + frontend Next.js prod build.
set -e

echo "[build_v2] Installing Python deps..."
pip install --quiet \
    fastapi \
    'uvicorn[standard]' \
    'python-jose[cryptography]' \
    python-multipart \
    sse-starlette \
    email-validator

echo "[build_v2] Building Next.js..."
cd web
pnpm install --frozen-lockfile --ignore-workspace 2>/dev/null \
    || pnpm install --ignore-workspace
pnpm build

echo "[build_v2] Build OK."
