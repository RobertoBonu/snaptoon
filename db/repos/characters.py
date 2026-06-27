"""Repository character sheets + reference image slots."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import CharacterSheet, Project, ReferenceImage


# ============================================================
# Character sheets
# ============================================================


def list_for_project(session: Session, project: Project) -> list[CharacterSheet]:
    return list(project.character_sheets)


def get_by_name(
    session: Session, project: Project, name: str
) -> CharacterSheet | None:
    """Lookup case-insensitive per nome dentro un progetto."""
    name_lc = name.strip().lower()
    for cs in project.character_sheets:
        if cs.name.strip().lower() == name_lc:
            return cs
    return None


def create_character(
    session: Session,
    *,
    project: Project,
    name: str,
    visual_description: str = "",
    color_palette: str = "",
) -> CharacterSheet:
    name = name.strip()
    if not name:
        raise ValueError("Il nome del personaggio non può essere vuoto.")
    if get_by_name(session, project, name) is not None:
        raise ValueError(f"Esiste già un personaggio chiamato «{name}» in questo progetto.")
    order_idx = len(project.character_sheets)
    cs = CharacterSheet(
        project_id=project.id,
        name=name,
        visual_description=visual_description,
        color_palette=color_palette,
        order_idx=order_idx,
    )
    session.add(cs)
    session.flush()
    return cs


def update_character(
    session: Session,
    cs: CharacterSheet,
    *,
    visual_description: str | None = None,
    color_palette: str | None = None,
) -> None:
    if visual_description is not None:
        cs.visual_description = visual_description
    if color_palette is not None:
        cs.color_palette = color_palette


def rename_character(
    session: Session, cs: CharacterSheet, new_name: str
) -> None:
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Il nuovo nome non può essere vuoto.")
    cs.name = new_name


def delete_character(session: Session, cs: CharacterSheet) -> None:
    session.delete(cs)


# ============================================================
# Reference image slots (1..7 per personaggio)
# ============================================================

MAX_REFERENCE_SLOTS = 7


def list_references(
    session: Session, cs: CharacterSheet
) -> list[ReferenceImage]:
    return list(cs.references)


def get_reference_slot(
    session: Session, cs: CharacterSheet, slot_number: int
) -> ReferenceImage | None:
    for ref in cs.references:
        if ref.slot_number == slot_number:
            return ref
    return None


def upsert_reference(
    session: Session,
    cs: CharacterSheet,
    *,
    slot_number: int,
    storage_key: str,
    mime_type: str = "image/png",
    file_size: int = 0,
    variant_kind: str | None = None,
) -> ReferenceImage:
    """Crea o aggiorna lo slot reference. Per slot 1: variant_kind=None.

    Per slot 2-7: variant_kind ∈ {profile, three_quarter, full_body, smiling, dramatic, back}.
    """
    if slot_number < 1 or slot_number > MAX_REFERENCE_SLOTS:
        raise ValueError(f"slot_number deve essere tra 1 e {MAX_REFERENCE_SLOTS}.")

    existing = get_reference_slot(session, cs, slot_number)
    if existing is not None:
        existing.storage_key = storage_key
        existing.mime_type = mime_type
        existing.file_size = file_size
        existing.variant_kind = variant_kind
        return existing

    ref = ReferenceImage(
        character_sheet_id=cs.id,
        slot_number=slot_number,
        storage_key=storage_key,
        mime_type=mime_type,
        file_size=file_size,
        variant_kind=variant_kind,
    )
    session.add(ref)
    session.flush()
    return ref


def delete_reference_slot(
    session: Session, cs: CharacterSheet, slot_number: int
) -> bool:
    """Elimina lo slot. Ritorna True se trovato e cancellato."""
    ref = get_reference_slot(session, cs, slot_number)
    if ref is None:
        return False
    session.delete(ref)
    return True
