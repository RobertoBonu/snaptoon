"""Repository billing crediti — credit ledger immutabile + balance check.

Tutti i movimenti crediti (entrate e uscite) passano da `record_movement`
per garantire atomicità: aggiornamento `credits_used_this_period`
+ append al ledger nella STESSA transazione.

Filosofia:
- Il "saldo corrente" è sempre derivato da:
    credits_total_this_period - credits_used_this_period
  Mai modificarlo direttamente.
- Il ledger è append-only: serve come audit/log + per ricostruire la storia.
- Errori durante operazione AI → `record_refund` per ripristinare il credito.
"""

from __future__ import annotations

import uuid
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CreditLedger, CreditOperation, User


class InsufficientCreditsError(Exception):
    """Sollevato quando un'operazione costa più del saldo disponibile."""

    def __init__(self, *, required: int, available: int) -> None:
        super().__init__(f"Servono {required} crediti ma ne hai {available}.")
        self.required = required
        self.available = available


def get_balance(user: User) -> int:
    """Saldo corrente. Derivato, non da query."""
    return user.credits_remaining


def can_afford(user: User, cost: int) -> bool:
    return get_balance(user) >= cost


def assert_can_afford(user: User, cost: int) -> None:
    """Solleva InsufficientCreditsError se non basta."""
    available = get_balance(user)
    if available < cost:
        raise InsufficientCreditsError(required=cost, available=available)


def _record_movement(
    session: Session,
    *,
    user: User,
    delta: int,
    operation: CreditOperation,
    reason: str = "",
    reference_id: str | None = None,
) -> CreditLedger:
    """Movimento atomico: aggiorna user + appende ledger.

    `delta` positivo = accredito; negativo = consumo.
    """
    if delta == 0:
        raise ValueError("Movimento credito con delta=0 non ha senso.")

    # Aggiorna user
    if delta < 0:
        # Consumo: aggiungo a credits_used_this_period
        user.credits_used_this_period += -delta
    else:
        # Entrata: aumento il totale del periodo
        user.credits_total_this_period += delta

    balance = user.credits_remaining

    # Appende ledger
    ledger = CreditLedger(
        user_id=user.id,
        delta=delta,
        operation=operation,
        reference_id=reference_id,
        balance_after=balance,
        reason=reason,
    )
    session.add(ledger)
    session.flush()
    return ledger


def charge(
    session: Session,
    user: User,
    *,
    cost: int,
    operation: CreditOperation,
    reason: str = "",
    reference_id: str | None = None,
) -> CreditLedger:
    """Addebito di N crediti per operazione AI.

    Pre-flight check: solleva InsufficientCreditsError se non basta.
    """
    if cost <= 0:
        raise ValueError("cost deve essere > 0 (usa grant per accrediti).")
    assert_can_afford(user, cost)
    return _record_movement(
        session,
        user=user,
        delta=-cost,
        operation=operation,
        reason=reason,
        reference_id=reference_id,
    )


def grant(
    session: Session,
    user: User,
    *,
    amount: int,
    operation: CreditOperation,
    reason: str = "",
    reference_id: str | None = None,
) -> CreditLedger:
    """Accredito di N crediti (admin grant, rinnovo periodo, mock purchase)."""
    if amount <= 0:
        raise ValueError("amount deve essere > 0.")
    return _record_movement(
        session,
        user=user,
        delta=amount,
        operation=operation,
        reason=reason,
        reference_id=reference_id,
    )


def refund(
    session: Session,
    user: User,
    *,
    amount: int,
    reason: str = "",
    reference_id: str | None = None,
) -> CreditLedger:
    """Rimborso post-failure (es. generazione vignetta fallita)."""
    if amount <= 0:
        raise ValueError("amount deve essere > 0.")
    return _record_movement(
        session,
        user=user,
        delta=amount,
        operation=CreditOperation.refund,
        reason=reason,
        reference_id=reference_id,
    )


def get_ledger(
    session: Session, user: User, *, limit: int = 50
) -> list[CreditLedger]:
    stmt = (
        select(CreditLedger)
        .where(CreditLedger.user_id == user.id)
        .order_by(CreditLedger.occurred_at.desc())
        .limit(limit)
    )
    return list(session.execute(stmt).scalars())


def total_consumed_in_period(
    session: Session, user: User, since
) -> int:
    """Somma dei consumi (delta negativi) dal momento `since`. Per dashboard admin."""
    stmt = (
        select(CreditLedger)
        .where(CreditLedger.user_id == user.id)
        .where(CreditLedger.occurred_at >= since)
        .where(CreditLedger.delta < 0)
    )
    return sum(-row.delta for row in session.execute(stmt).scalars())
