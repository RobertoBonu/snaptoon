"""FastAPI entrypoint per SnapToon.

Importa moduli esistenti da auth/, billing/, db/, storage/, snaptoon_core/.
Espone API REST consumate dal frontend Next.js (proxy via /api/* su porta 3000).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Aggiungo project root al path per importare i moduli backend esistenti
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import account as account_router
from api.routers import admin as admin_router
from api.routers import auth as auth_router
from api.routers import characters as characters_router
from api.routers import esplora as esplora_router
from api.routers import kids as kids_router
from api.routers import kids_generation as kids_gen_router
from api.routers import pages as pages_router
from api.routers import projects as projects_router
from api.routers import script as script_router
from api.routers import styles as styles_router
from api.routers import vignettes as vignettes_router

app = FastAPI(
    title="SnapToon API",
    version="0.1.0",
    description="Backend SnapToon — comics + KIDS",
)

# CORS: solo per dev quando Next.js gira separato. In produzione il proxy
# Next.js (rewrites) tiene tutto same-origin, quindi non serve.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects_router.router, prefix="/api/projects", tags=["projects"])
app.include_router(account_router.router, prefix="/api/account", tags=["account"])
app.include_router(kids_router.router, prefix="/api/kids", tags=["kids"])
app.include_router(kids_gen_router.router, prefix="/api/kids", tags=["kids-generation"])
app.include_router(script_router.router, prefix="/api", tags=["script"])
app.include_router(styles_router.router, prefix="/api/styles", tags=["styles"])
app.include_router(characters_router.router, prefix="/api", tags=["characters"])
app.include_router(vignettes_router.router, prefix="/api", tags=["vignettes"])
app.include_router(pages_router.router, prefix="/api", tags=["pages"])
app.include_router(admin_router.router, prefix="/api/admin", tags=["admin"])
app.include_router(esplora_router.public_router, prefix="/api/esplora", tags=["esplora"])
app.include_router(
    esplora_router.admin_router, prefix="/api/admin/esplora", tags=["esplora-admin"]
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "snaptoon-api"}
