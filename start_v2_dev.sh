#!/usr/bin/env bash
# Start dev SnapToon V2 (FastAPI + Next.js) per l'ambiente Replit.
#
# Architettura:
# - FastAPI uvicorn in background sulla porta 8000 (interna, non esposta)
# - Next.js DEV (hot-reload) sulla porta $PORT (esposta da Replit; default 5000)
# - Next.js fa proxy delle chiamate /api/* alla porta 8000
#   (vedi web/app/api/[...path]/route.ts)
set -e

API_PORT="${API_PORT:-8000}"
WEB_PORT="${PORT:-5000}"

echo "[start_v2_dev] Starting FastAPI on :${API_PORT}..."
python -m uvicorn api.main:app \
    --port "${API_PORT}" \
    --host 0.0.0.0 \
    --workers 1 &
UVICORN_PID=$!

# Graceful shutdown: alla chiusura termina anche uvicorn
trap "kill ${UVICORN_PID} 2>/dev/null || true" EXIT

# Aspetta che FastAPI sia up (max 30s)
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${API_PORT}/api/health" >/dev/null 2>&1; then
        echo "[start_v2_dev] FastAPI ready."
        API_READY=1
        break
    fi
    sleep 1
done

if [ "${API_READY:-0}" -ne 1 ]; then
    echo "[start_v2_dev] ERRORE: FastAPI non pronta dopo 30s. Esco." >&2
    exit 1
fi

echo "[start_v2_dev] Starting Next.js dev on :${WEB_PORT}..."
cd web
exec npx next dev --turbopack -p "${WEB_PORT}" -H 0.0.0.0
