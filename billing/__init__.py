"""SnapToon — billing & quote.

Modulo SENZA integrazione Stripe in MVP. Tutto gestito via admin.

Esposti:
- plans: definizione 3 piani (Free Trial, Creator, Pro) + costi operazioni
- credits: helper sopra db.repos.credits per le pagine
"""

from __future__ import annotations

from .plans import (
    OPERATION_COSTS,
    PLAN_CONFIG,
    PlanConfig,
    cost_for_operation,
    plan_config,
)

__all__ = [
    "OPERATION_COSTS",
    "PLAN_CONFIG",
    "PlanConfig",
    "cost_for_operation",
    "plan_config",
]
