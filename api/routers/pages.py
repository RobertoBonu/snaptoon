"""Endpoint impaginazione: grid per pagina, render pagina, PDF export."""
from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from db.repos import page_layouts as page_layouts_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import vignettes as vignettes_repo
from db.session import session_scope
from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import page_render_key, vignette_key

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class PageInfoOut(BaseModel):
    page_number: int
    grid_id: str
    available_grids: list[str]
    capacity: int
    n_panels: int
    show_balloons: bool


class PagesListOut(BaseModel):
    pages: list[PageInfoOut]


class SetGridIn(BaseModel):
    grid_id: str


class SetBalloonsIn(BaseModel):
    show_balloons: bool


# ============================================================
# Endpoints
# ============================================================


@router.get("/projects/{slug}/pages", response_model=PagesListOut)
def list_pages(slug: str, user: dict = Depends(require_user)) -> PagesListOut:
    from snaptoon_core.layout import GRIDS, default_grid_for, grids_for_capacity

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.script is None:
            return PagesListOut(pages=[])
        try:
            pyd = scripts_repo.load_pydantic(project.script)
        except Exception:
            return PagesListOut(pages=[])

        existing = {pl.page_number: pl for pl in project.page_layouts}

        out: list[PageInfoOut] = []
        for p in pyd.pages:
            n_panels = len(p.panels)
            pl = existing.get(p.number)
            grid_id = pl.grid_id if pl else default_grid_for(n_panels)
            available = grids_for_capacity(n_panels) or [grid_id]
            show_b = pl.show_balloons if pl else True
            out.append(
                PageInfoOut(
                    page_number=p.number,
                    grid_id=grid_id,
                    available_grids=available,
                    capacity=GRIDS[grid_id].capacity if grid_id in GRIDS else n_panels,
                    n_panels=n_panels,
                    show_balloons=show_b,
                )
            )
        return PagesListOut(pages=out)


@router.patch(
    "/projects/{slug}/pages/{page_num}/grid",
    status_code=status.HTTP_204_NO_CONTENT,
)
def set_page_grid(
    slug: str, page_num: int, payload: SetGridIn,
    user: dict = Depends(require_user),
) -> None:
    from snaptoon_core.layout import GRIDS

    if payload.grid_id not in GRIDS:
        raise HTTPException(status_code=400, detail=f"Grid non trovata: {payload.grid_id}")

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        pl = page_layouts_repo.get_or_create(s, project, page_num)
        page_layouts_repo.set_grid(s, pl, payload.grid_id)


@router.patch(
    "/projects/{slug}/pages/{page_num}/balloons",
    status_code=status.HTTP_204_NO_CONTENT,
)
def set_page_balloons(
    slug: str, page_num: int, payload: SetBalloonsIn,
    user: dict = Depends(require_user),
) -> None:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        pl = page_layouts_repo.get_or_create(s, project, page_num)
        page_layouts_repo.set_show_balloons(s, pl, payload.show_balloons)


@router.get("/projects/{slug}/pages/{page_num}/render")
def render_page_endpoint(
    slug: str, page_num: int, user: dict = Depends(require_user)
) -> Response:
    """Renderizza la pagina come PNG (con bg, vignette, balloon overlay).

    Riusa snaptoon_core.layout.render_page. Cacha su Object Storage.
    """
    from snaptoon_core.layout import GRIDS, render_page

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.script is None:
            raise HTTPException(status_code=400, detail="Sceneggiatura mancante")
        try:
            pyd = scripts_repo.load_pydantic(project.script)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Script non valido: {e}")

        page = next((p for p in pyd.pages if p.number == page_num), None)
        if page is None:
            raise HTTPException(status_code=404, detail="Pagina non trovata")

        pl = next(
            (x for x in project.page_layouts if x.page_number == page_num),
            None,
        )
        grid_id = pl.grid_id if pl else "2x2"
        show_balloons = pl.show_balloons if pl else True
        grid = GRIDS.get(grid_id)
        if grid is None:
            raise HTTPException(status_code=400, detail=f"Grid invalida: {grid_id}")

        pid = project.id

    # Scarica le vignette su tempfile per render_page
    temp_files: list[Path] = []
    panel_paths: list[tuple] = []
    try:
        for panel in page.panels:
            vk = vignette_key(pid, page_num, panel.number)
            if object_exists(vk):
                data = download_bytes(vk)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(data)
                tmp.close()
                p = Path(tmp.name)
                temp_files.append(p)
                panel_paths.append((panel, p))
            else:
                panel_paths.append((panel, None))

        out_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        out_tmp.close()
        out_path = Path(out_tmp.name)
        temp_files.append(out_path)

        render_page(
            panels_with_images=panel_paths,
            grid=grid,
            out_path=out_path,
            show_balloons=show_balloons,
        )

        # Cache su storage
        with open(out_path, "rb") as f:
            data = f.read()
        upload_bytes(
            page_render_key(pid, page_num), data, content_type="image/png"
        )

        return Response(content=data, media_type="image/png")
    finally:
        for tp in temp_files:
            try:
                tp.unlink()
            except OSError:
                pass


@router.get("/projects/{slug}/pdf")
def export_pdf_endpoint(
    slug: str, user: dict = Depends(require_user)
) -> Response:
    """Renderizza il PDF: cover + tavole interne + quarta di copertina.

    Struttura come per KIDS:
      Pagina 1:    cover AI (se generata, altrimenti si parte dalle tavole)
      Pagine 2..N-1: tavole con grid
      Pagina N:    quarta di copertina (PIL, con titolo/autore/logo/copyright)

    Logo compositato con parametri "pro" (indipendenti da KIDS).
    """
    from snaptoon_core.kids_back_cover import render_back_cover
    from snaptoon_core.layout import GRIDS, export_pdf, render_page
    from snaptoon_core.logo_composite import composite_logo, parse_logo_params
    from storage.keys import (
        ADMIN_BACK_COVER_TEMPLATE_KEY,
        admin_logo_key,
        admin_logo_params_key,
        cover_illustration_key,
    )

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.script is None:
            raise HTTPException(status_code=400, detail="Sceneggiatura mancante")
        try:
            pyd = scripts_repo.load_pydantic(project.script)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Script non valido: {e}")
        layouts = {pl.page_number: pl for pl in project.page_layouts}
        pid = project.id
        pname = project.name
        slug_name = project.slug

        cover_orm = project.cover
        bc_title = (cover_orm.title if cover_orm else "") or pname
        bc_subtitle = cover_orm.subtitle if cover_orm else ""
        bc_author = cover_orm.author if cover_orm else ""
        bc_copyright = project.copyright_text or ""

    # Logo di sistema Pro (indipendente da KIDS) + parametri
    logo_key = admin_logo_key("pro")
    logo_params_key = admin_logo_params_key("pro")
    logo_bytes = None
    if object_exists(logo_key):
        try:
            logo_bytes = download_bytes(logo_key)
        except Exception:
            pass
    logo_params_raw = None
    if object_exists(logo_params_key):
        try:
            logo_params_raw = download_bytes(logo_params_key)
        except Exception:
            pass
    logo_params = parse_logo_params(logo_params_raw)
    logo_active = bool(logo_bytes) and logo_params.get("logo_show", False)

    # Testo editoriale per quarta (condiviso col flusso KIDS)
    bc_template = ""
    if object_exists(ADMIN_BACK_COVER_TEMPLATE_KEY):
        try:
            bc_template = download_bytes(ADMIN_BACK_COVER_TEMPLATE_KEY).decode(
                "utf-8"
            )
        except Exception:
            pass

    temp_files: list[Path] = []
    page_temp_paths: list[Path] = []
    try:
        # === Pagina 1: cover AI (con logo compositato se attivo) ===
        cover_key = cover_illustration_key(pid)
        if object_exists(cover_key):
            cover_bytes = download_bytes(cover_key)
            if logo_active:
                cover_bytes = composite_logo(
                    base_bytes=cover_bytes,
                    logo_bytes=logo_bytes,
                    size_px=logo_params["cover_size_px"],
                    x=logo_params["cover_x"],
                    y=logo_params["cover_y"],
                )
            cover_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            cover_tmp.write(cover_bytes)
            cover_tmp.close()
            cover_path = Path(cover_tmp.name)
            temp_files.append(cover_path)
            page_temp_paths.append(cover_path)

        for page in pyd.pages:
            pl = layouts.get(page.number)
            grid_id = pl.grid_id if pl else "2x2"
            show_balloons = pl.show_balloons if pl else True
            grid = GRIDS.get(grid_id)
            if grid is None:
                continue

            panel_paths: list[tuple] = []
            for panel in page.panels:
                vk = vignette_key(pid, page.number, panel.number)
                if object_exists(vk):
                    data = download_bytes(vk)
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp.write(data)
                    tmp.close()
                    p = Path(tmp.name)
                    temp_files.append(p)
                    panel_paths.append((panel, p))
                else:
                    panel_paths.append((panel, None))

            out_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            out_tmp.close()
            out_path = Path(out_tmp.name)
            temp_files.append(out_path)
            render_page(
                panels_with_images=panel_paths,
                grid=grid,
                out_path=out_path,
                show_balloons=show_balloons,
            )
            page_temp_paths.append(out_path)

        # === ULTIMA PAGINA: la quarta di copertina (con logo compositato) ===
        back_cover_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        back_cover_tmp.close()
        back_cover_path = Path(back_cover_tmp.name)
        temp_files.append(back_cover_path)

        # Cover pulita per la miniatura nella quarta
        cover_bytes_for_back = None
        if object_exists(cover_key):
            try:
                cover_bytes_for_back = download_bytes(cover_key)
            except Exception:
                pass

        try:
            render_back_cover(
                title=bc_title,
                author=bc_author,
                subtitle=bc_subtitle,
                copyright_text=bc_copyright,
                back_cover_template=bc_template,
                cover_bytes=cover_bytes_for_back,
                out_path=back_cover_path,
            )
            if logo_active:
                bc_bytes = back_cover_path.read_bytes()
                bc_bytes = composite_logo(
                    base_bytes=bc_bytes,
                    logo_bytes=logo_bytes,
                    size_px=logo_params["back_size_px"],
                    x=logo_params["back_x"],
                    y=logo_params["back_y"],
                )
                back_cover_path.write_bytes(bc_bytes)
            page_temp_paths.append(back_cover_path)
        except Exception as e:
            logger.warning("Back cover Pro fallita, skip: %s", str(e))

        pdf_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf_tmp.close()
        pdf_path = Path(pdf_tmp.name)
        temp_files.append(pdf_path)
        export_pdf(page_temp_paths, pdf_path)

        pdf_bytes = pdf_path.read_bytes()
    finally:
        for tp in temp_files:
            try:
                tp.unlink()
            except OSError:
                pass

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="snaptoon_{slug_name}.pdf"',
        },
    )
