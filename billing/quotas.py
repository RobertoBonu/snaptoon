"""Gestione quote per-tipo di contenuto e pacchetti extra.

Nuovo modello economico (2026-07-05):
- Ogni piano ha una QUOTA MENSILE per ciascun tipo (libretti_kids,
  progetti_pro, cover, card). Reset al rinnovo.
- Ogni utente può aggiungere QUOTE EXTRA acquistando Pacchetti.
- Consumo: mensile PRIMA, extra DOPO.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from db.models import Plan


QuotaType = Literal["libretti_kids", "progetti_pro", "cover", "card"]

# Etichette user-friendly per messaggi upsell
QUOTA_LABELS: dict[str, str] = {
    "libretti_kids": "libretto KIDS",
    "progetti_pro": "progetto Pro",
    "cover": "cover",
    "card": "figurina",
}


@dataclass(frozen=True)
class PlanQuotas:
    libretti_kids: int = 0
    progetti_pro: int = 0
    cover: int = 0
    card: int = 0


# ============================================================
# Quote per piano
# ============================================================

PLAN_QUOTAS: dict[Plan, PlanQuotas] = {
    # Free-To-Play: 0 quote mensili (usa i counter ftp_*_used per la
    # dose una-tantum di prova). Vedi billing/plans.py per FTP logic.
    Plan.free_to_play: PlanQuotas(),

    # KIDS (€6,99/mese): 1 libretto + 5 cover + 5 figurine
    Plan.kids_plan: PlanQuotas(
        libretti_kids=1, progetti_pro=0, cover=5, card=5
    ),

    # PRO (€19/mese) — enum 'base' ma label "PRO"
    # 5 progetti pro + 1 libretto kids + 5 cover + 5 figurine
    Plan.base: PlanQuotas(
        libretti_kids=1, progetti_pro=5, cover=5, card=5
    ),

    # Premium legacy (mantenuto)
    Plan.premium: PlanQuotas(
        libretti_kids=2, progetti_pro=10, cover=10, card=10
    ),

    # Legacy (mantenuti)
    Plan.free_trial: PlanQuotas(),
    Plan.creator: PlanQuotas(libretti_kids=1, progetti_pro=5, cover=5, card=5),
    Plan.pro: PlanQuotas(libretti_kids=2, progetti_pro=10, cover=10, card=10),
}


def quotas_for_plan(plan: Plan) -> PlanQuotas:
    return PLAN_QUOTAS.get(plan, PlanQuotas())


# ============================================================
# Consumo quote
# ============================================================


class QuotaExhaustedError(Exception):
    """Sollevata quando month + extra sono a 0 per il tipo richiesto."""

    def __init__(self, quota_type: str):
        self.quota_type = quota_type
        super().__init__(f"Quota esaurita per '{quota_type}'")


def _field_names(quota_type: str) -> tuple[str, str]:
    """Ritorna (month_field, extra_field) sull'User per il tipo."""
    return (f"quota_{quota_type}_month", f"quota_{quota_type}_extra")


def get_available(user, quota_type: str) -> tuple[int, int]:
    """Ritorna (mensile_disponibile, extra_disponibile) per l'utente."""
    month_field, extra_field = _field_names(quota_type)
    return (
        int(getattr(user, month_field, 0) or 0),
        int(getattr(user, extra_field, 0) or 0),
    )


def _is_admin(user) -> bool:
    """L'admin bypassa TUTTE le quote (mensili, extra, FTP)."""
    from db.models import Role
    return user.role == Role.admin


def check_quota(user, quota_type: str) -> None:
    """Solleva QuotaExhaustedError se non c'è quota disponibile.

    Gli admin NON hanno mai limiti — ritorna subito.
    """
    if _is_admin(user):
        return
    m, e = get_available(user, quota_type)
    if m + e <= 0:
        raise QuotaExhaustedError(quota_type)


def consume_quota(user, quota_type: str) -> None:
    """Decrementa 1 unità dalla quota. Mensile PRIMA, extra POI.

    Gli admin NON consumano quota (no-op). Solleva QuotaExhaustedError
    se non disponibile per utenti non-admin. Il chiamante DEVE tenere
    l'user attaccato alla session per persistere il decremento.
    """
    if _is_admin(user):
        return
    month_field, extra_field = _field_names(quota_type)
    m = int(getattr(user, month_field, 0) or 0)
    e = int(getattr(user, extra_field, 0) or 0)
    if m > 0:
        setattr(user, month_field, m - 1)
    elif e > 0:
        setattr(user, extra_field, e - 1)
    else:
        raise QuotaExhaustedError(quota_type)


def add_extra(user, quota_type: str, amount: int) -> None:
    """Aggiunge quantità al counter *_extra (acquisto pacchetto)."""
    _, extra_field = _field_names(quota_type)
    current = int(getattr(user, extra_field, 0) or 0)
    setattr(user, extra_field, current + amount)


def reset_monthly_quotas(user) -> None:
    """Riporta i counter *_month ai valori del piano (chiamare al rinnovo)."""
    qs = quotas_for_plan(user.plan)
    user.quota_libretti_kids_month = qs.libretti_kids
    user.quota_progetti_pro_month = qs.progetti_pro
    user.quota_cover_month = qs.cover
    user.quota_card_month = qs.card
    user.period_started_at = datetime.now(timezone.utc)


# ============================================================
# Pacchetti Extra (catalog)
# ============================================================


@dataclass(frozen=True)
class ExtraPackageOption:
    quota_type: QuotaType
    quantity: int
    price_eur_cents: int  # es. 1200 = €12,00

    @property
    def price_eur(self) -> float:
        return self.price_eur_cents / 100

    @property
    def unit_price_eur(self) -> float:
        return self.price_eur / self.quantity if self.quantity else 0.0


# Listino: per ogni tipo, N opzioni con scala volumi (più compri meno costa)
EXTRA_PACKAGE_CATALOG: dict[str, list[ExtraPackageOption]] = {
    "libretti_kids": [
        ExtraPackageOption("libretti_kids", 1, 499),   # €4,99 → €4,99/cad
        ExtraPackageOption("libretti_kids", 3, 1200),  # €12   → €4,00/cad
        ExtraPackageOption("libretti_kids", 5, 1800),  # €18   → €3,60/cad
        ExtraPackageOption("libretti_kids", 10, 3200), # €32   → €3,20/cad
    ],
    "progetti_pro": [
        ExtraPackageOption("progetti_pro", 1, 999),    # €9,99  → €9,99/cad
        ExtraPackageOption("progetti_pro", 3, 2400),   # €24    → €8,00/cad
        ExtraPackageOption("progetti_pro", 5, 3500),   # €35    → €7,00/cad
        ExtraPackageOption("progetti_pro", 10, 6000),  # €60    → €6,00/cad
    ],
    "cover": [
        ExtraPackageOption("cover", 3, 599),           # €5,99  → €2,00/cad
        ExtraPackageOption("cover", 5, 900),           # €9,00  → €1,80/cad
        ExtraPackageOption("cover", 10, 1600),         # €16,00 → €1,60/cad
    ],
    "card": [
        ExtraPackageOption("card", 3, 499),            # €4,99  → €1,66/cad
        ExtraPackageOption("card", 5, 700),            # €7,00  → €1,40/cad
        ExtraPackageOption("card", 10, 1200),          # €12    → €1,20/cad
    ],
}


# ============================================================
# Stampa fisica (listino copie)
# ============================================================


@dataclass(frozen=True)
class PrintPricing:
    copies: int
    price_eur_cents: int

    @property
    def unit_price_eur(self) -> float:
        return (self.price_eur_cents / 100) / self.copies


PRINT_PRICING: list[PrintPricing] = [
    PrintPricing(copies=1, price_eur_cents=1900),   # €19 (+ spedizione)
    PrintPricing(copies=5, price_eur_cents=6500),   # €65   = €13,00/cad
    PrintPricing(copies=10, price_eur_cents=9900),  # €99   = €9,90/cad
    PrintPricing(copies=25, price_eur_cents=19900), # €199  = €7,96/cad
    PrintPricing(copies=50, price_eur_cents=32900), # €329  = €6,58/cad
    # 100+ = preventivo custom, non nel listino automatico
]


# ============================================================
# Export professionale (listino formati)
# ============================================================


@dataclass(frozen=True)
class ExportPricing:
    format_type: str
    label: str
    price_eur_cents: int
    description: str


EXPORT_PRICING: list[ExportPricing] = [
    ExportPricing(
        "epub", "ePub", 999,
        "Libro digitale universale (Apple Books, Kobo, ecc.)",
    ),
    ExportPricing(
        "mobi", "Kindle (.mobi)", 999,
        "Formato per Amazon KDP",
    ),
    ExportPricing(
        "idml", "IDML (Adobe InDesign)", 1999,
        "Per tipografia professionale",
    ),
    ExportPricing(
        "bundle_multi", "Bundle Multi-formato", 1999,
        "ePub + Kindle + PDF stampa (risparmio 30%)",
    ),
    ExportPricing(
        "bundle_pro", "Bundle Pro", 2999,
        "Tutti i formati + IDML tipografico (risparmio 40%)",
    ),
]
