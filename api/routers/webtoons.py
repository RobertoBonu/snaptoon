"""Endpoint pubblici per la lettura dei WebToon.

Un WebToon è un ProjectAssetShare con asset_kind='webtoon' e
share_status='published'. Il lettore su /w/{share_id} assembla al
volo:
  - la cover del progetto (in cima)
  - tutte le vignette in ordine narrativo (page.number, panel.number)
  - metadata (titolo, autore, caption)

Nessuna composizione lato server: il frontend impila i singoli PNG.

Endpoints (tutti pubblici):
  GET /api/webtoons/{share_id}                   → metadata + lista panels
  GET /api/webtoons/{share_id}/cover             → bytes cover
  GET /api/webtoons/{share_id}/panel/{p}/{v}     → bytes vignetta
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from db.repos import project_asset_shares as shares_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import users as users_repo
from db.session import session_scope
from storage.client import download_bytes, object_exists
from storage.keys import cover_illustration_key, vignette_key

router = APIRouter()


class WebtoonPanelOut(BaseModel):
    page: int
    panel: int
    url: str


class WebtoonReaderOut(BaseModel):
    id: str
    title: str
    subtitle: str
    author_name: str
    author_role: str
    caption: str
    cover_url: str
    panels: list[WebtoonPanelOut]


class WebtoonCardOut(BaseModel):
    """Card compatta per la griglia BookShop / community."""

    id: str
    title: str
    subtitle: str
    author_name: str
    author_role: str
    caption: str
    cover_url: str
    read_url: str
    panels_count: int
    published_at: Optional[str] = None


class WebtoonListOut(BaseModel):
    webtoons: list[WebtoonCardOut]


@router.get("", response_model=WebtoonListOut)
def list_public_webtoons(limit: int = 60) -> WebtoonListOut:
    """Elenco pubblico dei WebToon approvati, ordinati per data pubblicazione.

    limit: max cards restituite (default 60, safety cap 200).
    Nessuna autenticazione. Usato dal BookShop /bookshop e potenzialmente
    da altri consumer (esplora, dashboard).
    """
    from api.utils.user_display import public_author_name

    cap = max(1, min(limit, 200))

    with session_scope() as s:
        shares = shares_repo.list_published_by_kind(s, "webtoon")
        out: list[WebtoonCardOut] = []
        for share in shares[:cap]:
            project = projects_repo.get_by_id(s, share.project_id)
            if project is None or project.script is None:
                continue
            # Metadata da Cover se disponibili
            cover_orm = project.cover
            title = (cover_orm.title if cover_orm else "") or project.name
            subtitle = (cover_orm.subtitle if cover_orm else "") or ""
            cover_author = (cover_orm.author if cover_orm else "") or ""
            owner = users_repo.get_by_id(s, share.user_id)
            display_author = cover_author or public_author_name(owner)

            # Conta le vignette effettivamente generate
            pyd_script = scripts_repo.load_pydantic(project.script)
            panels_count = 0
            for page in pyd_script.pages:
                for panel in page.panels:
                    if object_exists(vignette_key(project.id, page.number, panel.number)):
                        panels_count += 1

            out.append(
                WebtoonCardOut(
                    id=str(share.id),
                    title=title,
                    subtitle=subtitle,
                    author_name=display_author,
                    author_role=share.share_author_role or "",
                    caption=share.share_caption or "",
                    cover_url=f"/api/webtoons/{share.id}/cover",
                    read_url=f"/w/{share.id}",
                    panels_count=panels_count,
                    published_at=(
                        share.share_moderated_at.isoformat()
                        if share.share_moderated_at
                        else None
                    ),
                )
            )
        return WebtoonListOut(webtoons=out)


def _get_published_webtoon_or_404(share_id: str):
    """Ritorna il ProjectAssetShare se è un webtoon pubblicato, altrimenti 404."""
    try:
        sid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="WebToon non trovato")

    with session_scope() as s:
        share = shares_repo.get_by_id(s, sid)
        if share is None:
            raise HTTPException(status_code=404, detail="WebToon non trovato")
        if share.asset_kind != "webtoon":
            raise HTTPException(status_code=404, detail="WebToon non trovato")
        if share.share_status != "published":
            raise HTTPException(status_code=404, detail="WebToon non pubblico")
        return share.id, share.project_id


@router.get("/{share_id}", response_model=WebtoonReaderOut)
def get_webtoon(share_id: str) -> WebtoonReaderOut:
    from api.utils.user_display import public_author_name

    _, project_id = _get_published_webtoon_or_404(share_id)

    with session_scope() as s:
        # Ricarico anche la share per i metadati di condivisione (caption, role)
        try:
            sid = uuid.UUID(share_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Non trovato")
        share = shares_repo.get_by_id(s, sid)
        if share is None:
            raise HTTPException(status_code=404, detail="Non trovato")

        project = projects_repo.get_by_id(s, project_id)
        if project is None or project.script is None:
            raise HTTPException(status_code=404, detail="Progetto non disponibile")

        owner = users_repo.get_by_id(s, share.user_id)
        author_name = public_author_name(owner)

        # Metadata dalla Cover ORM (title/subtitle/author) con fallback
        cover_orm = project.cover
        title = (cover_orm.title if cover_orm else "") or project.name
        subtitle = (cover_orm.subtitle if cover_orm else "") or ""
        # Se cover.author è compilato, ha priorità sul pseudonym dell'utente
        # (l'utente potrebbe aver scritto il proprio brand nel titolo autore
        # del libretto stesso, diverso dal pseudonimo generale).
        cover_author = (cover_orm.author if cover_orm else "") or ""
        display_author = cover_author or author_name

        # Ordina panels per (page, panel) come da script
        pyd_script = scripts_repo.load_pydantic(project.script)
        panels_out: list[WebtoonPanelOut] = []
        for page in sorted(pyd_script.pages, key=lambda p: p.number):
            for panel in sorted(page.panels, key=lambda p: p.number):
                vk = vignette_key(project.id, page.number, panel.number)
                if not object_exists(vk):
                    continue  # skip vignette non generate
                panels_out.append(
                    WebtoonPanelOut(
                        page=page.number,
                        panel=panel.number,
                        url=f"/api/webtoons/{share_id}/panel/{page.number}/{panel.number}",
                    )
                )

        return WebtoonReaderOut(
            id=share_id,
            title=title,
            subtitle=subtitle,
            author_name=display_author,
            author_role=share.share_author_role or "",
            caption=share.share_caption or "",
            cover_url=f"/api/webtoons/{share_id}/cover",
            panels=panels_out,
        )


@router.get("/{share_id}/cover")
def get_webtoon_cover(share_id: str) -> Response:
    _, project_id = _get_published_webtoon_or_404(share_id)
    key = cover_illustration_key(project_id)
    if not object_exists(key):
        raise HTTPException(status_code=404, detail="Cover non trovata")
    return Response(
        content=download_bytes(key),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/{share_id}/panel/{page_num}/{panel_num}")
def get_webtoon_panel(
    share_id: str, page_num: int, panel_num: int
) -> Response:
    _, project_id = _get_published_webtoon_or_404(share_id)
    vk = vignette_key(project_id, page_num, panel_num)
    if not object_exists(vk):
        raise HTTPException(status_code=404, detail="Vignetta non trovata")
    return Response(
        content=download_bytes(vk),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )
