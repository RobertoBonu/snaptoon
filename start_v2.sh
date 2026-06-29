#!/usr/bin/env bash
# Start del nuovo stack SnapToon (FastAPI + Next.js).
# Esegue entrambi in parallelo. Il browser vede solo Next.js (porta 3000),
# Next.js fa proxy a FastAPI (porta 8000, interno al Repl).
#
# Usato dal nuovo deploy quando la migrazione sarà completa.
# Durante la migrazione, lo Streamlit attuale resta attivo via .replit.
set -e

# Avvia FastAPI in background
uvicorn api.main:app --port 8000 --host 0.0.0.0 &
UVICORN_PID=$!
echo "[start_v2] FastAPI started PID=$UVICORN_PID on :8000"

# Avvia Next.js (produzione)
cd web
exec pnpm start
