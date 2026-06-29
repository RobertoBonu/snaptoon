"""Endpoint sceneggiatura: source_text + adapt (Claude)."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from billing.plans import cost_for_operation
from db.models import CreditOperation, LengthTarget
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import users as users_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope

router = APIRouter()


# ============================================================
# Schemas
# ============================================================


class ScriptDialogueOut(BaseModel):
    kind: str
    speaker: Optional[str] = None
    text: str


class ScriptPanelOut(BaseModel):
    number: int
    description: str
    dialogues: list[ScriptDialogueOut] = []
    shot_distance: Optional[str] = None
    shot_angle: Optional[str] = None
    mood: Optional[str] = None


class ScriptPageOut(BaseModel):
    number: int
    panels: list[ScriptPanelOut]


class ScriptOut(BaseModel):
    logline: str
    characters: list[dict]  # {name, visual_bible, voice}
    pages: list[ScriptPageOut]


class ProjectScriptOut(BaseModel):
    source_text: str
    has_script: bool
    script: Optional[ScriptOut] = None


class SourceTextIn(BaseModel):
    source_text: str = Field(..., max_length=20000)


# ============================================================
# Helpers
# ============================================================


def _project_or_404(slug: str, user_id: uuid.UUID):
    """Versione per slug — usata dagli endpoint del flusso Pro."""
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        return project.id


def _pyd_to_out(pyd) -> ScriptOut:
    return ScriptOut(
        logline=pyd.logline,
        characters=[
            {"name": c.name, "visual_bible": c.visual_bible, "voice": c.voice}
            for c in pyd.characters
        ],
        pages=[
            ScriptPageOut(
                number=p.number,
                panels=[
                    ScriptPanelOut(
                        number=pn.number,
                        description=pn.description,
                        dialogues=[
                            ScriptDialogueOut(
                                kind=d.kind,
                                speaker=d.speaker,
                                text=d.text,
                            )
                            for d in pn.dialogues
                        ],
                        shot_distance=getattr(pn, "shot_distance", None),
                        shot_angle=getattr(pn, "shot_angle", None),
                        mood=getattr(pn, "mood", None),
                    )
                    for pn in p.panels
                ],
            )
            for p in pyd.pages
        ],
    )


# ============================================================
# Endpoints
# ============================================================


@router.get("/projects/{slug}/script", response_model=ProjectScriptOut)
def get_script(slug: str, user: dict = Depends(require_user)) -> ProjectScriptOut:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        source = project.source_text or ""
        if project.script is None:
            return ProjectScriptOut(source_text=source, has_script=False)
        try:
            pyd = scripts_repo.load_pydantic(project.script)
            if not pyd.pages:
                return ProjectScriptOut(source_text=source, has_script=False)
            return ProjectScriptOut(
                source_text=source,
                has_script=True,
                script=_pyd_to_out(pyd),
            )
        except Exception:
            return ProjectScriptOut(source_text=source, has_script=False)


@router.patch("/projects/{slug}/source-text", status_code=status.HTTP_204_NO_CONTENT)
def update_source_text(
    slug: str, payload: SourceTextIn, user: dict = Depends(require_user)
) -> None:
    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        projects_repo.set_source_text(s, project, payload.source_text)


@router.post("/projects/{slug}/adapt-script", response_model=ScriptOut)
def adapt_script(slug: str, user: dict = Depends(require_user)) -> ScriptOut:
    """Trasforma source_text in sceneggiatura strutturata via Claude.

    Costa adapt_script crediti (5).
    """
    user_id = uuid.UUID(user["id"])

    # Carica dati
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if not (project.source_text or "").strip():
            raise HTTPException(
                status_code=400,
                detail="Inserisci prima il testo sorgente.",
            )
        title = project.name
        length_target = project.length_target
        source = project.source_text
        pid = project.id

    # Charge
    cost = cost_for_operation("adapt_script")
    try:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.charge(
                s, u, cost=cost,
                operation=CreditOperation.adapt_script,
                reason=f"Adatta sceneggiatura «{title}»",
                reference_id=str(pid),
            )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=402,
            detail=f"Crediti insufficienti: servono {e.required}, ne hai {e.available}",
        )

    # Chiama Claude
    try:
        from snaptoon_core.script import adapt_text_to_script

        pyd_script = adapt_text_to_script(
            title=title,
            length_target=length_target,
            source_text=source,
        )
    except Exception as e:
        with session_scope() as s:
            u = users_repo.get_by_id(s, user_id)
            credits_repo.refund(
                s, u, amount=cost,
                reason=f"Refund adapt_script: {str(e)[:200]}",
            )
        raise HTTPException(status_code=502, detail=f"Errore Claude: {str(e)[:300]}")

    # Salva
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        orm_script = scripts_repo.get_or_create(s, project)
        scripts_repo.save_pydantic(s, orm_script, pyd_script)

    return _pyd_to_out(pyd_script)
