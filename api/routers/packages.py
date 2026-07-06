"""Pacchetti extra (quote aggiuntive) + ordini stampa/export.

Utente:
    GET  /api/packages/catalog          → listino completo
    GET  /api/packages/my-quotas        → quote correnti (month + extra)
    POST /api/packages/buy              → acquista pacchetto (mock Stripe)
    GET  /api/packages/mine             → storico acquisti

    POST /api/packages/print            → ordine stampa fisica
    GET  /api/packages/print/mine       → miei ordini stampa

    POST /api/packages/export           → ordine export ePub/Kindle/IDML
    GET  /api/packages/export/mine      → miei ordini export

Admin:
    GET  /api/admin/packages/print      → tutti gli ordini stampa
    POST /api/admin/packages/print/{id}/status  → aggiorna status/tracking
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.admin import require_admin
from api.routers.auth import require_user
from billing.quotas import (
    EXPORT_PRICING,
    EXTRA_PACKAGE_CATALOG,
    PRINT_PRICING,
    QUOTA_LABELS,
    add_extra,
    get_available,
    quotas_for_plan,
)
from db.models import ExportOrder, ExtraPackagePurchase, PrintOrder
from db.repos import users as users_repo
from db.session import session_scope

logger = logging.getLogger(__name__)

router = APIRouter()
admin_router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class ExtraPackageOptionOut(BaseModel):
    package_type: str
    quota_type: str
    quota_type_label: str
    quantity: int
    quality: Optional[str] = None
    price_eur: float
    unit_price_eur: float


class PrintPricingOut(BaseModel):
    copies: int
    price_eur: float
    unit_price_eur: float


class ExportPricingOut(BaseModel):
    format_type: str
    label: str
    price_eur: float
    description: str


class CatalogOut(BaseModel):
    extra_packages: dict[str, list[ExtraPackageOptionOut]]
    print_pricing: list[PrintPricingOut]
    export_pricing: list[ExportPricingOut]


class QuotaStatusOut(BaseModel):
    quota_type: str
    quota_type_label: str
    month_available: int
    month_max: int
    extra_available: int


class MyQuotasOut(BaseModel):
    plan: str
    plan_label: str
    quotas: list[QuotaStatusOut]


class BuyIn(BaseModel):
    # Nuovo formato V03: package_type esatto (es. cover_high_5)
    package_type: str = Field(..., min_length=1)
    mock_stripe_token: str = Field(default="mock_test_token")


class PurchaseOut(BaseModel):
    id: str
    package_type: str
    quantity: int
    price_eur: float
    status: str
    created_at: str


class PurchasesListOut(BaseModel):
    purchases: list[PurchaseOut]


class PrintOrderIn(BaseModel):
    project_id: str
    project_kind: str = Field(..., pattern="^(kids|pro)$")
    copies: int = Field(..., gt=0)
    shipping_address: dict = Field(...)
    mock_stripe_token: str = Field(default="mock_test_token")


class PrintOrderOut(BaseModel):
    id: str
    project_id: str
    project_kind: str
    copies: int
    price_eur: float
    shipping_address: dict
    status: str
    tracking_number: str
    admin_notes: str
    created_at: str


class PrintOrdersListOut(BaseModel):
    orders: list[PrintOrderOut]


class PrintStatusUpdateIn(BaseModel):
    status: str = Field(..., pattern="^(pending|paid|printing|shipped|delivered|cancelled)$")
    tracking_number: Optional[str] = None
    admin_notes: Optional[str] = None


class ExportOrderIn(BaseModel):
    project_id: str
    project_kind: str = Field(..., pattern="^(kids|pro)$")
    format_type: str = Field(..., pattern="^(epub|mobi|idml|bundle_multi|bundle_pro)$")
    mock_stripe_token: str = Field(default="mock_test_token")


class ExportOrderOut(BaseModel):
    id: str
    project_id: str
    project_kind: str
    format_type: str
    price_eur: float
    status: str
    created_at: str


class ExportOrdersListOut(BaseModel):
    orders: list[ExportOrderOut]


# ============================================================
# Utility
# ============================================================


def _catalog_out() -> CatalogOut:
    extra_out: dict[str, list[ExtraPackageOptionOut]] = {}
    for qt, options in EXTRA_PACKAGE_CATALOG.items():
        extra_out[qt] = [
            ExtraPackageOptionOut(
                package_type=o.package_type,
                quota_type=o.quota_type,
                quota_type_label=QUOTA_LABELS.get(o.quota_type, o.quota_type),
                quantity=o.quantity,
                quality=o.quality,
                price_eur=o.price_eur,
                unit_price_eur=round(o.unit_price_eur, 2),
            )
            for o in options
        ]
    return CatalogOut(
        extra_packages=extra_out,
        print_pricing=[
            PrintPricingOut(
                copies=p.copies,
                price_eur=p.price_eur_cents / 100,
                unit_price_eur=round(p.unit_price_eur, 2),
            )
            for p in PRINT_PRICING
        ],
        export_pricing=[
            ExportPricingOut(
                format_type=e.format_type,
                label=e.label,
                price_eur=e.price_eur_cents / 100,
                description=e.description,
            )
            for e in EXPORT_PRICING
        ],
    )


def _find_package_option(package_type: str):
    """Ritorna l'ExtraPackageOption dal catalogo, o None se non esiste."""
    for options in EXTRA_PACKAGE_CATALOG.values():
        for opt in options:
            if opt.package_type == package_type:
                return opt
    return None


def _price_for_print(copies: int) -> Optional[int]:
    for p in PRINT_PRICING:
        if p.copies == copies:
            return p.price_eur_cents
    return None


def _price_for_export(format_type: str) -> Optional[int]:
    for e in EXPORT_PRICING:
        if e.format_type == format_type:
            return e.price_eur_cents
    return None


# ============================================================
# Endpoints utente
# ============================================================


@router.get("/catalog", response_model=CatalogOut)
def get_catalog() -> CatalogOut:
    """Listino pacchetti extra + stampa + export (pubblico)."""
    return _catalog_out()


@router.get("/my-quotas", response_model=MyQuotasOut)
def get_my_quotas(user: dict = Depends(require_user)) -> MyQuotasOut:
    """Quote correnti per ogni tipo (mensile + extra)."""
    from billing.plans import plan_config

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        cfg = plan_config(u.plan)
        plan_quotas = quotas_for_plan(u.plan)
        rows: list[QuotaStatusOut] = []
        for qt, max_month in [
            ("libretti_kids", plan_quotas.libretti_kids),
            ("progetti_pro", plan_quotas.progetti_pro),
            ("cover", plan_quotas.cover),
            ("card", plan_quotas.card),
        ]:
            m, e = get_available(u, qt)
            rows.append(
                QuotaStatusOut(
                    quota_type=qt,
                    quota_type_label=QUOTA_LABELS[qt],
                    month_available=m,
                    month_max=max_month,
                    extra_available=e,
                )
            )
        return MyQuotasOut(
            plan=u.plan.value if hasattr(u.plan, "value") else str(u.plan),
            plan_label=cfg.label,
            quotas=rows,
        )


@router.post("/buy", response_model=PurchaseOut, status_code=status.HTTP_201_CREATED)
def buy_package(
    payload: BuyIn, user: dict = Depends(require_user)
) -> PurchaseOut:
    """Acquisto MOCK di un pacchetto extra. Non c'è addebito reale.

    Nuovo formato V03: il client invia package_type preciso (es. cover_high_5).
    Il backend risale a (quota_type, quantity, prezzo) dal catalogo.
    """
    opt = _find_package_option(payload.package_type)
    if opt is None:
        raise HTTPException(
            status_code=400,
            detail=f"Pacchetto non nel catalogo: {payload.package_type}",
        )

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        purchase = ExtraPackagePurchase(
            user_id=user_id,
            package_type=payload.package_type,
            quantity=opt.quantity,
            price_eur_cents=opt.price_eur_cents,
            stripe_payment_id=payload.mock_stripe_token,
            status="paid",
        )
        s.add(purchase)
        # Incrementa il counter DB (usa il quota_type base, non package_type)
        add_extra(u, opt.quota_type, opt.quantity)
        s.flush()
        return PurchaseOut(
            id=str(purchase.id),
            package_type=payload.package_type,
            quantity=opt.quantity,
            price_eur=opt.price_eur_cents / 100,
            status="paid",
            created_at=purchase.created_at.isoformat(),
        )


@router.get("/mine", response_model=PurchasesListOut)
def list_my_purchases(user: dict = Depends(require_user)) -> PurchasesListOut:
    from sqlalchemy import select

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        stmt = (
            select(ExtraPackagePurchase)
            .where(ExtraPackagePurchase.user_id == user_id)
            .order_by(ExtraPackagePurchase.created_at.desc())
        )
        rows = list(s.execute(stmt).scalars())
        return PurchasesListOut(
            purchases=[
                PurchaseOut(
                    id=str(p.id),
                    package_type=p.package_type,
                    quantity=p.quantity,
                    price_eur=p.price_eur_cents / 100,
                    status=p.status,
                    created_at=p.created_at.isoformat(),
                )
                for p in rows
            ]
        )


# ============================================================
# Print orders
# ============================================================


@router.post("/print", response_model=PrintOrderOut, status_code=status.HTTP_201_CREATED)
def create_print_order(
    payload: PrintOrderIn, user: dict = Depends(require_user)
) -> PrintOrderOut:
    price_cents = _price_for_print(payload.copies)
    if price_cents is None:
        raise HTTPException(
            status_code=400,
            detail=f"Copie non nel listino ({payload.copies}). Per 100+ contatta info@snaptoon.art",
        )
    try:
        proj_uuid = uuid.UUID(payload.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID progetto invalido")

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        order = PrintOrder(
            user_id=user_id,
            project_id=proj_uuid,
            project_kind=payload.project_kind,
            copies=payload.copies,
            price_eur_cents=price_cents,
            shipping_address=payload.shipping_address,
            status="paid",  # mock: subito paid, admin lavora dopo
            stripe_payment_id=payload.mock_stripe_token,
        )
        s.add(order)
        s.flush()
        return PrintOrderOut(
            id=str(order.id),
            project_id=str(order.project_id),
            project_kind=order.project_kind,
            copies=order.copies,
            price_eur=price_cents / 100,
            shipping_address=order.shipping_address,
            status=order.status,
            tracking_number="",
            admin_notes="",
            created_at=order.created_at.isoformat(),
        )


@router.get("/print/mine", response_model=PrintOrdersListOut)
def list_my_print_orders(user: dict = Depends(require_user)) -> PrintOrdersListOut:
    from sqlalchemy import select

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        stmt = (
            select(PrintOrder)
            .where(PrintOrder.user_id == user_id)
            .order_by(PrintOrder.created_at.desc())
        )
        rows = list(s.execute(stmt).scalars())
        return PrintOrdersListOut(
            orders=[
                PrintOrderOut(
                    id=str(o.id),
                    project_id=str(o.project_id),
                    project_kind=o.project_kind,
                    copies=o.copies,
                    price_eur=o.price_eur_cents / 100,
                    shipping_address=o.shipping_address or {},
                    status=o.status,
                    tracking_number=o.tracking_number or "",
                    admin_notes=o.admin_notes or "",
                    created_at=o.created_at.isoformat(),
                )
                for o in rows
            ]
        )


# ============================================================
# Export orders
# ============================================================


@router.post("/export", response_model=ExportOrderOut, status_code=status.HTTP_201_CREATED)
def create_export_order(
    payload: ExportOrderIn, user: dict = Depends(require_user)
) -> ExportOrderOut:
    price_cents = _price_for_export(payload.format_type)
    if price_cents is None:
        raise HTTPException(status_code=400, detail=f"Formato sconosciuto: {payload.format_type}")
    try:
        proj_uuid = uuid.UUID(payload.project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID progetto invalido")

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        order = ExportOrder(
            user_id=user_id,
            project_id=proj_uuid,
            project_kind=payload.project_kind,
            format_type=payload.format_type,
            price_eur_cents=price_cents,
            status="pending",  # mock: rimane pending finché admin/job non lo genera
            stripe_payment_id=payload.mock_stripe_token,
        )
        s.add(order)
        s.flush()
        return ExportOrderOut(
            id=str(order.id),
            project_id=str(order.project_id),
            project_kind=order.project_kind,
            format_type=order.format_type,
            price_eur=price_cents / 100,
            status=order.status,
            created_at=order.created_at.isoformat(),
        )


@router.get("/export/mine", response_model=ExportOrdersListOut)
def list_my_export_orders(user: dict = Depends(require_user)) -> ExportOrdersListOut:
    from sqlalchemy import select

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        stmt = (
            select(ExportOrder)
            .where(ExportOrder.user_id == user_id)
            .order_by(ExportOrder.created_at.desc())
        )
        rows = list(s.execute(stmt).scalars())
        return ExportOrdersListOut(
            orders=[
                ExportOrderOut(
                    id=str(o.id),
                    project_id=str(o.project_id),
                    project_kind=o.project_kind,
                    format_type=o.format_type,
                    price_eur=o.price_eur_cents / 100,
                    status=o.status,
                    created_at=o.created_at.isoformat(),
                )
                for o in rows
            ]
        )


# ============================================================
# Admin
# ============================================================


@admin_router.get("/print", response_model=PrintOrdersListOut)
def admin_list_print_orders(
    _: dict = Depends(require_admin), status_filter: Optional[str] = None
) -> PrintOrdersListOut:
    from sqlalchemy import select

    with session_scope() as s:
        stmt = select(PrintOrder).order_by(PrintOrder.created_at.desc())
        if status_filter:
            stmt = stmt.where(PrintOrder.status == status_filter)
        rows = list(s.execute(stmt).scalars())
        return PrintOrdersListOut(
            orders=[
                PrintOrderOut(
                    id=str(o.id),
                    project_id=str(o.project_id),
                    project_kind=o.project_kind,
                    copies=o.copies,
                    price_eur=o.price_eur_cents / 100,
                    shipping_address=o.shipping_address or {},
                    status=o.status,
                    tracking_number=o.tracking_number or "",
                    admin_notes=o.admin_notes or "",
                    created_at=o.created_at.isoformat(),
                )
                for o in rows
            ]
        )


@admin_router.post("/print/{order_id}/status", response_model=PrintOrderOut)
def admin_update_print_status(
    order_id: str,
    payload: PrintStatusUpdateIn,
    _: dict = Depends(require_admin),
) -> PrintOrderOut:
    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID ordine invalido")
    with session_scope() as s:
        o = s.get(PrintOrder, oid)
        if o is None:
            raise HTTPException(status_code=404, detail="Ordine non trovato")
        o.status = payload.status
        if payload.tracking_number is not None:
            o.tracking_number = payload.tracking_number.strip()[:120]
        if payload.admin_notes is not None:
            o.admin_notes = payload.admin_notes.strip()[:2000]
        return PrintOrderOut(
            id=str(o.id),
            project_id=str(o.project_id),
            project_kind=o.project_kind,
            copies=o.copies,
            price_eur=o.price_eur_cents / 100,
            shipping_address=o.shipping_address or {},
            status=o.status,
            tracking_number=o.tracking_number or "",
            admin_notes=o.admin_notes or "",
            created_at=o.created_at.isoformat(),
        )
