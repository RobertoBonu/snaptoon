"""Endpoint gestione abbonamenti.

Utente:
    GET  /api/subscription/me            → stato abbonamento corrente
    POST /api/subscription/checkout      → checkout mock Stripe: crea richiesta
                                          pending_approval per un nuovo piano
    POST /api/subscription/cancel        → disdetta (status='cancelled')

Admin:
    GET  /api/admin/subscriptions        → lista utenti (filtrabile per status)
    POST /api/admin/subscriptions/{uid}/approve  → attiva + email
    POST /api/admin/subscriptions/{uid}/reject   → rifiuta + email
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.admin import require_admin
from api.routers.auth import require_user
from billing.plans import plan_config
from db.models import Plan, Role
from db.repos import users as users_repo
from db.session import session_scope
from mail.sender import (
    send_registration_confirmation,
    send_subscription_activated,
    send_subscription_rejected,
)

logger = logging.getLogger(__name__)

router = APIRouter()
admin_router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class SubscriptionOut(BaseModel):
    id: str
    email: str
    plan: str
    plan_label: str
    plan_requested: str | None
    plan_requested_label: str | None
    subscription_status: str
    subscription_activated_at: str | None
    subscription_rejection_reason: str
    created_at: str
    credits_total: int
    credits_used: int
    ftp_striscia_used: int
    ftp_card_used: int
    ftp_cover_used: int
    is_free_to_play: bool


class SubscriptionsListOut(BaseModel):
    subscriptions: list[SubscriptionOut]


class CheckoutIn(BaseModel):
    """Checkout MOCK Stripe: nessun pagamento reale.

    Il sistema salva il piano richiesto + mette lo status a
    'pending_approval'. L'admin approva manualmente per ora.
    """

    plan: str = Field(..., pattern="^(free_to_play|base|premium)$")
    # Campi mock Stripe (opzionali, salvati solo per traccia)
    mock_stripe_token: str = Field(default="mock_test_token")


class CheckoutOut(BaseModel):
    ok: bool
    plan_requested: str
    subscription_status: str
    message: str


class RejectIn(BaseModel):
    reason: str = Field(default="", max_length=500)


# ============================================================
# Helpers
# ============================================================


def _to_out(u) -> SubscriptionOut:
    plan_val = u.plan.value if hasattr(u.plan, "value") else str(u.plan)
    cfg = plan_config(u.plan)
    req = u.subscription_plan_requested
    req_val = None
    req_label = None
    if req is not None:
        req_val = req.value if hasattr(req, "value") else str(req)
        try:
            req_label = plan_config(req).label
        except Exception:
            req_label = req_val
    return SubscriptionOut(
        id=str(u.id),
        email=u.email,
        plan=plan_val,
        plan_label=cfg.label,
        plan_requested=req_val,
        plan_requested_label=req_label,
        subscription_status=getattr(u, "subscription_status", "active"),
        subscription_activated_at=(
            u.subscription_activated_at.isoformat()
            if getattr(u, "subscription_activated_at", None) else None
        ),
        subscription_rejection_reason=getattr(u, "subscription_rejection_reason", "") or "",
        created_at=u.created_at.isoformat() if u.created_at else "",
        credits_total=u.credits_total_this_period,
        credits_used=u.credits_used_this_period,
        ftp_striscia_used=int(getattr(u, "ftp_striscia_used", 0) or 0),
        ftp_card_used=int(getattr(u, "ftp_card_used", 0) or 0),
        ftp_cover_used=int(getattr(u, "ftp_cover_used", 0) or 0),
        is_free_to_play=u.plan == Plan.free_to_play,
    )


# ============================================================
# Endpoints utente
# ============================================================


@router.get("/me", response_model=SubscriptionOut)
def get_my_subscription(user: dict = Depends(require_user)) -> SubscriptionOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        return _to_out(u)


@router.post("/checkout", response_model=CheckoutOut)
def checkout(
    payload: CheckoutIn, user: dict = Depends(require_user)
) -> CheckoutOut:
    """Checkout MOCK Stripe. Registra la richiesta cambio piano.

    Non c'è pagamento reale: l'admin approverà manualmente. Se il piano
    richiesto è free_to_play, comunque richiede approvazione admin per
    coerenza col flusso.
    """
    user_id = uuid.UUID(user["id"])
    try:
        req_plan = Plan(payload.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Piano non riconosciuto")

    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        u.subscription_plan_requested = req_plan
        u.subscription_status = "pending_approval"
        u.subscription_rejection_reason = ""
        cfg = plan_config(req_plan)

    # Notifica di ricezione (best-effort)
    try:
        send_registration_confirmation(u.email, cfg.label)
    except Exception as e:
        logger.error("send_registration failed: %s", e)

    return CheckoutOut(
        ok=True,
        plan_requested=payload.plan,
        subscription_status="pending_approval",
        message=(
            "Richiesta ricevuta. Riceverai un'email di conferma quando "
            "il piano sarà attivo."
        ),
    )


@router.post("/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_subscription(user: dict = Depends(require_user)) -> None:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        u.subscription_status = "cancelled"


# ============================================================
# Endpoints admin
# ============================================================


@admin_router.get("", response_model=SubscriptionsListOut)
def admin_list_subscriptions(
    _: dict = Depends(require_admin),
    status_filter: str | None = None,
) -> SubscriptionsListOut:
    from sqlalchemy import select
    from db.models import User

    with session_scope() as s:
        stmt = select(User).order_by(User.created_at.desc())
        if status_filter:
            stmt = stmt.where(User.subscription_status == status_filter)
        users = list(s.execute(stmt).scalars())
        return SubscriptionsListOut(
            subscriptions=[_to_out(u) for u in users]
        )


@admin_router.post("/{user_id}/approve", response_model=SubscriptionOut)
def admin_approve_subscription(
    user_id: str, _: dict = Depends(require_admin)
) -> SubscriptionOut:
    """Approva la richiesta. Applica il piano richiesto e resetta i
    contatori FTP se il nuovo piano non è free_to_play."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID utente invalido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, uid)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        req = u.subscription_plan_requested or u.plan
        cfg = plan_config(req)
        # Applica il piano richiesto e riparte periodo crediti
        u.plan = req
        u.credits_total_this_period = cfg.monthly_credits
        u.credits_used_this_period = 0
        u.subscription_status = "active"
        u.subscription_activated_at = datetime.now(timezone.utc)
        u.subscription_rejection_reason = ""
        # Se il nuovo piano non è free_to_play, i contatori FTP si
        # azzerano (l'utente ha già "consumato" la sua prova gratis)
        if req != Plan.free_to_play:
            u.ftp_striscia_used = 0
            u.ftp_card_used = 0
            u.ftp_cover_used = 0
        out = _to_out(u)

    # Email di attivazione (best-effort)
    try:
        send_subscription_activated(u.email, cfg.label)
    except Exception as e:
        logger.error("send_subscription_activated failed: %s", e)

    return out


@admin_router.post("/{user_id}/reject", response_model=SubscriptionOut)
def admin_reject_subscription(
    user_id: str,
    payload: RejectIn,
    _: dict = Depends(require_admin),
) -> SubscriptionOut:
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID utente invalido")

    with session_scope() as s:
        u = users_repo.get_by_id(s, uid)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        u.subscription_status = "rejected"
        u.subscription_rejection_reason = payload.reason.strip()[:500]
        req = u.subscription_plan_requested or u.plan
        cfg = plan_config(req)
        out = _to_out(u)

    try:
        send_subscription_rejected(u.email, cfg.label, payload.reason)
    except Exception as e:
        logger.error("send_subscription_rejected failed: %s", e)

    return out
