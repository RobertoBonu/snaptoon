"""Definizione dei piani di abbonamento + costi operazioni.

Pricing roadmap (MVP):
- Free Trial: 7 giorni, 30 crediti, 1 progetto, qualità Media
- Creator:    €19/mese,  200 crediti, 5 progetti, qualità Bassa+Media
- Pro:        €49/mese,  600 crediti, ∞ progetti, qualità Bassa+Media+Alta

Tutti i piani senza Stripe in MVP: admin assegna manualmente da pannello.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from db.models import Plan


@dataclass(frozen=True)
class PlanConfig:
    """Configurazione di un piano: limiti + qualità ammesse + features."""

    plan: Plan
    label: str
    monthly_credits: int
    max_projects: int  # 0 = illimitato
    allowed_qualities: tuple[str, ...]
    features: tuple[str, ...]
    trial_days: int | None = None
    monthly_price_eur: int | None = None  # None per Free Trial


PLAN_CONFIG: dict[Plan, PlanConfig] = {
    Plan.free_trial: PlanConfig(
        plan=Plan.free_trial,
        label="Free Trial",
        monthly_credits=30,
        max_projects=1,
        allowed_qualities=("medium",),
        trial_days=7,
        monthly_price_eur=None,
        features=(
            "30 crediti totali",
            "1 progetto",
            "Qualità Media",
            "7 giorni di prova",
        ),
    ),
    Plan.creator: PlanConfig(
        plan=Plan.creator,
        label="Creator",
        monthly_credits=200,
        max_projects=5,
        allowed_qualities=("low", "medium"),
        monthly_price_eur=19,
        features=(
            "200 crediti al mese",
            "5 progetti",
            "Qualità Bassa + Media",
            "Export PDF",
        ),
    ),
    Plan.pro: PlanConfig(
        plan=Plan.pro,
        label="Pro",
        monthly_credits=600,
        max_projects=0,  # illimitato
        allowed_qualities=("low", "medium", "high"),
        monthly_price_eur=49,
        features=(
            "600 crediti al mese",
            "Progetti illimitati",
            "Qualità Bassa + Media + Alta",
            "Export PDF",
            "Priorità di generazione",
        ),
    ),
}


def plan_config(plan: Plan) -> PlanConfig:
    return PLAN_CONFIG[plan]


# ============================================================
# COSTI OPERAZIONI (in crediti)
# ============================================================
#
# 1 credito = 1 immagine Media (1024x1024 con OpenAI gpt-image-2 quality medium).
# Operazioni più care/economiche ricavate dal rapporto reale di costi API.

OPERATION_COSTS: dict[str, int] = {
    # Image generation (per quality)
    "generate_panel_low": 1,        # 0.3 → arrotondato a 1 per semplicità
    "generate_panel_medium": 1,
    "generate_panel_high": 4,

    "generate_cover_low": 1,
    "generate_cover_medium": 1,
    "generate_cover_high": 4,

    "generate_reference": 1,         # sempre Media (slot 1)
    "generate_variant": 1,           # sempre Media (slot 2-7)

    # Claude (text)
    "adapt_script": 5,
    "generate_subject": 5,

    # Gratis (operazioni locali)
    "render_page": 0,
    "export_pdf": 0,
    "edit_balloon": 0,
}


def cost_for_operation(operation: str, *, quality: str | None = None) -> int:
    """Restituisce il costo in crediti per un'operazione.

    Per image-gen passare anche `quality` (low/medium/high). Per altre operazioni
    il quality è ignorato.
    """
    if operation in ("generate_panel", "generate_cover"):
        if quality is None:
            quality = "medium"
        key = f"{operation}_{quality}"
        if key not in OPERATION_COSTS:
            raise ValueError(f"Quality '{quality}' non supportata per {operation}.")
        return OPERATION_COSTS[key]

    if operation not in OPERATION_COSTS:
        raise ValueError(f"Operazione '{operation}' non riconosciuta.")
    return OPERATION_COSTS[operation]


def quality_allowed_for_plan(plan: Plan, quality: str) -> bool:
    return quality in PLAN_CONFIG[plan].allowed_qualities


def project_limit_reached(plan: Plan, current_count: int) -> bool:
    """True se l'utente ha raggiunto il limite di progetti del suo piano."""
    cfg = PLAN_CONFIG[plan]
    if cfg.max_projects == 0:
        return False  # illimitato
    return current_count >= cfg.max_projects
