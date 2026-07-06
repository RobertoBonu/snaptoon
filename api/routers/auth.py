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

import secrets

from auth import hash_password, login as auth_login
from db.models import Plan, Role
from db.repos import users as users_repo
from db.session import session_scope
from mail.sender import (
    send_email_verification,
    send_welcome_after_verification,
)

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


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    plan: str
    pseudonym: str = ""
    first_name: str = ""
    last_name: str = ""


class RegisterResponse(BaseModel):
    id: str
    email: str
    subscription_status: str
    plan_requested: str
    email_verified: bool
    message: str


class VerifyRequest(BaseModel):
    token: str


class VerifyResponse(BaseModel):
    ok: bool
    email: str
    message: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    is_admin: bool
    must_change_password: bool
    subscription_status: str = "active"


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
            "subscription_status": getattr(user, "subscription_status", "active"),
        }


_ALLOWED_REGISTRATION_PLANS = {"free_to_play", "kids_plan", "base"}


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_endpoint(req: RegisterRequest) -> RegisterResponse:
    """Registra un nuovo utente.

    - free_to_play → attivato SUBITO (nessuna approvazione admin necessaria)
    - kids_plan / base → subscription_status='pending_approval' fino ad admin
    """
    import logging
    import traceback

    logger = logging.getLogger(__name__)
    from billing.plans import plan_config

    if req.plan not in _ALLOWED_REGISTRATION_PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Piano non valido. Consenti: {sorted(_ALLOWED_REGISTRATION_PLANS)}",
        )
    if len(req.password) < 8:
        raise HTTPException(
            status_code=400, detail="Password troppo corta (min 8 caratteri)"
        )

    try:
        plan_enum = Plan(req.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Piano non riconosciuto")
    cfg = plan_config(plan_enum)

    verification_token = ""
    display_name_for_email = ""
    try:
        with session_scope() as s:
            existing = users_repo.get_by_email(s, req.email)
            if existing is not None:
                raise HTTPException(
                    status_code=409,
                    detail="Email già registrata. Prova a fare login.",
                )
            user = users_repo.create_user(
                s,
                email=str(req.email),
                password_hash=hash_password(req.password),
                plan=plan_enum,
                initial_credits=cfg.monthly_credits,
                is_admin=False,
                must_change_password=False,
            )
            user.role = Role.autore_base
            if req.pseudonym.strip():
                user.pseudonym = req.pseudonym.strip()[:80]
            if req.first_name.strip():
                user.first_name = req.first_name.strip()[:80]
            if req.last_name.strip():
                user.last_name = req.last_name.strip()[:80]

            # Email verification: genera token univoco, email NON verificata
            verification_token = secrets.token_urlsafe(32)
            user.email_verified = False
            user.email_verification_token = verification_token
            user.email_verified_at = None

            # Auto-activate free_to_play (piano gratuito, no admin approval)
            # NB: l'account è attivo ma l'email deve essere comunque verificata
            # per fare login.
            is_free = plan_enum == Plan.free_to_play
            if is_free:
                user.subscription_status = "active"
                user.subscription_activated_at = datetime.now(timezone.utc)
                user.subscription_plan_requested = None
                try:
                    from billing.quotas import reset_monthly_quotas
                    reset_monthly_quotas(user)
                except Exception as e:
                    logger.warning("reset_monthly_quotas fallito: %s", e)
            else:
                user.subscription_status = "pending_approval"
                user.subscription_plan_requested = plan_enum

            user_id_str = str(user.id)
            user_email = user.email
            plan_label = cfg.label
            final_status = user.subscription_status
            display_name_for_email = (
                f"{user.first_name} {user.last_name}".strip()
                or user.pseudonym
                or user_email.split("@")[0]
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "REGISTER FAILED plan=%s email=%s: %s\n%s",
            req.plan, req.email, e, traceback.format_exc(),
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"Errore registrazione: {type(e).__name__}: {str(e)[:200]}. "
                "Verifica che le migrazioni DB siano applicate "
                "(alembic upgrade head)."
            ),
        )

    # Invio email di VERIFICA (best-effort, non blocca la registrazione)
    email_sent = False
    try:
        email_sent = send_email_verification(
            user_email, verification_token, display_name_for_email
        )
    except Exception as e:
        logger.error("send_email_verification failed: %s", e)

    return RegisterResponse(
        id=user_id_str,
        email=user_email,
        subscription_status=final_status,
        plan_requested=req.plan,
        email_verified=False,
        message=(
            "Registrazione completata! Ti abbiamo mandato un'email con "
            "il link per verificare il tuo indirizzo."
            if email_sent else
            "Registrazione completata, ma l'invio dell'email è fallito. "
            "Contatta info@snaptoon.art per assistenza."
        ),
    )


class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/resend-verification")
def resend_verification_endpoint(req: ResendVerificationRequest) -> dict:
    """Rispedisce l'email di verifica per un account non ancora verificato."""
    try:
        with session_scope() as s:
            user = users_repo.get_by_email(s, req.email)
            # Per motivi di privacy rispondiamo sempre 200: non riveliamo se
            # l'email esiste o meno.
            if user is None or user.email_verified:
                return {
                    "ok": True,
                    "message": "Se l'account esiste ed è ancora da verificare, ti abbiamo mandato una nuova email.",
                }
            # Genera un nuovo token e sostituisci il vecchio
            new_token = secrets.token_urlsafe(32)
            user.email_verification_token = new_token
            display = (
                f"{user.first_name} {user.last_name}".strip()
                or user.pseudonym or user.email.split("@")[0]
            )
            user_email = user.email
    except Exception as e:
        logger.error("resend_verification failed: %s", e)
        raise HTTPException(status_code=500, detail="Errore interno")

    try:
        send_email_verification(user_email, new_token, display)
    except Exception as e:
        logger.error("send_email_verification (resend) failed: %s", e)

    return {
        "ok": True,
        "message": "Se l'account esiste ed è ancora da verificare, ti abbiamo mandato una nuova email.",
    }


@router.post("/verify", response_model=VerifyResponse)
def verify_email_endpoint(req: VerifyRequest) -> VerifyResponse:
    """Verifica il token contenuto nel link email.

    Su successo:
    - Marca user.email_verified=True
    - Rimuove il token (single-use)
    - Invia la SECONDA email di benvenuto
    """
    from billing.plans import plan_config

    token = req.token.strip()
    if not token or len(token) < 20:
        raise HTTPException(status_code=400, detail="Token invalido o mancante.")

    try:
        from sqlalchemy import select
        from db.models import User

        with session_scope() as s:
            stmt = select(User).where(User.email_verification_token == token)
            user = s.execute(stmt).scalar_one_or_none()
            if user is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Link non valido o già usato. Se hai già verificato "
                        "l'email, fai login."
                    ),
                )

            user.email_verified = True
            user.email_verified_at = datetime.now(timezone.utc)
            user.email_verification_token = None
            user_email = user.email
            first = user.first_name or ""
            last = user.last_name or ""
            pseud = user.pseudonym or ""
            cfg = plan_config(user.plan)
            plan_label = cfg.label
    except HTTPException:
        raise
    except Exception as e:
        logger.error("VERIFY failed: %s\n%s", e, traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Errore verifica: {type(e).__name__}: {str(e)[:150]}",
        )

    # Seconda email: benvenuto post-verifica
    try:
        send_welcome_after_verification(
            user_email, first, last, pseud, plan_label
        )
    except Exception as e:
        logger.error("send_welcome_after_verification failed: %s", e)

    return VerifyResponse(
        ok=True,
        email=user_email,
        message="Email verificata! Ora puoi fare login.",
    )


@router.post("/login", response_model=UserOut)
def login_endpoint(req: LoginRequest, response: Response) -> UserOut:
    with session_scope() as s:
        user = auth_login(s, email=req.email, password=req.password)
        if user is None:
            raise HTTPException(status_code=401, detail="Credenziali non valide")
        # Blocco login se email non ancora verificata (utenti creati DOPO
        # la migrazione d2e3f4a5b6c7). Gli utenti esistenti hanno
        # email_verified=true di default (server_default retrocompat).
        if not getattr(user, "email_verified", True):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Email non ancora verificata. Controlla la tua casella di "
                    "posta e clicca sul link che ti abbiamo inviato."
                ),
            )
        token = _create_access_token(str(user.id))
        user_out = UserOut(
            id=str(user.id),
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            is_admin=user.role == Role.admin,
            must_change_password=user.must_change_password,
            subscription_status=getattr(user, "subscription_status", "active"),
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
