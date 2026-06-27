"""Repository sceneggiature.

Lo Script è memorizzato come JSONB (payload completo del Pydantic
snaptoon_core.models.Script) + colonne denormalizzate (logline, n_pages,
n_panels) per query veloci nelle liste progetti.

Pattern:
    script_model = scripts.get_or_create(session, project)
    # script_model è un'istanza ORM
    snaptoon_script = scripts.load_pydantic(script_model)
    # snaptoon_script è un Pydantic Script (usabile dai builder prompt)
    snaptoon_script.logline = "Nuova logline"
    scripts.save_pydantic(session, script_model, snaptoon_script)
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from snaptoon_core.models import Script as PydScript

from ..models import Project, Script


def get_for_project(session: Session, project: Project) -> Script | None:
    """Restituisce il record ORM Script per il progetto (o None)."""
    return project.script


def get_or_create(session: Session, project: Project) -> Script:
    """Restituisce lo Script ORM, creandolo vuoto se non esiste."""
    if project.script is not None:
        return project.script
    s = Script(
        project_id=project.id,
        logline="",
        n_pages=0,
        n_panels=0,
        payload={"logline": "", "characters": [], "pages": []},
    )
    session.add(s)
    session.flush()
    project.script = s
    return s


def load_pydantic(orm_script: Script) -> PydScript:
    """Deserializza il payload JSONB in un Pydantic Script."""
    return PydScript.model_validate(orm_script.payload)


def save_pydantic(
    session: Session, orm_script: Script, pyd_script: PydScript
) -> None:
    """Salva il Pydantic Script come JSONB + aggiorna colonne denormalizzate."""
    orm_script.payload = pyd_script.model_dump()
    orm_script.logline = pyd_script.logline
    orm_script.n_pages = len(pyd_script.pages)
    orm_script.n_panels = sum(len(p.panels) for p in pyd_script.pages)
