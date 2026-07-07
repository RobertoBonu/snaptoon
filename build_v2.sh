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
# Rimuove qualsiasi build precedente (dev/turbopack o parziale) per garantire
# un build di produzione PULITO. Un .next stantìo può generare un
# routes-manifest.json senza `dataRoutes`, e `next start` crasha con
# "TypeError: routesManifest.dataRoutes is not iterable" → health check /
# in 500 → l'autoscale manda SIGTERM in loop (crash-loop del deployment).
rm -rf .next
pnpm build

# Guardia: se il manifest non contiene dataRoutes il build è corrotto;
# meglio fallire il deploy qui che servire un'app che va in crash-loop.
if ! grep -q '"dataRoutes"' .next/routes-manifest.json 2>/dev/null; then
    echo "[build_v2] ERRORE: .next/routes-manifest.json privo di dataRoutes (build non valido)." >&2
    exit 1
fi

echo "[build_v2] Build OK."
