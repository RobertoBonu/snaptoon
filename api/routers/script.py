"""Endpoint sceneggiatura: source_text + adapt (Claude)."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.routers.auth import require_user
from billing.plans import cost_for_operation
from db.models import CreditOperation, LengthTarget
from db.repos import characters as characters_repo
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


# === Edit dello script (patch parziale, granulare) ===


class DialogueEditIn(BaseModel):
    kind: str = "FUMETTO"
    speaker: Optional[str] = None
    text: str


class PanelEditIn(BaseModel):
    number: int
    description: str
    dialogues: list[DialogueEditIn] = []
    shot_distance: Optional[str] = None
    shot_angle: Optional[str] = None
    mood: Optional[str] = None


class PageEditIn(BaseModel):
    number: int
    panels: list[PanelEditIn]


class CharacterEditIn(BaseModel):
    name: str
    visual_bible: str = ""
    voice: str = ""


class ScriptEditIn(BaseModel):
    logline: str
    characters: list[CharacterEditIn] = []
    pages: list[PageEditIn]


class CharacterSyncOut(BaseModel):
    created: list[str]  # nomi dei personaggi creati
    already_existing: list[str]  # nomi già presenti (skip)


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
    created_chars: list[str] = []
    with session_scope() as s:
        project = projects_repo.get_by_id(s, pid)
        orm_script = scripts_repo.get_or_create(s, project)
        scripts_repo.save_pydantic(s, orm_script, pyd_script)

        # Auto-populate CharacterSheet dai personaggi dello script se non esistono
        existing_names = {c.name.lower() for c in project.character_sheets}
        for pyd_char in pyd_script.characters:
            if pyd_char.name.lower() in existing_names:
                continue
            try:
                characters_repo.create_character(
                    s, project=project, name=pyd_char.name,
                    visual_description=pyd_char.visual_bible or "",
                )
                created_chars.append(pyd_char.name)
            except ValueError:
                pass

    return _pyd_to_out(pyd_script)


@router.patch(
    "/projects/{slug}/script", response_model=ScriptOut,
    status_code=status.HTTP_200_OK,
)
def update_script(
    slug: str, payload: ScriptEditIn, user: dict = Depends(require_user)
) -> ScriptOut:
    """Salva modifiche manuali allo script (description, dialoghi, scene per vignetta).

    Ricostruisce il PydScript dal payload e sovrascrive quello del progetto.
    Non tocca il source_text. Non chiama Claude. Gratuito.
    """
    from snaptoon_core.models import Character, Dialogue, Page, Panel
    from snaptoon_core.models import Script as PydScript

    user_id = uuid.UUID(user["id"])
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")

        pyd_script = PydScript(
            logline=payload.logline,
            characters=[
                Character(name=c.name, visual_bible=c.visual_bible, voice=c.voice)
                for c in payload.characters
            ],
            pages=[
                Page(
                    number=p.number,
                    panels=[
                        Panel(
                            number=pn.number,
                            description=pn.description,
                            dialogues=[
                                Dialogue(
                                    kind=d.kind or "FUMETTO",
                                    speaker=d.speaker,
                                    text=d.text,
                                )
                                for d in pn.dialogues
                                if d.text and d.text.strip()
                            ],
                            shot_distance=pn.shot_distance,
                            shot_angle=pn.shot_angle,
                            mood=pn.mood,
                        )
                        for pn in p.panels
                    ],
                )
                for p in payload.pages
            ],
        )

        orm_script = scripts_repo.get_or_create(s, project)
        scripts_repo.save_pydantic(s, orm_script, pyd_script)

    return _pyd_to_out(pyd_script)


@router.post(
    "/projects/{slug}/characters/sync-from-script",
    response_model=CharacterSyncOut,
)
def sync_characters_from_script(
    slug: str, user: dict = Depends(require_user)
) -> CharacterSyncOut:
    """Crea CharacterSheet per ogni Script.characters non ancora presente nel cast.

    Utile quando lo script è stato adattato prima che V2 avesse l'auto-populate
    (progetti pre-esistenti). Non elimina character esistenti.
    """
    user_id = uuid.UUID(user["id"])
    created: list[str] = []
    existing: list[str] = []
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, slug)
        if project is None:
            raise HTTPException(status_code=404, detail="Progetto non trovato")
        if project.script is None:
            return CharacterSyncOut(created=[], already_existing=[])
        try:
            pyd = scripts_repo.load_pydantic(project.script)
        except Exception:
            return CharacterSyncOut(created=[], already_existing=[])

        existing_names_lower = {c.name.lower() for c in project.character_sheets}
        for pyd_char in pyd.characters:
            if pyd_char.name.lower() in existing_names_lower:
                existing.append(pyd_char.name)
                continue
            try:
                characters_repo.create_character(
                    s, project=project, name=pyd_char.name,
                    visual_description=pyd_char.visual_bible or "",
                )
                created.append(pyd_char.name)
            except ValueError:
                existing.append(pyd_char.name)
    return CharacterSyncOut(created=created, already_existing=existing)
