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

# Sotto-tipi di quota per Medium/High (V03).
# I counter DB restano un solo campo per quota_type: quando l'utente
# compra "cover_high", incrementiamo comunque quota_cover_extra ma
# tracciamo la qualità nel record ExtraPackagePurchase.package_type.
QUALITY_PACKAGE_TYPES = {
    "libretti_kids": ["libretti_kids"],
    "progetti_pro": ["progetti_pro_medium", "progetti_pro_high"],
    "cover": ["cover_medium", "cover_high"],
    "card": ["card_medium", "card_high"],
}


def base_quota_type(pkg_type: str) -> str:
    """Ritorna il quota_type DB da un package_type (rimuove _medium/_high)."""
    for base, subs in QUALITY_PACKAGE_TYPES.items():
        if pkg_type in subs or pkg_type == base:
            return base
    return pkg_type


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
    # V03 (piano commerciale definitivo):
    #
    # Free-To-Play (gratis, una-tantum via counter ftp_*_used):
    #   1 striscia + 1 figurina + 1 cover. Vedi billing/plans.py per FTP logic.
    Plan.free_to_play: PlanQuotas(),

    # KIDS (€6,99/mese): 1 libretto + 2 cover + 2 figurine (tutto Medium)
    Plan.kids_plan: PlanQuotas(
        libretti_kids=1, progetti_pro=0, cover=2, card=2
    ),

    # PRO (€19/mese) — enum 'base' ma label "PRO":
    # 1 progetto Pro + 3 cover + 3 figurine (Medium o High)
    # NO libretto KIDS incluso (V03: rimosso).
    Plan.base: PlanQuotas(
        libretti_kids=0, progetti_pro=1, cover=3, card=3
    ),

    # Legacy Premium (utenti esistenti): mantenuto generoso
    Plan.premium: PlanQuotas(
        libretti_kids=1, progetti_pro=3, cover=5, card=5
    ),

    # Legacy (mantenuti)
    Plan.free_trial: PlanQuotas(),
    Plan.creator: PlanQuotas(libretti_kids=1, progetti_pro=5, cover=5, card=5),
    Plan.pro: PlanQuotas(libretti_kids=2, progetti_pro=10, cover=10, card=10),
}


# ============================================================
# Welcome bonus (1° mese)
# ============================================================
#
# Al primo attivamento di un piano a pagamento (KIDS o PRO), l'utente
# riceve delle quote EXTRA una tantum come "welcome bonus". Si sommano
# ai counter *_extra (non scadono, ma sono pensate per esaurirsi nel
# primo mese come incentivo di conversione).

WELCOME_BONUS: dict[Plan, PlanQuotas] = {
    Plan.kids_plan: PlanQuotas(libretti_kids=0, progetti_pro=0, cover=5, card=5),
    Plan.base:      PlanQuotas(libretti_kids=0, progetti_pro=0, cover=10, card=10),
}


def welcome_bonus_for(plan: Plan) -> PlanQuotas:
    return WELCOME_BONUS.get(plan, PlanQuotas())


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


def reset_monthly_quotas(user, *, apply_welcome_bonus: bool = False) -> None:
    """Riporta i counter *_month ai valori del piano (chiamare al rinnovo).

    Se apply_welcome_bonus=True (di solito al PRIMO attivamento del piano
    a pagamento), aggiunge il welcome bonus del piano ai counter *_extra.
    """
    qs = quotas_for_plan(user.plan)
    user.quota_libretti_kids_month = qs.libretti_kids
    user.quota_progetti_pro_month = qs.progetti_pro
    user.quota_cover_month = qs.cover
    user.quota_card_month = qs.card
    user.period_started_at = datetime.now(timezone.utc)

    if apply_welcome_bonus:
        wb = welcome_bonus_for(user.plan)
        user.quota_libretti_kids_extra = int(getattr(user, "quota_libretti_kids_extra", 0) or 0) + wb.libretti_kids
        user.quota_progetti_pro_extra = int(getattr(user, "quota_progetti_pro_extra", 0) or 0) + wb.progetti_pro
        user.quota_cover_extra = int(getattr(user, "quota_cover_extra", 0) or 0) + wb.cover
        user.quota_card_extra = int(getattr(user, "quota_card_extra", 0) or 0) + wb.card


# ============================================================
# Pacchetti Extra (catalog)
# ============================================================


@dataclass(frozen=True)
class ExtraPackageOption:
    """Un'opzione di pacchetto extra.

    package_type: identificatore preciso salvato in ExtraPackagePurchase.
        Es. "libretti_kids", "cover_medium", "cover_high",
        "progetti_pro_medium", "progetti_pro_high", "card_medium", "card_high".
    quota_type: quale counter DB (quota_*_extra) viene incrementato.
        Sempre il "base type" (libretti_kids/progetti_pro/cover/card).
        La qualità è tracciata solo nel package_type del record purchase.
    quality: "medium" | "high" | None (per libretti KIDS, sempre medium).
    """
    package_type: str
    quota_type: str
    quantity: int
    price_eur_cents: int
    quality: str | None = None

    @property
    def price_eur(self) -> float:
        return self.price_eur_cents / 100

    @property
    def unit_price_eur(self) -> float:
        return self.price_eur / self.quantity if self.quantity else 0.0


# Listino V03 — Piano Commerciale definitivo.
# Solo unità singola per libretti/progetti; +1 o 5x per cover/figurine.
# Cover e figurine hanno prezzi diversi tra Medium e High.
EXTRA_PACKAGE_CATALOG: dict[str, list[ExtraPackageOption]] = {
    # Libretti KIDS extra: solo unità singola, sempre medium
    "libretti_kids": [
        ExtraPackageOption("libretti_kids", "libretti_kids", 1, 499),   # +1 €4,99
    ],
    # Progetti Pro extra: Medium o High, solo unità singola
    "progetti_pro": [
        ExtraPackageOption("progetti_pro_medium", "progetti_pro", 1, 799, "medium"),   # +1 Medium €7,99
        ExtraPackageOption("progetti_pro_high",   "progetti_pro", 1, 1499, "high"),    # +1 High €14,99
    ],
    # Cover extra: Medium/High × 1 o 5
    "cover": [
        ExtraPackageOption("cover_medium",   "cover", 1, 149, "medium"),   # +1 Medium €1,49
        ExtraPackageOption("cover_medium_5", "cover", 5, 499, "medium"),   # 5 Medium €4,99
        ExtraPackageOption("cover_high",     "cover", 1, 399, "high"),     # +1 High €3,99
        ExtraPackageOption("cover_high_5",   "cover", 5, 1200, "high"),    # 5 High €12,00
    ],
    # Figurine extra: Medium/High × 1 o 5
    "card": [
        ExtraPackageOption("card_medium",   "card", 1, 129, "medium"),    # +1 Medium €1,29
        ExtraPackageOption("card_medium_5", "card", 5, 449, "medium"),    # 5 Medium €4,49
        ExtraPackageOption("card_high",     "card", 1, 299, "high"),      # +1 High €2,99
        ExtraPackageOption("card_high_5",   "card", 5, 1000, "high"),     # 5 High €10,00
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
