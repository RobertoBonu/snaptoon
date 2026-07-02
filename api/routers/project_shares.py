"""Endpoint condivisione community di cover e tavole (Pro + KIDS).

Un utente può proporre alla community:
  - la COPERTINA del suo progetto (kind='cover')
  - una TAVOLA impaginata del suo progetto (kind='tavola', page_number)

L'admin approva/rifiuta. Approvato → visibile su /esplora.

Endpoints:
  POST /api/project-shares/cover/{project_id_or_slug}
  POST /api/project-shares/tavola/{project_id_or_slug}/{page_number}
  DELETE /api/project-shares/{share_id}                   (ritira)
  GET /api/project-shares/mine                            (lista propria)

Admin (require_admin):
  GET  /api/admin/esplora/project-shares?status_filter=pending
  GET  /api/admin/esplora/project-shares/{id}/image
  POST /api/admin/esplora/project-shares/{id}/approve
  POST /api/admin/esplora/project-shares/{id}/reject
"""
from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.routers.admin import require_admin
from api.routers.auth import require_user
from db.repos import project_asset_shares as shares_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import users as users_repo
from db.repos import vignettes as vignettes_repo
from db.session import session_scope
from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import cover_illustration_key, page_render_key, vignette_key

logger = logging.getLogger(__name__)

router = APIRouter()
admin_router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class ProjectShareOut(BaseModel):
    id: str
    project_id: str
    project_title: str
    project_flow: str
    asset_kind: str
    page_number: Optional[int] = None
    caption: str
    author_role: str
    share_status: str
    submitted_at: Optional[str]
    moderated_at: Optional[str]
    rejection_reason: str
    image_url: str


class ShareCoverIn(BaseModel):
    caption: str = Field(default="", max_length=500)
    author_role: str = Field(default="", max_length=80)


class ShareTavolaIn(BaseModel):
    caption: str = Field(default="", max_length=500)
    author_role: str = Field(default="", max_length=80)


class ShareAdminOut(BaseModel):
    id: str
    project_id: str
    project_title: str
    project_flow: str
    asset_kind: str
    page_number: Optional[int] = None
    author_name: str
    author_email: str
    author_role: str
    caption: str
    submitted_at: Optional[str]
    moderated_at: Optional[str]
    rejection_reason: str
    share_status: str
    image_url: str


class RejectIn(BaseModel):
    reason: str = Field(default="", max_length=1000)


# ============================================================
# Helpers
# ============================================================


def _to_out(share, base_url: str = "/api/project-shares") -> ProjectShareOut:
    return ProjectShareOut(
        id=str(share.id),
        project_id=str(share.project_id),
        project_title=share.project_title or "",
        project_flow=share.project_flow or "pro",
        asset_kind=share.asset_kind,
        page_number=share.page_number,
        caption=share.share_caption or "",
        author_role=share.share_author_role or "",
        share_status=share.share_status,
        submitted_at=(
            share.share_submitted_at.isoformat() if share.share_submitted_at else None
        ),
        moderated_at=(
            share.share_moderated_at.isoformat() if share.share_moderated_at else None
        ),
        rejection_reason=share.share_rejection_reason or "",
        image_url=f"{base_url}/{share.id}/image",
    )


def _to_admin_out(share, owner) -> ShareAdminOut:
    author_name = ""
    author_email = ""
    if owner and owner.email:
        author_email = owner.email
        author_name = owner.email.split("@")[0]
    return ShareAdminOut(
        id=str(share.id),
        project_id=str(share.project_id),
        project_title=share.project_title or "",
        project_flow=share.project_flow or "pro",
        asset_kind=share.asset_kind,
        page_number=share.page_number,
        author_name=author_name,
        author_email=author_email,
        author_role=share.share_author_role or "",
        caption=share.share_caption or "",
        submitted_at=(
            share.share_submitted_at.isoformat() if share.share_submitted_at else None
        ),
        moderated_at=(
            share.share_moderated_at.isoformat() if share.share_moderated_at else None
        ),
        rejection_reason=share.share_rejection_reason or "",
        share_status=share.share_status,
        image_url=f"/api/admin/esplora/project-shares/{share.id}/image",
    )


def _load_project_by_id_or_slug(session, user_id: uuid.UUID, key: str):
    """Accetta sia UUID che slug, ritorna il Project (owned) o solleva 404."""
    project = None
    try:
        pid = uuid.UUID(key)
        project = projects_repo.get_by_id(session, pid)
        if project is not None and project.owner_user_id != user_id:
            project = None
    except ValueError:
        project = projects_repo.get_by_slug(session, user_id, key)
    if project is None:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    return project


def _detect_flow(project) -> str:
    """kids se lo style_id è uno di quelli KIDS, altrimenti pro."""
    try:
        from snaptoon_core.kids_pipeline import KIDS_STYLE_PRESET_IDS

        if project.style_id and project.style_id in KIDS_STYLE_PRESET_IDS:
            return "kids"
    except Exception:
        pass
    return "pro"


def _render_and_cache_tavola(project, page_number: int) -> str:
    """Rende la tavola N in PNG e la salva in object storage.

    Ritorna la storage_key. Rilancia HTTPException se manca lo script o
    layout.
    """
    from snaptoon_core.layout import GRIDS, render_page

    if project.script is None:
        raise HTTPException(status_code=400, detail="Script mancante")

    pyd = scripts_repo.load_pydantic(project.script)
    target_page = next((p for p in pyd.pages if p.number == page_number), None)
    if target_page is None:
        raise HTTPException(status_code=404, detail=f"Pagina {page_number} non trovata")

    layouts = {pl.page_number: pl for pl in project.page_layouts}
    pl = layouts.get(page_number)
    grid_id = pl.grid_id if pl else "2x2"
    show_balloons = pl.show_balloons if pl else True
    grid = GRIDS.get(grid_id)
    if grid is None:
        raise HTTPException(status_code=400, detail=f"Grid non valido: {grid_id}")

    # Prepara i panel paths
    tmp_files: list[Path] = []
    try:
        panel_paths: list[tuple] = []
        for panel in target_page.panels:
            vk = vignette_key(project.id, page_number, panel.number)
            if object_exists(vk):
                data = download_bytes(vk)
                tf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tf.write(data)
                tf.close()
                p = Path(tf.name)
                tmp_files.append(p)
                panel_paths.append((panel, p))
            else:
                panel_paths.append((panel, None))

        out_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        out_tmp.close()
        out_path = Path(out_tmp.name)
        tmp_files.append(out_path)

        # Per KIDS balloon già bake-ati dentro le vignette, per Pro dipende
        # dall'impaginazione utente. Usiamo il valore su pl.show_balloons.
        render_page(
            panels_with_images=panel_paths,
            grid=grid,
            out_path=out_path,
            show_balloons=show_balloons,
        )

        rendered_bytes = out_path.read_bytes()
    finally:
        for tf in tmp_files:
            try:
                tf.unlink()
            except OSError:
                pass

    key = page_render_key(project.id, page_number)
    upload_bytes(key, rendered_bytes, content_type="image/png")
    return key


# ============================================================
# Endpoint utente
# ============================================================


@router.post(
    "/cover/{project_key}", response_model=ProjectShareOut, status_code=201
)
def share_cover(
    project_key: str,
    payload: ShareCoverIn,
    user: dict = Depends(require_user),
) -> ProjectShareOut:
    """Condividi la copertina del progetto (Pro o KIDS)."""
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        project = _load_project_by_id_or_slug(s, user_id, project_key)
        ck = cover_illustration_key(project.id)
        if not object_exists(ck):
            raise HTTPException(
                status_code=400,
                detail="Genera prima la copertina, poi condividi.",
            )
        share = shares_repo.submit(
            s,
            project=project,
            user=u,
            asset_kind="cover",
            page_number=None,
            storage_key=ck,
            project_flow=_detect_flow(project),
            caption=payload.caption,
            author_role=payload.author_role,
        )
        return _to_out(share)


@router.post(
    "/tavola/{project_key}/{page_number}",
    response_model=ProjectShareOut,
    status_code=201,
)
def share_tavola(
    project_key: str,
    page_number: int,
    payload: ShareTavolaIn,
    user: dict = Depends(require_user),
) -> ProjectShareOut:
    """Condividi la tavola N del progetto. Renderizza on-demand se necessario."""
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        project = _load_project_by_id_or_slug(s, user_id, project_key)
        # Renderizza la tavola on-demand (idempotente su file già presente)
        key = _render_and_cache_tavola(project, page_number)
        share = shares_repo.submit(
            s,
            project=project,
            user=u,
            asset_kind="tavola",
            page_number=page_number,
            storage_key=key,
            project_flow=_detect_flow(project),
            caption=payload.caption,
            author_role=payload.author_role,
        )
        return _to_out(share)


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def unshare(share_id: str, user: dict = Depends(require_user)) -> None:
    user_id = uuid.UUID(user["id"])
    try:
        sid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        share = shares_repo.get_by_user_and_id(s, u, sid) if u else None
        if share is None:
            raise HTTPException(status_code=404, detail="Share non trovata")
        shares_repo.unshare(s, share)


@router.get("/mine", response_model=list[ProjectShareOut])
def list_my_shares(user: dict = Depends(require_user)) -> list[ProjectShareOut]:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        if u is None:
            raise HTTPException(status_code=404, detail="User not found")
        entries = shares_repo.list_by_user(s, u)
        return [_to_out(e) for e in entries]


@router.get("/{share_id}/image")
def get_share_image_user(
    share_id: str, user: dict = Depends(require_user)
) -> Response:
    """Preview della share dal punto di vista utente (solo se propria)."""
    user_id = uuid.UUID(user["id"])
    try:
        sid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        u = users_repo.get_by_id(s, user_id)
        share = shares_repo.get_by_user_and_id(s, u, sid) if u else None
        if share is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        key = share.storage_key
    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Immagine non trovata")
    return Response(
        content=download_bytes(key), media_type="image/png",
    )


# ============================================================
# Endpoint admin
# ============================================================


@admin_router.get("/project-shares", response_model=list[ShareAdminOut])
def admin_list_shares(
    status_filter: str = "pending", admin: dict = Depends(require_admin)
) -> list[ShareAdminOut]:
    with session_scope() as s:
        if status_filter in ("pending", "published", "rejected"):
            entries = shares_repo.list_by_status(s, status_filter)
        else:
            entries = shares_repo.list_all_not_deleted(s)
        out = []
        for e in entries:
            owner = users_repo.get_by_id(s, e.user_id)
            out.append(_to_admin_out(e, owner))
        return out


@admin_router.get("/project-shares/{share_id}/image")
def admin_get_share_image(
    share_id: str, admin: dict = Depends(require_admin)
) -> Response:
    try:
        sid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        share = shares_repo.get_by_id(s, sid)
        if share is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        key = share.storage_key
    if not key or not object_exists(key):
        raise HTTPException(status_code=404, detail="Immagine non trovata")
    return Response(content=download_bytes(key), media_type="image/png")


@admin_router.post(
    "/project-shares/{share_id}/approve", response_model=ShareAdminOut
)
def admin_approve(
    share_id: str, admin: dict = Depends(require_admin)
) -> ShareAdminOut:
    try:
        sid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        share = shares_repo.get_by_id(s, sid)
        if share is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        shares_repo.approve(s, share)
        owner = users_repo.get_by_id(s, share.user_id)
        return _to_admin_out(share, owner)


@admin_router.post(
    "/project-shares/{share_id}/reject", response_model=ShareAdminOut
)
def admin_reject(
    share_id: str,
    payload: RejectIn,
    admin: dict = Depends(require_admin),
) -> ShareAdminOut:
    try:
        sid = uuid.UUID(share_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID non valido")
    with session_scope() as s:
        share = shares_repo.get_by_id(s, sid)
        if share is None:
            raise HTTPException(status_code=404, detail="Non trovato")
        shares_repo.reject(s, share, reason=payload.reason)
        owner = users_repo.get_by_id(s, share.user_id)
        return _to_admin_out(share, owner)
