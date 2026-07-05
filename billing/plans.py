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


@dataclass(frozen=True)
class PlanQuotas:
    """Quote MENSILI per tipo di contenuto (2026-07: nuovo modello).

    Ogni piano definisce quante unità di ciascun tipo l'utente può creare
    OGNI MESE (reset al rinnovo). I pacchetti Extra si sommano DOPO,
    con consumo month-first, extra-second.
    """
    libretti_kids: int = 0
    progetti_pro: int = 0
    cover: int = 0
    card: int = 0


PLAN_CONFIG: dict[Plan, PlanConfig] = {
    Plan.free_to_play: PlanConfig(
        plan=Plan.free_to_play,
        label="Free-To-Play",
        monthly_credits=25,  # legacy: budget per striscia+fig+cover una tantum
        max_projects=1,
        allowed_qualities=("medium",),
        monthly_price_eur=0,
        features=(
            "1 striscia KIDS (1 tavola)",
            "1 figurina collezionabile",
            "1 cover standalone",
            "Qualità Media",
            "Prova gratis, senza carta di credito",
        ),
    ),
    Plan.kids_plan: PlanConfig(
        plan=Plan.kids_plan,
        label="KIDS",
        monthly_credits=100,  # legacy budget crediti
        max_projects=6,  # 1 libretto/mese ma con cast_archive posso avere fino a 6 char
        allowed_qualities=("medium",),
        monthly_price_eur=7,  # €6,99 arrotondato
        features=(
            "1 libretto KIDS al mese (breve o lungo)",
            "5 cover al mese",
            "5 figurine al mese",
            "Qualità Media",
            "Modalità KIDS guidata",
            "Export PDF",
        ),
    ),
    Plan.base: PlanConfig(
        # Il "Base" storico ora si chiama PRO ma il valore enum resta
        # 'base' per non rompere gli utenti esistenti già registrati.
        plan=Plan.base,
        label="PRO",
        monthly_credits=200,
        max_projects=5,
        allowed_qualities=("low", "medium", "high"),
        monthly_price_eur=19,
        features=(
            "5 progetti Pro al mese",
            "1 libretto KIDS al mese",
            "5 cover al mese",
            "5 figurine al mese",
            "Qualità Bassa + Media + Alta",
            "Export PDF",
        ),
    ),
    Plan.premium: PlanConfig(
        plan=Plan.premium,
        label="PRO (legacy Premium)",
        monthly_credits=600,
        max_projects=0,
        allowed_qualities=("low", "medium", "high"),
        monthly_price_eur=49,
        features=(
            "Legacy premium (mantenuto per utenti esistenti)",
        ),
    ),
    # === Legacy (mantenuti per utenti esistenti) ===
    Plan.free_trial: PlanConfig(
        plan=Plan.free_trial,
        label="Free Trial (legacy)",
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
        label="Creator (legacy)",
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
        label="Pro (legacy)",
        monthly_credits=600,
        max_projects=0,
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


# ============================================================
# FREE-TO-PLAY: enforcement per azione (non per credito)
# ============================================================

class FreeToPlayLimitError(Exception):
    """L'utente free_to_play ha esaurito il quota di un'azione FTP."""

    def __init__(self, action: str):
        self.action = action
        super().__init__(f"Free-to-play quota esaurita per '{action}'")


# Le azioni tracciate: chiave = tipo, valore = nome campo counter su User
FTP_ACTIONS = {
    "striscia": "ftp_striscia_used",
    "card": "ftp_card_used",
    "cover": "ftp_cover_used",
}

FTP_LIMIT_PER_ACTION = 1  # 1 utilizzo per tipo


def is_free_to_play(user) -> bool:
    return user.plan == Plan.free_to_play


def check_free_to_play_quota(user, action: str) -> None:
    """Solleva FreeToPlayLimitError se l'utente FTP ha già usato l'azione.

    Chiamare PRIMA di fare la generazione. Se l'utente NON è FTP,
    è un no-op.
    """
    if not is_free_to_play(user):
        return
    field = FTP_ACTIONS.get(action)
    if field is None:
        return
    used = int(getattr(user, field, 0) or 0)
    if used >= FTP_LIMIT_PER_ACTION:
        raise FreeToPlayLimitError(action)


def consume_free_to_play(user, action: str) -> None:
    """Incrementa il contatore per l'azione. Chiamare DOPO successo generazione.

    No-op per utenti non FTP.
    """
    if not is_free_to_play(user):
        return
    field = FTP_ACTIONS.get(action)
    if field is None:
        return
    setattr(user, field, int(getattr(user, field, 0) or 0) + 1)


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
    can_use_kids_mode: bool = False  # accesso al wizard KIDS


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
        can_use_kids_mode=True,
        features=(
            "Accesso pannello admin",
            "10.000 crediti al mese",
            "Progetti illimitati",
            "Tutte le qualità AI",
            "Tutte le funzionalità sbloccate",
            "Modalità Kids",
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
    Role.kids: RoleConfig(
        role=Role.kids,
        label="Kids",
        monthly_credits=100,
        max_projects=5,
        allowed_qualities=("medium",),
        can_use_kids_mode=True,
        features=(
            "100 crediti al mese",
            "5 progetti",
            "Solo qualità Bassa (kids)",
            "Modalità wizard 5-step",
            "3 template (1/2/3 personaggi)",
            "3 stili: Flat / 3D / Manga",
            "Export PDF",
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
