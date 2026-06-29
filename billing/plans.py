"""Definizione di ruoli (autoritativi per permessi) e piani (legacy).

I 4 ruoli e i loro limiti:
- admin           : 10000 crediti/mese, tutto sbloccato
- autore_base     : 200  crediti/mese, max 5 progetti, qualità Bassa+Media
- autore_premium  : 600  crediti/mese, ∞ progetti, anche qualità Alta
- editore         : 1000 crediti/mese, ∞ progetti, tutto + IDML export (futuro)

PLAN_CONFIG resta come legacy tracking commerciale (Free Trial / Creator / Pro)
ma i permessi reali sono ora basati su ROLE_CONFIG.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from db.models import Plan, Role


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
# ROLE-BASED CONFIG (autoritativo)
# ============================================================


@dataclass(frozen=True)
class RoleConfig:
    """Configurazione di un ruolo: limiti + qualità ammesse + features."""

    role: Role
    label: str
    monthly_credits: int
    max_projects: int  # 0 = illimitato
    allowed_qualities: tuple[str, ...]
    features: tuple[str, ...]
    can_access_admin: bool = False
    can_use_bookshop: bool = False
    can_export_idml: bool = False


ROLE_CONFIG: dict[Role, RoleConfig] = {
    Role.admin: RoleConfig(
        role=Role.admin,
        label="Admin",
        monthly_credits=10000,
        max_projects=0,
        allowed_qualities=("low", "medium", "high"),
        can_access_admin=True,
        can_use_bookshop=True,
        can_export_idml=True,
        features=(
            "Accesso pannello admin",
            "10.000 crediti al mese",
            "Progetti illimitati",
            "Tutte le qualità AI",
            "Tutte le funzionalità sbloccate",
        ),
    ),
    Role.autore_base: RoleConfig(
        role=Role.autore_base,
        label="Autore Base",
        monthly_credits=200,
        max_projects=5,
        allowed_qualities=("low", "medium"),
        features=(
            "200 crediti al mese",
            "5 progetti",
            "Qualità Bassa + Media",
            "Export PDF",
        ),
    ),
    Role.autore_premium: RoleConfig(
        role=Role.autore_premium,
        label="Autore Premium",
        monthly_credits=600,
        max_projects=0,
        allowed_qualities=("low", "medium", "high"),
        features=(
            "600 crediti al mese",
            "Progetti illimitati",
            "Qualità Bassa + Media + Alta",
            "Export PDF",
            "Priorità di generazione",
        ),
    ),
    Role.editore: RoleConfig(
        role=Role.editore,
        label="Editore",
        monthly_credits=1000,
        max_projects=0,
        allowed_qualities=("low", "medium", "high"),
        can_use_bookshop=True,
        can_export_idml=True,
        features=(
            "1.000 crediti al mese",
            "Progetti illimitati",
            "Qualità Bassa + Media + Alta",
            "Pubblicazione nel bookshop",
            "Export IDML tipografico (Adobe InDesign)",
        ),
    ),
}


def role_config(role: Role) -> RoleConfig:
    return ROLE_CONFIG[role]


def quality_allowed_for_role(role: Role, quality: str) -> bool:
    return quality in ROLE_CONFIG[role].allowed_qualities


def project_limit_reached_for_role(role: Role, current_count: int) -> bool:
    cfg = ROLE_CONFIG[role]
    if cfg.max_projects == 0:
        return False
    return current_count >= cfg.max_projects


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
