"""Repository page_layouts — gabbia + visibilità balloon per pagina."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import PageLayout, Project


def get(session: Session, project: Project, page_number: int) -> PageLayout | None:
    for pl in project.page_layouts:
        if pl.page_number == page_number:
            return pl
    return None


def get_or_create(
    session: Session, project: Project, page_number: int, *, default_grid: str = "2x2"
) -> PageLayout:
    existing = get(session, project, page_number)
    if existing is not None:
        return existing
    pl = PageLayout(
        project_id=project.id,
        page_number=page_number,
        grid_id=default_grid,
        show_balloons=True,
    )
    session.add(pl)
    session.flush()
    return pl


def set_grid(session: Session, pl: PageLayout, grid_id: str) -> None:
    pl.grid_id = grid_id


def set_show_balloons(session: Session, pl: PageLayout, show: bool) -> None:
    pl.show_balloons = show


def list_for_project(session: Session, project: Project) -> list[PageLayout]:
    return list(project.page_layouts)
