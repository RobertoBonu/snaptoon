"""Endpoint admin: gestione utenti, crediti, stats.

Tutte le route richiedono user.is_admin = True.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field

from api.routers.auth import require_user
from auth import hash_password
from billing.plans import ROLE_CONFIG, role_config
from db.models import CreditOperation, Plan, Role
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import users as users_repo
from db.session import session_scope

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class AdminUserOut(BaseModel):
    id: str
    email: str
    role: str
    is_admin: bool
    is_active: bool
    plan: str
    credits_total: int
    credits_used: int
    credits_remaining: int
    must_change_password: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    project_count: int


class AdminUserListOut(BaseModel):
    users: list[AdminUserOut]


class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    admin_count: int
    users_by_role: dict[str, int]
    total_projects: int
    active_last_7_days: int


class CreateUserIn(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=200)
    role: str = "autore_base"
    must_change_password: bool = True


class UpdateRoleIn(BaseModel):
    role: str
    reset_credits: bool = False


class GrantCreditsIn(BaseModel):
    amount: int = Field(..., ge=1, le=10000)
    reason: str = Field(default="Admin grant", max_length=200)


class ResetPasswordIn(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=200)


# ============================================================
# Dependency: require admin
# ============================================================


def require_admin(user: dict = Depends(require_user)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=403, detail="Solo admin può accedere a questa risorsa"
        )
    return user


# ============================================================
# Helpers
# ============================================================


def _user_to_out(u, project_count: int = 0) -> AdminUserOut:
    return AdminUserOut(
        id=str(u.id),
        email=u.email,
        role=u.role.value if hasattr(u.role, "value") else str(u.role),
        is_admin=(u.role == Role.admin),
        is_active=u.is_active,
        plan=u.plan.value if hasattr(u.plan, "value") else str(u.plan),
        credits_total=u.credits_total_this_period,
        credits_used=u.credits_used_this_period,
        credits_remaining=max(
            0, u.credits_total_this_period - u.credits_used_this_period
        ),
        must_change_password=u.must_change_password,
        created_at=u.created_at,
        last_login_at=u.last_login_at,
        project_count=project_count,
    )


# ============================================================
# Endpoints
# ============================================================


@router.get("/users", response_model=AdminUserListOut)
def list_users(admin: dict = Depends(require_admin)) -> AdminUserListOut:
    with session_scope() as s:
        users = users_repo.list_all(s, include_inactive=True)
        return AdminUserListOut(
            users=[
                _user_to_out(
                    u, project_count=projects_repo.count_by_owner(s, u.id)
                )
                for u in users
            ]
        )


@router.get("/stats", response_model=AdminStatsOut)
def get_stats(admin: dict = Depends(require_admin)) -> AdminStatsOut:
    with session_scope() as s:
        users = users_repo.list_all(s, include_inactive=True)
        total = len(users)
        active = sum(1 for u in users if u.is_active)
        admins = sum(1 for u in users if u.role == Role.admin)
        by_role: dict[str, int] = {}
        total_projects = 0
        for u in users:
            r = u.role.value if hasattr(u.role, "value") else str(u.role)
            by_role[r] = by_role.get(r, 0) + 1
            total_projects += projects_repo.count_by_owner(s, u.id)
        active_last_7 = users_repo.count_active_in_last_days(s, days=7)
        return AdminStatsOut(
            total_users=total,
            active_users=active,
            admin_count=admins,
            users_by_role=by_role,
            total_projects=total_projects,
            active_last_7_days=active_last_7,
        )


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserIn, admin: dict = Depends(require_admin)
) -> AdminUserOut:
    try:
        role = Role(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Ruolo invalido: {payload.role}")
    cfg = role_config(role)

    with session_scope() as s:
        existing = users_repo.get_by_email(s, payload.email)
        if existing is not None:
            raise HTTPException(status_code=409, detail="Email già registrata")
        u = users_repo.create_user(
            s,
            email=payload.email,
            password_hash=hash_password(payload.password),
            plan=Plan.free_trial,  # default; admin può cambiare
            initial_credits=cfg.monthly_credits,
            is_admin=(role == Role.admin),
            must_change_password=payload.must_change_password,
        )
        users_repo.set_role(s, u, role)
        return _user_to_out(u, project_count=0)


@router.patch("/users/{user_id}/role", response_model=AdminUserOut)
def update_user_role(
    user_id: str, payload: UpdateRoleIn, admin: dict = Depends(require_admin)
) -> AdminUserOut:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")
    try:
        role = Role(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Ruolo invalido: {payload.role}")

    with session_scope() as s:
        u = users_repo.get_by_id(s, uid)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        cfg = role_config(role)
        reset = cfg.monthly_credits if payload.reset_credits else None
        users_repo.set_role(s, u, role, reset_period_credits=reset)
        return _user_to_out(u, project_count=projects_repo.count_by_owner(s, u.id))


@router.post("/users/{user_id}/grant-credits", response_model=AdminUserOut)
def grant_credits(
    user_id: str, payload: GrantCreditsIn, admin: dict = Depends(require_admin)
) -> AdminUserOut:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")
    with session_scope() as s:
        u = users_repo.get_by_id(s, uid)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        credits_repo.grant(
            s, u,
            amount=payload.amount,
            operation=CreditOperation.admin_grant,
            reason=payload.reason,
        )
        return _user_to_out(u, project_count=projects_repo.count_by_owner(s, u.id))


@router.post("/users/{user_id}/reset-password", response_model=AdminUserOut)
def reset_password(
    user_id: str, payload: ResetPasswordIn, admin: dict = Depends(require_admin)
) -> AdminUserOut:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")
    with session_scope() as s:
        u = users_repo.get_by_id(s, uid)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        u.password_hash = hash_password(payload.new_password)
        u.must_change_password = True
        return _user_to_out(u, project_count=projects_repo.count_by_owner(s, u.id))


@router.patch("/users/{user_id}/active", response_model=AdminUserOut)
def set_active(
    user_id: str, active: bool, admin: dict = Depends(require_admin)
) -> AdminUserOut:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID invalido")
    with session_scope() as s:
        u = users_repo.get_by_id(s, uid)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        users_repo.set_active(s, u, active)
        return _user_to_out(u, project_count=projects_repo.count_by_owner(s, u.id))


@router.get("/roles")
def list_roles(admin: dict = Depends(require_admin)) -> dict:
    """Ritorna i ruoli disponibili + config (per dropdown frontend)."""
    return {
        "roles": [
            {
                "key": r.value,
                "label": ROLE_CONFIG[r].label,
                "monthly_credits": ROLE_CONFIG[r].monthly_credits,
                "max_projects": ROLE_CONFIG[r].max_projects,
            }
            for r in Role
        ]
    }


# ============================================================
# Sistema — logo e testo default per quarta di copertina
# Solo admin può modificare. Gli utenti finali lo ricevono già valorizzato.
# ============================================================


_ACCEPTED_LOGO_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
_MAX_LOGO_SIZE = 4 * 1024 * 1024  # 4 MB


class SystemSettingsOut(BaseModel):
    has_logo: bool
    default_copyright_text: str
    back_cover_template: str


@router.get("/system-settings", response_model=SystemSettingsOut)
def get_system_settings(admin: dict = Depends(require_admin)) -> SystemSettingsOut:
    from storage.client import download_bytes, object_exists
    from storage.keys import (
        ADMIN_BACK_COVER_TEMPLATE_KEY,
        ADMIN_DEFAULT_COPYRIGHT_KEY,
        ADMIN_LOGO_KEY,
    )

    default_copyright = ""
    if object_exists(ADMIN_DEFAULT_COPYRIGHT_KEY):
        try:
            default_copyright = download_bytes(ADMIN_DEFAULT_COPYRIGHT_KEY).decode(
                "utf-8"
            )
        except Exception:
            pass

    template = ""
    if object_exists(ADMIN_BACK_COVER_TEMPLATE_KEY):
        try:
            template = download_bytes(ADMIN_BACK_COVER_TEMPLATE_KEY).decode(
                "utf-8"
            )
        except Exception:
            pass

    return SystemSettingsOut(
        has_logo=object_exists(ADMIN_LOGO_KEY),
        default_copyright_text=default_copyright,
        back_cover_template=template,
    )


class SystemTextsIn(BaseModel):
    default_copyright_text: Optional[str] = Field(default=None, max_length=1000)
    back_cover_template: Optional[str] = Field(default=None, max_length=2000)


@router.patch("/system-settings", response_model=SystemSettingsOut)
def update_system_settings(
    payload: SystemTextsIn, admin: dict = Depends(require_admin)
) -> SystemSettingsOut:
    """Aggiorna testi default per quarta di copertina.

    default_copyright_text: proposto come suggerimento sotto il campo
      copyright quando l'utente crea un nuovo libretto.
    back_cover_template: template testo per la sezione "note editore"
      sulla quarta di copertina di ogni libretto (opzionale).
    """
    from storage.client import object_exists, upload_bytes
    from storage.keys import (
        ADMIN_BACK_COVER_TEMPLATE_KEY,
        ADMIN_DEFAULT_COPYRIGHT_KEY,
        ADMIN_LOGO_KEY,
    )

    if payload.default_copyright_text is not None:
        upload_bytes(
            ADMIN_DEFAULT_COPYRIGHT_KEY,
            payload.default_copyright_text.encode("utf-8"),
            content_type="text/plain",
        )
    if payload.back_cover_template is not None:
        upload_bytes(
            ADMIN_BACK_COVER_TEMPLATE_KEY,
            payload.back_cover_template.encode("utf-8"),
            content_type="text/plain",
        )

    return get_system_settings(admin)


@router.post("/logo")
async def upload_system_logo(
    file: UploadFile = File(...), admin: dict = Depends(require_admin)
) -> SystemSettingsOut:
    """Carica il logo di sistema (usato in copertina e quarta di ogni libretto).

    Sostituisce il precedente. PNG/JPEG/WEBP max 4 MB.
    """
    from storage.client import upload_bytes
    from storage.keys import ADMIN_LOGO_KEY

    if file.content_type not in _ACCEPTED_LOGO_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Formato non supportato ({file.content_type}). Usa PNG, JPEG o WEBP.",
        )
    data = await file.read()
    if len(data) > _MAX_LOGO_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Logo troppo grande (max {_MAX_LOGO_SIZE // (1024*1024)} MB).",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="File vuoto.")

    upload_bytes(ADMIN_LOGO_KEY, data, content_type=file.content_type)
    return get_system_settings(admin)


@router.delete("/logo", status_code=status.HTTP_204_NO_CONTENT)
def delete_system_logo(admin: dict = Depends(require_admin)) -> None:
    from storage.client import delete_object
    from storage.keys import ADMIN_LOGO_KEY

    delete_object(ADMIN_LOGO_KEY)


@router.get("/logo")
def get_system_logo(admin: dict = Depends(require_admin)) -> Response:
    """Ritorna i bytes del logo per la preview admin."""
    from storage.client import download_bytes, object_exists
    from storage.keys import ADMIN_LOGO_KEY

    if not object_exists(ADMIN_LOGO_KEY):
        raise HTTPException(status_code=404, detail="Logo non impostato")
    return Response(content=download_bytes(ADMIN_LOGO_KEY), media_type="image/png")


# Endpoint pubblico: gli utenti kids lo usano per mostrare il logo nella
# preview della quarta di copertina. Non richiede admin, solo utente
# autenticato per non esporre il logo pubblicamente.
_public_router = APIRouter()


@_public_router.get("/logo")
def get_public_system_logo(user: dict = Depends(require_user)) -> Response:
    from storage.client import download_bytes, object_exists
    from storage.keys import ADMIN_LOGO_KEY

    if not object_exists(ADMIN_LOGO_KEY):
        raise HTTPException(status_code=404, detail="Logo non impostato")
    return Response(content=download_bytes(ADMIN_LOGO_KEY), media_type="image/png")


@_public_router.get("/default-copyright")
def get_public_default_copyright(user: dict = Depends(require_user)) -> dict:
    """Ritorna il testo copyright default (utilizzato come placeholder nel wizard)."""
    from storage.client import download_bytes, object_exists
    from storage.keys import ADMIN_DEFAULT_COPYRIGHT_KEY

    if not object_exists(ADMIN_DEFAULT_COPYRIGHT_KEY):
        return {"text": ""}
    try:
        return {
            "text": download_bytes(ADMIN_DEFAULT_COPYRIGHT_KEY).decode("utf-8")
        }
    except Exception:
        return {"text": ""}


# Il router pubblico verrà montato su /api/system in main.py.
