"""Repository log usage — audit di ogni operazione AI."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AdminAudit, UsageLog, User


def log_operation(
    session: Session,
    *,
    user: User,
    operation: str,
    credits_spent: int = 0,
    success: bool = True,
    error_message: str | None = None,
    latency_ms: int = 0,
    project_id: uuid.UUID | None = None,
) -> UsageLog:
    """Log di una singola operazione AI o azione importante.

    Operations standard:
      - adapt_script, generate_subject
      - generate_panel, generate_cover, generate_reference, generate_variant
      - export_pdf, render_page
    """
    log = UsageLog(
        user_id=user.id,
        project_id=project_id,
        operation=operation,
        credits_spent=credits_spent,
        success=success,
        error_message=error_message,
        latency_ms=latency_ms,
    )
    session.add(log)
    session.flush()
    return log


def recent_logs(
    session: Session, *, limit: int = 100
) -> list[UsageLog]:
    stmt = select(UsageLog).order_by(UsageLog.occurred_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars())


def audit_admin_action(
    session: Session,
    *,
    admin: User,
    action: str,
    target_user_id: uuid.UUID | None = None,
    payload: dict | None = None,
) -> AdminAudit:
    """Audit di un'azione admin (create_user, grant_credits, disable_user, ...)."""
    if not admin.is_admin:
        raise ValueError("Solo admin possono auditare azioni admin.")
    entry = AdminAudit(
        admin_user_id=admin.id,
        action=action,
        target_user_id=target_user_id,
        payload=payload or {},
    )
    session.add(entry)
    session.flush()
    return entry
