#!/usr/bin/env bash
# Start del nuovo stack SnapToon V2 (FastAPI + Next.js).
#
# Architettura su Replit:
# - FastAPI uvicorn in background sulla porta 8000 (interna, non esposta)
# - Next.js prod sulla porta $PORT (esposta da Replit; default 5000)
# - Next.js fa proxy delle chiamate /api/* alla porta 8000 (vedi
#   web/next.config.ts)
#
# Replit Autoscale assegna automaticamente la porta in $PORT.
set -e

# Defaults (override via env)
API_PORT="${API_PORT:-8000}"
WEB_PORT="${PORT:-5000}"

echo "[start_v2] Starting FastAPI on :${API_PORT}..."
python -m uvicorn api.main:app \
    --port "${API_PORT}" \
    --host 0.0.0.0 \
    --workers 1 &
UVICORN_PID=$!

# Graceful shutdown
trap "kill ${UVICORN_PID} 2>/dev/null || true" EXIT

# Aspetta che FastAPI sia up (max 30s)
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${API_PORT}/api/health" >/dev/null 2>&1; then
        echo "[start_v2] FastAPI ready."
        break
    fi
    sleep 1
done

echo "[start_v2] Starting Next.js on :${WEB_PORT}..."
cd web
exec npx next start --port "${WEB_PORT}" --hostname 0.0.0.0
