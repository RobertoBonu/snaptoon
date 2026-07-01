"""Endpoint auth: login, logout, me.

Riusa la funzione di login esistente in auth/ (bcrypt) ma sostituisce la
sessione Streamlit con JWT in httpOnly cookie.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from auth import login as auth_login
from db.models import Role
from db.repos import users as users_repo
from db.session import session_scope

router = APIRouter()

# JWT config
#
# JWT_SECRET firma i cookie di sessione: se prevedibile, un attaccante può
# forgiare token e impersonare qualsiasi utente (incluso admin).
#
# Strategia:
# - Su Replit (env REPL_ID o REPLIT_DEPLOYMENT presenti) → JWT_SECRET DEVE
#   esistere, altrimenti l'app si rifiuta di partire (fail-fast).
# - In dev locale (no Replit env) → fallback su una stringa esplicita di
#   sviluppo, con warning chiaro nei log.
def _resolve_jwt_secret() -> str:
    env_secret = os.getenv("JWT_SECRET", "").strip()
    is_replit = bool(os.getenv("REPL_ID") or os.getenv("REPLIT_DEPLOYMENT"))
    if env_secret:
        return env_secret
    if is_replit:
        raise RuntimeError(
            "JWT_SECRET non impostato. Aggiungi un Replit Secret 'JWT_SECRET' "
            "con una stringa random lunga (>=32 chars). Genera con: "
            "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    # Solo dev locale fuori da Replit
    import warnings
    warnings.warn(
        "JWT_SECRET non impostato — uso fallback DEV. NON usare in produzione.",
        stacklevel=2,
    )
    return "snaptoon-dev-local-only-DO-NOT-USE-IN-PRODUCTION"


JWT_SECRET = _resolve_jwt_secret()
JWT_ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 giorni
COOKIE_NAME = "snaptoon_token"

# In produzione (deployment Replit su HTTPS) il cookie DEVE essere Secure:
# altrimenti browser come Safari/iOS possono rifiutare di persisterlo, con il
# risultato che il login viene accettato dal server (200) ma la sessione non
# viene salvata nel browser → "il login non funziona". In dev locale (HTTP) deve
# restare False, altrimenti il cookie non verrebbe mai inviato su http://localhost.
# REPLIT_DEPLOYMENT è presente SOLO nei deployment, non nel workspace di sviluppo
# (REPL_ID invece è presente anche in dev, quindi non è utilizzabile qui).
COOKIE_SECURE = bool(os.getenv("REPLIT_DEPLOYMENT"))


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    is_admin: bool
    must_change_password: bool


def _create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": int(expire.timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def _decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return str(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_user(snaptoon_token: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict:
    """FastAPI dependency: ritorna i dati utente o solleva 401.

    Returns dict {id, email, role, is_admin, must_change_password} così le
    altre route possono usarlo senza riaprire la sessione DB.
    """
    if snaptoon_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id_str = _decode_token(snaptoon_token)
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    with session_scope() as s:
        user = users_repo.get_by_id(s, user_uuid)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return {
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            # is_admin è DERIVATO dal ruolo (single source of truth): la colonna
            # legacy users.is_admin può desincronizzarsi (es. UPDATE manuale del
            # solo `role`), causando "role=admin ma niente accesso admin".
            "is_admin": user.role == Role.admin,
            "must_change_password": user.must_change_password,
        }


@router.post("/login", response_model=UserOut)
def login_endpoint(req: LoginRequest, response: Response) -> UserOut:
    with session_scope() as s:
        user = auth_login(s, email=req.email, password=req.password)
        if user is None:
            raise HTTPException(status_code=401, detail="Credenziali non valide")
        token = _create_access_token(str(user.id))
        user_out = UserOut(
            id=str(user.id),
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            is_admin=user.role == Role.admin,
            must_change_password=user.must_change_password,
        )
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return user_out


@router.post("/logout")
def logout_endpoint(response: Response) -> dict:
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me_endpoint(user: dict = Depends(require_user)) -> UserOut:
    return UserOut(**user)
