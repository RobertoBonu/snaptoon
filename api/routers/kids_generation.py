"""Endpoint generazione KIDS: storia + immagini + serving binari + PDF.

Pipeline:
  1. POST /api/kids/projects/{id}/story → genera storia con Claude (5 cr)
     Body: { "feedback": "" } per rigenerare con un suggerimento
  2. GET  /api/kids/projects/{id}/details → ritorna script + status vignette
  3. GET  /api/kids/projects/{id}/generate-stream → SSE: cover + vignette
     una per una, eventi push al browser per UI live
  4. GET  /api/kids/projects/{id}/images/cover → byte cover (image/png)
  5. GET  /api/kids/projects/{id}/images/panel/{page}/{panel} → byte vignetta
  6. POST /api/kids/projects/{id}/regenerate-cover → rigenera (1 cr)
  7. POST /api/kids/projects/{id}/regenerate-panel/{page}/{panel} → rigenera (1 cr)
  8. GET  /api/kids/projects/{id}/pdf → PDF download
"""
from __future__ import annotations

import json
import logging
import tempfile
import time
import uuid
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from api.routers.auth import require_user
from api.routers.kids import KIDS_STYLE_MAP, KIDS_STYLE_PRESET_IDS
from billing.plans import cost_for_operation
from db.models import CreditOperation
from db.repos import characters as characters_repo
from db.repos import covers as covers_repo
from db.repos import credits as credits_repo
from db.repos import page_layouts as page_layouts_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import users as users_repo
from db.repos import vignettes as vignettes_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from snaptoon_core.kids_pipeline import (
    build_cover_prompt,
    build_panel_prompt,
    build_reference_prompt,
    generate_kids_script,
    panel_size_for,
)
from snaptoon_core.models import Script as PydScript
from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import (
    cover_illustration_key,
    reference_key,
    vignette_key,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class GenerateStoryIn(BaseModel):
    feedback: str = Field(default="", max_length=2000)


class PanelOut(BaseModel):
    number: int
    description: str
    dialogue_speaker: Optional[str] = None
    dialogue_text: Optional[str] = None


class PageOut(BaseModel):
    number: int
    panels: list[PanelOut]


class StoryOut(BaseModel):
    logline: str
    pages: list[PageOut]


class VignetteStatusOut(BaseModel):
    page_number: int
    panel_number: int
    generated: bool
    aspect_ratio_key: Optional[str] = None


class KidsProjectDetailsOut(BaseModel):
    id: str
    slug: str
    name: str
    style_id: Optional[str] = None
    style_slug: Optional[str] = None
    has_story: bool
    story: Optional[StoryOut] = None
    has_cover: bool
    vignettes: list[VignetteStatusOut]


# ============================================================
# Helpers
# ============================================================


def _project_or_404(project_id: str, user_id: uuid.UUID):
    """Ritorna (project_uuid, project, user) o solleva 404. NB: gli oggetti
    SQLAlchemy sono detached subito dopo session_scope().__exit__, quindi
    questo helper va chiamato in un context-manager esterno."""
    try:
        pid = uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID progetto invalido")
    return pid


def _style_slug_from_preset(preset_id: Optional[str]) -> Optional[str]:
    for slug, (_, pid) in KIDS_STYLE_MAP.items():
        if pid == preset_id:
            return slug
    return None


# ============================================================
# Step 1: Storia (Claude)
# ============================================================


@router.post("/projects/{project_id}/story", response_model=StoryOut)
def generate_story(
    project_id: str,
    payload: GenerateStoryIn,
    user: dict = Depends(require_user),
) -> StoryOut:
    """Genera (o rigenera con feedback) la storia con Claude.

    Costa adapt_script crediti (5). Salva lo script su DB.
    """
    user_id = uuid.UUID(user["id"])
    pid = _project_or_404(project_id, user_id)

    # 1. Carica context dal DB
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.style_id not in KIDS_STYLE_PRESET_IDS:
            raise HTTPException(status_code=400, detail="Progetto non Kids")

        # Recupera template dalla grid_distribution salvata o ricalcola
        # Usiamo page_layouts già salvati se ci sono, altrimenti default 2x2
        page_layouts = sorted(project.page_layouts, key=lambda p: p.page_number)
        if page_layouts:
            grid_distribution = [pl.grid_id for pl in page_layouts]
        else:
            # Fallback breve standard se manca
            grid_distribution = ["splash", "1+2", "2x2", "1+2", "splash"]

        scintilla = project.source_text or ""
        if not scintilla:
            raise HTTPException(status_code=400, detail="Scintilla mancante")

        # Cast
        cast_chars = list(project.character_sheets)
        if not cast_chars:
            raise HTTPException(status_code=400, detail="Cast mancante")
        names = [c.name for c in cast_chars]
        descs = [c.visual_description for c in cast_chars]

    # 2. Charge crediti
    cost = cost_for_operation("adapt_script")
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u,
                cost=cost,
                operation=CreditOperation.adapt_script,
                reason="KIDS story generation",
                reference_id=str(pid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # 3. Chiama Claude
    try:
        pyd_script = generate_kids_script(
            scintilla, names, descs, grid_distribution, feedback=payload.feedback
        )
    except Exception as e:
        # Refund
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund kids story: {str(e)[:200]}",
            )
        raise HTTPException(status_code=502, detail=f"Errore Claude: {str(e)[:300]}")

    # 4. Salva script su DB + page_layouts (se nuovi)
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        orm_script = scripts_repo.get_or_create(s, project)
        scripts_repo.save_pydantic(s, orm_script, pyd_script)

        # Save grid_distribution come page_layouts (idempotente)
        for page_idx, grid_id in enumerate(grid_distribution, start=1):
            pl = page_layouts_repo.get_or_create(s, project, page_idx)
            page_layouts_repo.set_grid(s, pl, grid_id)

    # 5. Return story per UI
    return StoryOut(
        logline=pyd_script.logline,
        pages=[
            PageOut(
                number=p.number,
                panels=[
                    PanelOut(
                        number=pn.number,
                        description=pn.description,
                        dialogue_speaker=(
                            pn.dialogues[0].speaker if pn.dialogues else None
                        ),
                        dialogue_text=(
                            pn.dialogues[0].text if pn.dialogues else None
                        ),
                    )
                    for pn in p.panels
                ],
            )
            for p in pyd_script.pages
        ],
    )


# ============================================================
# Step 2: Details (storia + status vignette)
# ============================================================


@router.get("/projects/{project_id}/details", response_model=KidsProjectDetailsOut)
def get_project_details(
    project_id: str, user: dict = Depends(require_user)
) -> KidsProjectDetailsOut:
    user_id = uuid.UUID(user["id"])
    pid = _project_or_404(project_id, user_id)

    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")

        # Story (se c'è)
        story = None
        has_story = False
        if project.script is not None:
            try:
                pyd = scripts_repo.load_pydantic(project.script)
                if pyd.pages:
                    has_story = True
                    story = StoryOut(
                        logline=pyd.logline,
                        pages=[
                            PageOut(
                                number=p.number,
                                panels=[
                                    PanelOut(
                                        number=pn.number,
                                        description=pn.description,
                                        dialogue_speaker=(
                                            pn.dialogues[0].speaker
                                            if pn.dialogues
                                            else None
                                        ),
                                        dialogue_text=(
                                            pn.dialogues[0].text
                                            if pn.dialogues
                                            else None
                                        ),
                                    )
                                    for pn in p.panels
                                ],
                            )
                            for p in pyd.pages
                        ],
                    )
            except Exception:
                pass

        # Cover
        cover_key_ = cover_illustration_key(pid)
        has_cover = object_exists(cover_key_)

        # Vignettes
        vigs = vignettes_repo.list_for_project(s, project)
        vig_status = [
            VignetteStatusOut(
                page_number=v.page_number,
                panel_number=v.panel_number,
                generated=True,
                aspect_ratio_key=v.aspect_ratio_key,
            )
            for v in vigs
        ]

        return KidsProjectDetailsOut(
            id=str(project.id),
            slug=project.slug,
            name=project.name,
            style_id=project.style_id,
            style_slug=_style_slug_from_preset(project.style_id),
            has_story=has_story,
            story=story,
            has_cover=has_cover,
            vignettes=vig_status,
        )


# ============================================================
# Step 3: Serving immagini (cover + vignette)
# ============================================================


@router.get("/projects/{project_id}/images/cover")
def get_cover_image(
    project_id: str, user: dict = Depends(require_user)
) -> Response:
    user_id = uuid.UUID(user["id"])
    pid = _project_or_404(project_id, user_id)
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
    cover_key_ = cover_illustration_key(pid)
    if not object_exists(cover_key_):
        raise HTTPException(status_code=404, detail="Cover not yet generated")
    data = download_bytes(cover_key_)
    return Response(content=data, media_type="image/png")


@router.get("/projects/{project_id}/images/panel/{page_num}/{panel_num}")
def get_panel_image(
    project_id: str,
    page_num: int,
    panel_num: int,
    user: dict = Depends(require_user),
) -> Response:
    user_id = uuid.UUID(user["id"])
    pid = _project_or_404(project_id, user_id)
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
    vk = vignette_key(pid, page_num, panel_num)
    if not object_exists(vk):
        raise HTTPException(status_code=404, detail="Vignetta non trovata")
    data = download_bytes(vk)
    return Response(content=data, media_type="image/png")


# ============================================================
# Step 4: Generate-stream (SSE pipeline live)
# ============================================================


@router.get("/projects/{project_id}/generate-stream")
def generate_stream(
    project_id: str, user: dict = Depends(require_user)
) -> EventSourceResponse:
    """SSE pipeline: genera reference + cover + vignette UNA ALLA VOLTA.

    Eventi emessi:
      data: {"type":"start", "total_steps":N}
      data: {"type":"step", "kind":"reference|cover|panel", "label":"...", "current":i, "total":N}
      data: {"type":"image_ready", "kind":"cover|panel", "key":"page-panel"}
      data: {"type":"error", "message":"..."}
      data: {"type":"done"}
    """
    user_id = uuid.UUID(user["id"])
    pid = _project_or_404(project_id, user_id)

    # Carica subito i dati necessari (no lazy nei generatori per evitare problemi
    # con session scope async)
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        if project is None or project.owner_user_id != user_id:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.script is None:
            raise HTTPException(status_code=400, detail="Storia non ancora generata")
        if project.style_id not in KIDS_STYLE_PRESET_IDS:
            raise HTTPException(status_code=400, detail="Stile non Kids")

        style_preset_id = project.style_id
        project_name = project.name

        try:
            pyd_script = scripts_repo.load_pydantic(project.script)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Script non valido: {e}")

        page_layouts = {pl.page_number: pl.grid_id for pl in project.page_layouts}

        # Cast
        cast_chars = list(project.character_sheets)
        cast = [
            {"id": str(c.id), "name": c.name, "description": c.visual_description}
            for c in cast_chars
        ]

        # Vignette già esistenti (skip)
        existing_vigs = {
            (v.page_number, v.panel_number)
            for v in vignettes_repo.list_for_project(s, project)
        }
        cover_already = object_exists(cover_illustration_key(pid))

        # Scene distribution: per ora MVP usiamo defaults se non c'è
        # (le scene specifiche le mette pages/06_KIDS.py via template)

    flat_panels = [(p.number, pn) for p in pyd_script.pages for pn in p.panels]

    # Conta steps totali
    n_refs = sum(1 for c in cast if not _ref_exists(pid, c["id"]))
    n_cover = 0 if cover_already else 1
    n_panels = sum(
        1 for p, pn in flat_panels if (p, pn.number) not in existing_vigs
    )
    total_steps = n_refs + n_cover + n_panels

    def event(payload: dict) -> dict:
        return {"data": json.dumps(payload)}

    async def event_generator() -> AsyncIterator[dict]:
        from snaptoon_core.generator import OpenAIImageGenerator

        generator = OpenAIImageGenerator()
        step = 0

        yield event({"type": "start", "total_steps": total_steps})

        # === 1. Reference per ogni personaggio ===
        char_storage_keys = {}
        for c in cast:
            ref_storage = reference_key(pid, uuid.UUID(c["id"]), 1)
            if object_exists(ref_storage):
                char_storage_keys[c["name"]] = ref_storage
                continue
            step += 1
            yield event({
                "type": "step", "kind": "reference",
                "label": f"Disegno {c['name']}...",
                "current": step, "total": total_steps,
            })
            try:
                cost = cost_for_operation("generate_reference")
                with session_scope() as s:
                    u = users_repo.get_by_id(s, user_id)
                    credits_repo.charge(
                        s, u, cost=cost,
                        operation=CreditOperation.generate_reference,
                        reason=f"KIDS reference {c['name']}",
                        reference_id=str(pid),
                    )
                prompt = build_reference_prompt(c["name"], c["description"], style_preset_id)
                img_bytes = generator._generate_bytes(
                    prompt=prompt,
                    size="1024x1024",
                    reference_images=None,
                    quality="medium",
                )
                upload_bytes(ref_storage, img_bytes, content_type="image/png")
                # Salva su DB
                with session_scope() as s:
                    project = projects_repo.get_by_id(s, pid)
                    cs = next((x for x in project.character_sheets if x.name == c["name"]), None)
                    if cs is not None:
                        characters_repo.upsert_reference(
                            s, cs, slot_number=1, storage_key=ref_storage,
                            mime_type="image/png", file_size=len(img_bytes),
                        )
                char_storage_keys[c["name"]] = ref_storage
                yield event({
                    "type": "image_ready", "kind": "reference",
                    "name": c["name"],
                })
            except Exception as e:
                logger.exception("ref gen failed")
                with session_scope() as s:
                    u = users_repo.get_by_id(s, user_id)
                    credits_repo.refund(
                        s, u, amount=cost,
                        reason=f"Refund kids ref {c['name']}: {str(e)[:200]}",
                    )
                yield event({"type": "error", "message": f"Reference {c['name']}: {str(e)[:200]}"})

        # === 2. Cover ===
        if not cover_already:
            step += 1
            yield event({
                "type": "step", "kind": "cover",
                "label": "Disegno la copertina...",
                "current": step, "total": total_steps,
            })
            try:
                cost = cost_for_operation("generate_panel", quality="medium")
                with session_scope() as s:
                    u = users_repo.get_by_id(s, user_id)
                    credits_repo.charge(
                        s, u, cost=cost,
                        operation=CreditOperation.generate_cover,
                        reason="KIDS cover",
                        reference_id=str(pid),
                    )
                # Reference temp
                tmp_refs = []
                for c in cast:
                    rk = char_storage_keys.get(c["name"])
                    if rk and object_exists(rk):
                        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        tmp.write(download_bytes(rk))
                        tmp.close()
                        tmp_refs.append(Path(tmp.name))
                cover_title = pyd_script.logline or project_name
                prompt = build_cover_prompt(cover_title, cast, style_preset_id)
                img_bytes = generator._generate_bytes(
                    prompt=prompt,
                    size="1024x1536",
                    reference_images=tmp_refs if tmp_refs else None,
                    quality="medium",
                )
                ck = cover_illustration_key(pid)
                upload_bytes(ck, img_bytes, content_type="image/png")
                with session_scope() as s:
                    project = projects_repo.get_by_id(s, pid)
                    cover_orm = covers_repo.get_or_create(s, project)
                    covers_repo.update_text(
                        s, cover_orm, title=cover_title, author="",
                        description=project.source_text or "",
                    )
                    covers_repo.update_illustration_key(s, cover_orm, ck)
                for tp in tmp_refs:
                    try:
                        tp.unlink()
                    except OSError:
                        pass
                yield event({"type": "image_ready", "kind": "cover"})
            except Exception as e:
                logger.exception("cover gen failed")
                with session_scope() as s:
                    u = users_repo.get_by_id(s, user_id)
                    credits_repo.refund(
                        s, u, amount=cost,
                        reason=f"Refund kids cover: {str(e)[:200]}",
                    )
                yield event({"type": "error", "message": f"Cover: {str(e)[:200]}"})

        # === 3. Vignette ===
        for page_num, panel in flat_panels:
            if (page_num, panel.number) in existing_vigs:
                continue
            step += 1
            yield event({
                "type": "step", "kind": "panel",
                "label": f"Pagina {page_num} · vignetta {panel.number}",
                "current": step, "total": total_steps,
            })
            try:
                cost = cost_for_operation("generate_panel", quality="medium")
                with session_scope() as s:
                    u = users_repo.get_by_id(s, user_id)
                    credits_repo.charge(
                        s, u, cost=cost,
                        operation=CreditOperation.generate_panel,
                        reason=f"KIDS p{page_num}v{panel.number}",
                        reference_id=str(pid),
                    )
                grid_id = page_layouts.get(page_num, "2x2")
                size_str, aspect_key, fmt_label = panel_size_for(grid_id, panel.number)
                scene_params = {}  # MVP: defaults
                prompt = build_panel_prompt(
                    panel, cast, style_preset_id, scene_params, panel_format=fmt_label,
                )
                # Reference temp
                tmp_refs = []
                for c in cast:
                    rk = char_storage_keys.get(c["name"])
                    if rk and object_exists(rk):
                        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                        tmp.write(download_bytes(rk))
                        tmp.close()
                        tmp_refs.append(Path(tmp.name))
                img_bytes = generator._generate_bytes(
                    prompt=prompt,
                    size=size_str,
                    reference_images=tmp_refs if tmp_refs else None,
                    quality="medium",
                )
                vk = vignette_key(pid, page_num, panel.number)
                upload_bytes(vk, img_bytes, content_type="image/png")
                with session_scope() as s:
                    project = projects_repo.get_by_id(s, pid)
                    vignettes_repo.upsert(
                        s, project=project,
                        page_number=page_num, panel_number=panel.number,
                        storage_key=vk,
                        prompt_hash=_hash_prompt(prompt),
                        quality="medium",
                        aspect_ratio_key=aspect_key,
                        provider="openai",
                        model="gpt-image-2",
                    )
                for tp in tmp_refs:
                    try:
                        tp.unlink()
                    except OSError:
                        pass
                yield event({
                    "type": "image_ready", "kind": "panel",
                    "page": page_num, "panel": panel.number,
                })
            except Exception as e:
                logger.exception("panel gen failed")
                with session_scope() as s:
                    u = users_repo.get_by_id(s, user_id)
                    credits_repo.refund(
                        s, u, amount=cost,
                        reason=f"Refund kids p{page_num}v{panel.number}: {str(e)[:200]}",
                    )
                yield event({
                    "type": "error",
                    "message": f"P{page_num}V{panel.number}: {str(e)[:200]}",
                })

        yield event({"type": "done"})

    return EventSourceResponse(event_generator())


def _ref_exists(project_id: uuid.UUID, char_id: str) -> bool:
    try:
        return object_exists(reference_key(project_id, uuid.UUID(char_id), 1))
    except Exception:
        return False


def _hash_prompt(prompt: str, *extra: str) -> str:
    import hashlib

    h = hashlib.sha256(prompt.encode("utf-8"))
    for e in extra:
        h.update(b"|")
        h.update(e.encode("utf-8"))
    return h.hexdigest()
