"""Endpoint admin: gestione utenti, crediti, stats.

Tutte le route richiedono user.is_admin = True.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
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
