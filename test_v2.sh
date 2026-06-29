#!/usr/bin/env bash
# Test del nuovo stack V2 (FastAPI + Next.js) SENZA toccare Streamlit.
# Streamlit gira sulla porta 5000 (configurata in .streamlit/config.toml).
# Il nuovo stack: FastAPI su 8000, Next.js dev su 3001.
#
# Esegue:
#   1. uvicorn FastAPI in background (porta 8000)
#   2. next dev in background (porta 3001)
#   3. attende 15s che startino
#   4. curl /api/health (deve dire "ok")
#   5. curl / (deve restituire HTML landing con "SnapToon")
#   6. kill background processes
#
# Per testare manualmente nel browser, esegui:
#   cd web && pnpm dev -p 3001
# poi apri https://<repl-domain>:3001/

set -e
cd "$(dirname "$0")"

echo "=== Test V2 stack ==="

# Verifica deps Python
echo "[1/5] Verifica fastapi installato..."
python -c "import fastapi; print(f'  fastapi {fastapi.__version__} OK')" || {
    echo "  ✗ fastapi non installato. Esegui: pip install -r requirements.txt"
    exit 1
}

# Verifica node_modules
echo "[2/5] Verifica next.js installato..."
if [ ! -d "web/node_modules/next" ]; then
    echo "  ✗ node_modules/next mancante. Esegui: cd web && pnpm install"
    exit 1
fi
echo "  next $(cat web/node_modules/next/package.json | grep '"version"' | head -1) OK"

# Start FastAPI
echo "[3/5] Avvio FastAPI su :8000..."
python -m uvicorn api.main:app --port 8000 --host 0.0.0.0 > /tmp/fastapi.log 2>&1 &
UVI_PID=$!
trap "kill $UVI_PID 2>/dev/null; kill $NEXT_PID 2>/dev/null" EXIT

# Start Next.js dev
echo "[4/5] Avvio Next.js dev su :3001..."
cd web
pnpm dev -p 3001 > /tmp/next.log 2>&1 &
NEXT_PID=$!
cd ..

# Aspetta che siano pronti
echo "[5/5] Attendo 15s per startup..."
sleep 15

# Test endpoints
echo ""
echo "=== Risultati ==="
echo ""
echo "→ curl http://localhost:8000/api/health"
curl -s http://localhost:8000/api/health || echo "FAIL"
echo ""
echo ""
echo "→ curl http://localhost:3001/ (primi 500 char)"
curl -s http://localhost:3001/ | head -c 500
echo ""
echo "..."
echo ""

# Cleanup esplicito
kill $UVI_PID 2>/dev/null
kill $NEXT_PID 2>/dev/null
echo ""
echo "Logs salvati in /tmp/fastapi.log e /tmp/next.log"
