"""Endpoint BookShop.

Struttura:
  Public (no auth):
    GET  /api/bookshop/categories             → categorie raggruppate per macro

  Admin (require_admin):
    GET    /api/admin/bookshop/categories     → tutte (incluse inattive)
    POST   /api/admin/bookshop/categories     → crea
    PATCH  /api/admin/bookshop/categories/{id}
    DELETE /api/admin/bookshop/categories/{id}

Le "macro" sono hardcoded 3 valori (kids | young | kidult) che
corrispondono al target di età. Le sotto-categorie sono libere e
gestite dall'admin.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.admin import require_admin
from db.repos import bookshop_categories as bookshop_repo
from db.session import session_scope

public_router = APIRouter()
admin_router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class CategoryOut(BaseModel):
    id: str
    macro: str
    slug: str
    label: str
    description: str
    position: int
    is_active: bool


class MacroGroupOut(BaseModel):
    macro: str
    label: str
    categories: list[CategoryOut]


class CategoriesListOut(BaseModel):
    macros: list[MacroGroupOut]


class CategoryCreateIn(BaseModel):
    macro: str = Field(..., pattern="^(kids|young|kidult)$")
    slug: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    position: int = 0
    is_active: bool = True


class CategoryUpdateIn(BaseModel):
    macro: Optional[str] = Field(default=None, pattern="^(kids|young|kidult)$")
    label: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = Field(default=None, max_length=1000)
    position: Optional[int] = None
    is_active: Optional[bool] = None


# Etichette IT per le macro (mostrate all'utente)
MACRO_LABELS: dict[str, str] = {
    "kids": "KIDS (bambini)",
    "young": "YOUNG (ragazzi)",
    "kidult": "KIDULT (adulti giovani)",
}


def _to_out(cat) -> CategoryOut:
    return CategoryOut(
        id=str(cat.id),
        macro=cat.macro,
        slug=cat.slug,
        label=cat.label,
        description=cat.description or "",
        position=cat.position,
        is_active=cat.is_active,
    )


def _grouped(cats, *, only_active: bool = False) -> CategoriesListOut:
    """Raggruppa le categorie per macro nell'ordine standard."""
    by_macro: dict[str, list] = {"kids": [], "young": [], "kidult": []}
    for c in cats:
        if only_active and not c.is_active:
            continue
        if c.macro in by_macro:
            by_macro[c.macro].append(_to_out(c))
    return CategoriesListOut(
        macros=[
            MacroGroupOut(
                macro=m,
                label=MACRO_LABELS[m],
                categories=by_macro[m],
            )
            for m in ("kids", "young", "kidult")
        ]
    )


# ============================================================
# Public
# ============================================================


@public_router.get("/categories", response_model=CategoriesListOut)
def list_public_categories() -> CategoriesListOut:
    """Categorie ATTIVE visibili al pubblico del BookShop."""
    with session_scope() as s:
        cats = bookshop_repo.list_all(s, only_active=True)
        return _grouped(cats, only_active=True)


# ============================================================
# Admin
# ============================================================


@admin_router.get("/categories", response_model=CategoriesListOut)
def admin_list_categories(admin: dict = Depends(require_admin)) -> CategoriesListOut:
    with session_scope() as s:
        cats = bookshop_repo.list_all(s, only_active=False)
        return _grouped(cats, only_active=False)


@admin_router.post(
    "/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED
)
def admin_create_category(
    payload: CategoryCreateIn, admin: dict = Depends(require_admin)
) -> CategoryOut:
    with session_scope() as s:
        try:
            cat = bookshop_repo.create(
                s,
                macro=payload.macro,
                slug=payload.slug,
                label=payload.label,
                description=payload.description,
                position=payload.position,
                is_active=payload.is_active,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _to_out(cat)


@admin_router.patch("/categories/{cat_id}", response_model=CategoryOut)
def admin_update_category(
    cat_id: str,
    payload: CategoryUpdateIn,
    admin: dict = Depends(require_admin),
) -> CategoryOut:
    try:
        cid = uuid.UUID(cat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        cat = bookshop_repo.get_by_id(s, cid)
        if cat is None:
            raise HTTPException(status_code=404, detail="Categoria non trovata")
        try:
            bookshop_repo.update(
                s, cat,
                macro=payload.macro,
                label=payload.label,
                description=payload.description,
                position=payload.position,
                is_active=payload.is_active,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return _to_out(cat)


@admin_router.delete(
    "/categories/{cat_id}", status_code=status.HTTP_204_NO_CONTENT
)
def admin_delete_category(
    cat_id: str, admin: dict = Depends(require_admin)
) -> None:
    try:
        cid = uuid.UUID(cat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")

    with session_scope() as s:
        cat = bookshop_repo.get_by_id(s, cid)
        if cat is None:
            raise HTTPException(status_code=404, detail="Categoria non trovata")
        bookshop_repo.soft_delete(s, cat)
