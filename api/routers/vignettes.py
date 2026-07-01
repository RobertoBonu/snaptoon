"""Endpoint vignette flusso Pro: scene params, generazione, serving."""
from __future__ import annotations

import hashlib
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from billing.plans import cost_for_operation
from db.models import CreditOperation
from db.repos import credits as credits_repo
from db.repos import page_layouts as page_layouts_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import users as users_repo
from db.repos import vignettes as vignettes_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import reference_key, vignette_key

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class SceneOption(BaseModel):
    key: str
    label: str


class SceneOptionsOut(BaseModel):
    shot_distances: list[SceneOption]
    shot_angles: list[SceneOption]
    moods: list[SceneOption]
    aspect_ratios: list[SceneOption]


class VignetteStatusOut(BaseModel):
    page_number: int
    panel_number: int
    description: str
    dialogue_text: Optional[str] = None
    dialogue_speaker: Optional[str] = None
    generated: bool
    shot_distance: Optional[str] = None
    shot_angle: Optional[str] = None
    mood: Optional[str] = None
    aspect_ratio_key: Optional[str] = None


class VignettesListOut(BaseModel):
    vignettes: list[VignetteStatusOut]


class GeneratePanelIn(BaseModel):
    shot_distance: Optional[str] = None
    shot_angle: Optional[str] = None
    mood: Optional[str] = None
    aspect_ratio: Optional[str] = Field(default="2_3")
    quality: str = Field(default="medium")
    # Nomi dei personaggi che DEVONO apparire in questa vignetta. Se None →
    # tutto il cast (comportamento V2 originale). Se lista vuota → nessun
    # personaggio (utile per scene ambientali).
    character_names: Optional[list[str]] = None


# ============================================================
# Helpers
# ============================================================


def _hash_prompt(prompt: str, *extra: str) -> str:
    h = hashlib.sha256(prompt.encode("utf-8"))
    for e in extra:
        h.update(b"|")
        h.update(e.encode("utf-8"))
    return h.hexdigest()


def _size_from_aspect(aspect_key: Optional[str]) -> tuple[str, str]:
    """Aspect key → (openai_size, fmt_label)."""
    if aspect_key in ("2_3", "3_4", "9_16"):
        return ("1024x1536", "vertical portrait, tall format")
    if aspect_key in ("3_2", "4_3", "16_9", "2_1"):
        return ("1536x1024", "horizontal panoramic, wide format")
    return ("1024x1024", "square format")


# ============================================================
# Endpoints — Scene options
# ============================================================


@router.get("/scene-options", response_model=SceneOptionsOut)
def scene_options(user: dict = Depends(require_user)) -> SceneOptionsOut:
    from snaptoon_core.scene import ASPECT_RATIOS, MOODS, SHOT_ANGLES, SHOT_DISTANCES

    return SceneOptionsOut(
        shot_distances=[SceneOption(key=o.key, label=o.label) for o in SHOT_DISTANCES],
        shot_angles=[SceneOption(key=o.key, label=o.label) for o in SHOT_ANGLES],
        moods=[SceneOption(key=o.key, label=o.label) for o in MOODS],
        aspect_ratios=[SceneOption(key=o.key, label=o.label) for o in ASPECT_RATIOS],
    )


# ============================================================
# Endpoints — Lista vignette + Generazione
# ============================================================


@router.get("/projects/{slug}/vignettes", response_model=VignettesListOut)
def list_project_vignettes(
    slug: str, user: dict = Depends(require_user)
) -> VignettesListOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.script is None:
            return VignettesListOut(vignettes=[])
        try:
            pyd = scripts_repo.load_pydantic(project.script)
        except Exception:
            return VignettesListOut(vignettes=[])

        generated_set = {
            (v.page_number, v.panel_number): v
            for v in vignettes_repo.list_for_project(s, project)
        }

        out: list[VignetteStatusOut] = []
        for p in pyd.pages:
            for pn in p.panels:
                v = generated_set.get((p.number, pn.number))
                dialogue_text = pn.dialogues[0].text if pn.dialogues else None
                dialogue_speaker = pn.dialogues[0].speaker if pn.dialogues else None
                out.append(
                    VignetteStatusOut(
                        page_number=p.number,
                        panel_number=pn.number,
                        description=pn.description,
                        dialogue_text=dialogue_text,
                        dialogue_speaker=dialogue_speaker,
                        generated=v is not None,
                        shot_distance=getattr(pn, "shot_distance", None),
                        shot_angle=getattr(pn, "shot_angle", None),
                        mood=getattr(pn, "mood", None),
                        aspect_ratio_key=v.aspect_ratio_key if v else None,
                    )
                )
        return VignettesListOut(vignettes=out)


@router.post("/projects/{slug}/vignettes/{page_num}/{panel_num}/generate")
def generate_vignette(
    slug: str,
    page_num: int,
    panel_num: int,
    payload: GeneratePanelIn,
    user: dict = Depends(require_user),
) -> dict:
    """Genera una singola vignetta con scene params + balloon AI-bake."""
    user_id = uuid.UUID(user["id"])

    # 1. Carica context
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.script is None:
            raise HTTPException(status_code=400, detail="Sceneggiatura mancante")
        if not project.style_id:
            raise HTTPException(status_code=400, detail="Scegli prima uno stile")

        pyd = scripts_repo.load_pydantic(project.script)
        target_panel = None
        for p in pyd.pages:
            if p.number == page_num:
                for pn in p.panels:
                    if pn.number == panel_num:
                        target_panel = pn
                        break
                break
        if target_panel is None:
            raise HTTPException(status_code=404, detail="Vignetta non trovata")

        style_preset_id = project.style_id
        pid = project.id

        # Full cast del progetto
        full_cast = [
            {"name": cs.name, "description": cs.visual_description, "id": str(cs.id)}
            for cs in project.character_sheets
        ]

    # Filtra il cast se l'utente ha selezionato personaggi specifici
    if payload.character_names is None:
        cast = full_cast
    else:
        wanted_lower = {n.lower() for n in payload.character_names if n.strip()}
        cast = [c for c in full_cast if c["name"].lower() in wanted_lower]

    # 2. Charge
    cost = cost_for_operation("generate_panel", quality=payload.quality)
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.generate_panel,
                reason=f"Panel p{page_num}v{panel_num}",
                reference_id=str(pid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # 3. Build prompt + generate
    try:
        from snaptoon_core.generator import OpenAIImageGenerator
        from snaptoon_core.kids_pipeline import build_panel_prompt

        size_str, fmt_label = _size_from_aspect(payload.aspect_ratio)
        scene_params = {
            "shot_distance": payload.shot_distance,
            "shot_angle": payload.shot_angle,
            "mood": payload.mood,
        }
        prompt = build_panel_prompt(
            target_panel, cast, style_preset_id, scene_params, panel_format=fmt_label,
        )

        # Reference temp files dei personaggi citati
        tmp_refs: list[Path] = []
        for c in cast:
            rk = reference_key(pid, uuid.UUID(c["id"]), 1)
            if object_exists(rk):
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(download_bytes(rk))
                tmp.close()
                tmp_refs.append(Path(tmp.name))

        generator = OpenAIImageGenerator()
        img_bytes = generator._generate_bytes(
            prompt=prompt,
            size=size_str,
            reference_images=tmp_refs if tmp_refs else None,
            quality=payload.quality,
        )

        # Cleanup
        for tp in tmp_refs:
            try:
                tp.unlink()
            except OSError:
                pass

    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund panel p{page_num}v{panel_num}: {str(e)[:200]}",
            )
        raise HTTPException(status_code=502, detail=f"Errore generazione: {str(e)[:300]}")

    # 4. Upload + save
    vk = vignette_key(pid, page_num, panel_num)
    upload_bytes(vk, img_bytes, content_type="image/png")
    aspect_key = payload.aspect_ratio or "1_1"
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        vignettes_repo.upsert(
            s, project=project,
            page_number=page_num, panel_number=panel_num,
            storage_key=vk,
            prompt_hash=_hash_prompt(prompt),
            quality=payload.quality,
            aspect_ratio_key=aspect_key,
            provider="openai",
            model="gpt-image-2",
        )

    return {"ok": True}


@router.get("/projects/{slug}/vignettes/{page_num}/{panel_num}/image")
def get_vignette_image(
    slug: str, page_num: int, panel_num: int,
    user: dict = Depends(require_user),
) -> Response:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        pid = project.id
    vk = vignette_key(pid, page_num, panel_num)
    if not object_exists(vk):
        raise HTTPException(status_code=404, detail="Vignetta non generata")
    return Response(content=download_bytes(vk), media_type="image/png")
