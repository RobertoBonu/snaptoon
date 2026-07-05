"""Endpoint /api/account: profilo, storico crediti, cambio password."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from auth import hash_password
from billing.plans import ROLE_CONFIG, plan_config
from db.repos import credits as credits_repo
from db.repos import users as users_repo
from db.session import session_scope

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class AccountOut(BaseModel):
    id: str
    email: str
    pseudonym: str
    role: str
    is_admin: bool
    plan: str
    plan_label: str
    credits_used: int
    credits_total: int
    credits_remaining: int
    max_projects: int  # 0 = illimitato
    created_at: datetime
    must_change_password: bool
    # Preferenze utente per la generazione immagine
    preferred_quality: str = "medium"
    allowed_qualities: list[str] = []


class UpdateProfileIn(BaseModel):
    pseudonym: Optional[str] = Field(default=None, max_length=80)
    preferred_quality: Optional[str] = Field(
        default=None, pattern="^(auto|low|medium|high)$"
    )


class CreditEntryOut(BaseModel):
    operation: str
    delta: int  # negativo = uso, positivo = grant/refund
    reason: Optional[str] = None
    reference_id: Optional[str] = None
    occurred_at: datetime


class CreditHistoryOut(BaseModel):
    entries: list[CreditEntryOut]


class ChangePasswordIn(BaseModel):
    new_password: str = Field(..., min_length=8)


# ============================================================
# Endpoints
# ============================================================


@router.get("/me", response_model=AccountOut)
def get_account(user: dict = Depends(require_user)) -> AccountOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        cfg = plan_config(u.plan)
        remaining = max(0, u.credits_total_this_period - u.credits_used_this_period)
        # Qualità permesse in base al ruolo (le stringhe raw come "low",
        # "medium", "high"). "auto" è concesso a tutti come override
        # esplicito dell'utente: se il ruolo non supporta "high", ma
        # l'utente sceglie "auto", si paga come medium (vedi
        # api.utils.quality.cost_for_generation).
        allowed = list(ROLE_CONFIG[u.role].allowed_qualities)
        if "auto" not in allowed:
            allowed = allowed + ["auto"]

        return AccountOut(
            id=str(u.id),
            email=u.email,
            pseudonym=(u.pseudonym or ""),
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            is_admin=u.is_admin,
            plan=u.plan.value if hasattr(u.plan, "value") else str(u.plan),
            plan_label=cfg.label,
            credits_used=u.credits_used_this_period,
            credits_total=u.credits_total_this_period,
            credits_remaining=remaining,
            max_projects=cfg.max_projects,
            created_at=u.created_at,
            must_change_password=u.must_change_password,
            preferred_quality=u.preferred_quality or "medium",
            allowed_qualities=allowed,
        )


@router.patch("/me", response_model=AccountOut)
def update_profile(
    payload: UpdateProfileIn, user: dict = Depends(require_user)
) -> AccountOut:
    """Aggiorna il profilo utente (pseudonimo, qualità preferita)."""
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        if payload.pseudonym is not None:
            u.pseudonym = payload.pseudonym.strip()[:80]
        if payload.preferred_quality is not None:
            requested = payload.preferred_quality
            # Verifica ruolo: high non ammesso su ruoli restrittivi
            allowed = set(ROLE_CONFIG[u.role].allowed_qualities) | {"auto"}
            if requested not in allowed:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        f"Qualità '{requested}' non disponibile per il tuo "
                        f"ruolo. Consentite: {sorted(allowed)}."
                    ),
                )
            u.preferred_quality = requested
    return get_account(user)


@router.get("/credits-history", response_model=CreditHistoryOut)
def credit_history(user: dict = Depends(require_user)) -> CreditHistoryOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        entries = credits_repo.get_ledger(s, u, limit=100)
        return CreditHistoryOut(
            entries=[
                CreditEntryOut(
                    operation=(
                        e.operation.value if hasattr(e.operation, "value") else str(e.operation)
                    ),
                    delta=e.delta,
                    reason=e.reason or None,
                    reference_id=e.reference_id,
                    occurred_at=e.occurred_at,
                )
                for e in entries
            ]
        )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordIn, user: dict = Depends(require_user)
) -> None:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        users_repo.set_password_hash(s, u, hash_password(payload.new_password))
        # Reset flag must_change_password (modifica diretta — campo del modello)
        u.must_change_password = False
