"""Helper per risolvere la qualità di generazione preferita da un utente.

Applica il ruolo (allowed_qualities) e gestisce "auto" (valido per l'API
OpenAI, costato come medium per semplicità)."""
from __future__ import annotations

from typing import Optional

# Gerarchia di fallback se il preferred non è ammesso dal ruolo
_QUALITY_ORDER: tuple[str, ...] = ("medium", "low", "high", "auto")


def resolve_user_quality(user, override: Optional[str] = None) -> str:
    """Ritorna la qualità effettiva da usare per una generazione.

    Args:
        user: User ORM (deve avere `role` e `preferred_quality`)
        override: se passato, ha priorità sulla preferenza utente
                  (usato per casi speciali tipo admin Test-Style)

    Returns:
        una tra "auto", "low", "medium", "high"
        Se il valore preferito non è ammesso dal ruolo, ripiega su
        "medium" (che è disponibile per tutti i ruoli).
    """
    from billing.plans import ROLE_CONFIG

    requested = (override or getattr(user, "preferred_quality", None) or "medium").strip().lower()
    if requested not in ("auto", "low", "medium", "high"):
        requested = "medium"

    allowed = set(ROLE_CONFIG[user.role].allowed_qualities)
    # "auto" non è nell'allowed_qualities delle role config attuali —
    # lo permettiamo comunque a tutti (delega al modello). Se poi il
    # ruolo non permette high, e il modello sceglie high, si paga
    # medium (vedi cost_for_generation).
    if requested == "auto":
        return "auto"
    if requested in allowed:
        return requested
    # Fallback: prima qualità dell'ordine standard che è ammessa
    for q in _QUALITY_ORDER:
        if q in allowed:
            return q
    return "medium"


def cost_for_generation(operation: str, resolved_quality: str) -> int:
    """Costo in crediti coerente con billing.plans.cost_for_operation.

    "auto" viene costato come "medium" per prevedibilità (l'utente non
    sa in anticipo cosa OpenAI userà). Le altre qualità passano diritte
    al mapping OPERATION_COSTS.
    """
    from billing.plans import cost_for_operation

    q_for_cost = "medium" if resolved_quality == "auto" else resolved_quality
    return cost_for_operation(operation, quality=q_for_cost)
