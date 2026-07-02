"""Tutte le tabelle del database SnapToon.

12 tabelle organizzate per area:
  Auth/account:        User, UserSession
  Progetto:            Project, Script, CharacterSheet, ReferenceImage, PageLayout, Cover
  Generazione:         Vignette
  Billing & audit:     CreditLedger, UsageLog, AdminAudit

Convenzioni:
- Chiavi primarie: UUID (auto-generate, indipendenti dal DB host)
- Timestamp: created_at su tutto, updated_at dove ha senso
- Soft-delete: deleted_at su Project (non eliminiamo dati di un utente pagante per errore)
- Hard-delete: tutto il resto (FK cascade su Project)
- Enum: PostgreSQL ENUM type, riusabile (non duplicato per tabella)
- JSON payload: per aggregati complessi (es. Script) usiamo JSONB pieno, query rare
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin, UpdatedAtMixin, utcnow


# ============================================================
# ENUM
# ============================================================


class Plan(str, enum.Enum):
    """LEGACY — piano abbonamento. Manteniamo per backward compat
    e come traccia commerciale, ma le decisioni di permessi e qualità
    sono ora basate su Role."""

    free_trial = "free_trial"
    creator = "creator"
    pro = "pro"


class Role(str, enum.Enum):
    """Ruolo utente. Determina permessi, limiti, qualità AI ammesse.

    - admin            : super-utente con accesso al pannello admin
    - autore_base      : creator standard (Bassa + Media quality)
    - autore_premium   : creator avanzato (anche Alta quality)
    - editore          : pubblica nel bookshop + accesso a export IDML (futuro)
    - kids             : modalità semplificata wizard 5-step per libri illustrati bambini
    """

    admin = "admin"
    autore_base = "autore_base"
    autore_premium = "autore_premium"
    editore = "editore"
    kids = "kids"


class LengthTarget(str, enum.Enum):
    """Lunghezza target del progetto (numero pagine consigliato)."""

    striscia = "striscia"  # 1-2 pagine
    breve = "breve"        # 3-6 pagine
    medio = "medio"        # 8-16 pagine
    lungo = "lungo"        # 24+ pagine


class CreditOperation(str, enum.Enum):
    """Tipo di operazione sul ledger crediti.

    Convenzione segno (delta):
    - Positivo (entrata): signup_grant, period_renewal, admin_grant, mock_purchase
    - Negativo (uscita):  generate_*, adapt_script, generate_subject
    - Zero:               (mai)
    """

    signup_grant = "signup_grant"
    period_renewal = "period_renewal"
    admin_grant = "admin_grant"
    mock_purchase = "mock_purchase"
    generate_panel = "generate_panel"
    generate_reference = "generate_reference"
    generate_variant = "generate_variant"
    generate_cover = "generate_cover"
    adapt_script = "adapt_script"
    generate_subject = "generate_subject"
    refund = "refund"  # rimborso post-failure


# ============================================================
# Auth & Account
# ============================================================


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_seen_onboarding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Ruolo (autoritativo per permessi/qualità). is_admin resta come flag
    # legacy ma è derivabile da role == Role.admin.
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role_enum", values_callable=lambda x: [e.value for e in x]),
        default=Role.autore_base,
        nullable=False,
    )

    # Piano commerciale (LEGACY tracking — ora i permessi vengono da role)
    plan: Mapped[Plan] = mapped_column(
        Enum(Plan, name="plan_enum", values_callable=lambda x: [e.value for e in x]),
        default=Plan.free_trial,
        nullable=False,
    )
    credits_total_this_period: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    credits_used_this_period: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    period_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    period_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    projects: Mapped[list["Project"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", lazy="select"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    credit_ledger: Mapped[list["CreditLedger"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    @property
    def credits_remaining(self) -> int:
        return max(0, self.credits_total_this_period - self.credits_used_this_period)


class UserSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    user: Mapped[User] = relationship(back_populates="sessions")


# ============================================================
# Progetto
# ============================================================


class Project(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("owner_user_id", "slug", name="uq_project_owner_slug"),
        Index("ix_project_owner_updated", "owner_user_id", "updated_at"),
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    length_target: Mapped[LengthTarget] = mapped_column(
        Enum(LengthTarget, name="length_target_enum", values_callable=lambda x: [e.value for e in x]),
        default=LengthTarget.medio,
        nullable=False,
    )
    page_format: Mapped[str] = mapped_column(String(16), default="A4", nullable=False)

    style_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_text: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Aspetto visivo personalizzato (sfondo + balloon/caption/sfx colors).
    # Schema JSON libero; vedi appearance.py per il contratto.
    appearance: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Pagina copyright (testo libero markdown). Se valorizzato, viene aggiunta
    # come ultima pagina nel PDF export.
    copyright_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    owner: Mapped[User] = relationship(back_populates="projects")
    script: Mapped["Script | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
    character_sheets: Mapped[list["CharacterSheet"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="CharacterSheet.order_idx"
    )
    page_layouts: Mapped[list["PageLayout"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="PageLayout.page_number"
    )
    vignettes: Mapped[list["Vignette"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    cover: Mapped["Cover | None"] = relationship(
        back_populates="project", uselist=False, cascade="all, delete-orphan"
    )


class Script(UUIDPrimaryKeyMixin, UpdatedAtMixin, Base):
    """Sceneggiatura del progetto. JSONB con l'intero payload Pydantic Script,
    + colonne denormalizzate per query veloci (logline, n_pages, n_panels)."""

    __tablename__ = "scripts"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    logline: Mapped[str] = mapped_column(Text, default="", nullable=False)
    n_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    n_panels: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    project: Mapped[Project] = relationship(back_populates="script")


class CharacterSheet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "character_sheets"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_charsheet_project_name"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    visual_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    color_palette: Mapped[str] = mapped_column(Text, default="", nullable=False)
    order_idx: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    project: Mapped[Project] = relationship(back_populates="character_sheets")
    references: Mapped[list["ReferenceImage"]] = relationship(
        back_populates="character_sheet",
        cascade="all, delete-orphan",
        order_by="ReferenceImage.slot_number",
    )


class ReferenceImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Slot 1..7 di reference image per un personaggio."""

    __tablename__ = "reference_images"
    __table_args__ = (
        UniqueConstraint(
            "character_sheet_id", "slot_number", name="uq_refimg_charsheet_slot"
        ),
    )

    character_sheet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("character_sheets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), default="image/png", nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    variant_kind: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # ^ profile / three_quarter / full_body / smiling / dramatic / back. None su slot 1.

    character_sheet: Mapped[CharacterSheet] = relationship(back_populates="references")


class PageLayout(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "page_layouts"
    __table_args__ = (
        UniqueConstraint("project_id", "page_number", name="uq_pagelayout_project_page"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    grid_id: Mapped[str] = mapped_column(String(64), default="2x2", nullable=False)
    show_balloons: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    project: Mapped[Project] = relationship(back_populates="page_layouts")


class Cover(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "covers"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    subtitle: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    author: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Payload completo (TextBox positions, scene params, characters_in_scene) come JSONB
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    illustration_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rendered_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    project: Mapped[Project] = relationship(back_populates="cover")


# ============================================================
# Vignette generate
# ============================================================


class Vignette(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    __tablename__ = "vignettes"
    __table_args__ = (
        UniqueConstraint("project_id", "page_number", "panel_number", name="uq_vignette_p_p"),
        Index("ix_vignette_project", "project_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    panel_number: Mapped[int] = mapped_column(Integer, nullable=False)

    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Hash include prompt + refs + quality + size. Cambia uno → si rigenera.

    quality: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    aspect_ratio_key: Mapped[str] = mapped_column(String(16), default="1_1", nullable=False)

    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # openai | gemini
    model: Mapped[str] = mapped_column(String(64), nullable=False)

    project: Mapped[Project] = relationship(back_populates="vignettes")


# ============================================================
# Billing & Audit
# ============================================================


class CreditLedger(UUIDPrimaryKeyMixin, Base):
    """Ledger immutabile dei movimenti crediti. Append-only.

    Cancellare/modificare righe è VIETATO. Per correggere errori si fa
    una nuova riga di segno opposto con `reason` descrittivo.
    """

    __tablename__ = "credit_ledger"
    __table_args__ = (Index("ix_ledger_user_time", "user_id", "occurred_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    operation: Mapped[CreditOperation] = mapped_column(
        Enum(
            CreditOperation,
            name="credit_operation_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
    )
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # ^ es. UUID di vignetta, o "page_5_panel_3" per audit
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    user: Mapped[User] = relationship(back_populates="credit_ledger")


class UsageLog(UUIDPrimaryKeyMixin, Base):
    """Log operazioni AI (audit + abuse detection + analytics)."""

    __tablename__ = "usage_log"
    __table_args__ = (Index("ix_usage_user_time", "user_id", "occurred_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True
    )
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    credits_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class KidsTemplate(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    """Template pre-configurati per la modalità Kids.

    Combina N personaggi (1/2/3) × lunghezza (breve/lungo) per generare
    automaticamente la sequenza di gabbie e scene del fumetto. L'utente
    Kids sceglie SOLO template + stile, niente di altro.

    grid_distribution: list[str] — sequenza di grid_id per ogni pagina
                       (es. ["splash", "1+2", "2x2", "1+2", "2x2", "splash"])
    scene_distribution: list[dict] — uno per ogni vignetta nell'ordine in cui
                        appaiono (espandi grid_distribution per cell);
                        ogni dict ha shot_distance, shot_angle, mood (optional).
    """

    __tablename__ = "kids_templates"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_kids_templates_slug"),
    )

    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    n_characters: Mapped[int] = mapped_column(Integer, nullable=False)
    # length_target memorizzato come VARCHAR per evitare collisioni su
    # length_target_enum già esistente. LengthTarget(str, Enum) gestisce
    # la validazione/conversione a livello applicativo.
    length_target: Mapped[str] = mapped_column(String(16), nullable=False)
    grid_distribution: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    scene_distribution: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class CastArchiveEntry(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    """Archivio personale dei personaggi riusabili tra progetti ("I miei personaggi").

    L'utente può creare personaggi da descrizione testuale o da foto reale
    (foto immediatamente cancellata dopo la generazione della reference AI),
    e importarli in qualsiasi progetto (KIDS o Pro).

    reference_storage_key è la PNG del ritratto in stile neutro / portrait
    realistico, salvata in object storage in "my-characters/{user_id}/{id}.png".
    Se None, il personaggio non ha ancora una reference generata.

    Soft-delete via deleted_at (per non perdere lo storico se importato in
    progetti esistenti; le reference importate rimangono nei progetti).
    """

    __tablename__ = "cast_archive_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_cast_archive_user_name"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    visual_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    color_palette: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reference_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AdminStyle(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    """Stili visivi creati/curati dall'admin, disponibili a tutti gli utenti.

    Si affiancano ai 98 preset hardcoded della libreria visual-prompt-engine.
    Permettono di aggiungere stili senza redeploy.

    Schema compatibile con StylePreset di snaptoon_core.styles_library:
    label + category + expansion + extra_negative_terms + is_handmade.
    """

    __tablename__ = "admin_styles"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_admin_styles_slug"),
    )

    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="Personali")
    expansion: Mapped[str] = mapped_column(Text, nullable=False)
    negative_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_handmade: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class EsploraAsset(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    """Asset mostrati nella pagina pubblica /esplora, curati dall'admin.

    Tre sezioni: copertine, tavole, personaggi. Ogni asset ha metadati
    (titolo, didascalia, posizione) e un'immagine opzionale in object storage.
    L'admin può caricare/generare/rigenerare/eliminare l'immagine.
    """

    __tablename__ = "esplora_assets"
    __table_args__ = (
        Index("ix_esplora_assets_section_position", "section", "position"),
    )

    section: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # ^ copertine | tavole | personaggi
    asset_type: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    # ^ "Tipo" mostrato in alto nella card (es. KIDSTOONS)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    caption: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    author_name: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    author_role: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AdminAudit(UUIDPrimaryKeyMixin, Base):
    """Log azioni admin (creazione utenti, grant crediti, disable account)."""

    __tablename__ = "admin_audit"

    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    # ^ create_user / grant_credits / disable_user / reactivate_user / change_plan
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )


class CreaImage(UUIDPrimaryKeyMixin, TimestampMixin, UpdatedAtMixin, Base):
    """Immagini della pagina pubblica /crea, sovrascrivibili dall'admin.

    Slot fissi (6): dashboard, step-testo, step-stile, step-personaggi,
    step-genera, step-impagina. Ogni slot ha al più una riga. Se non esiste
    riga (o storage_key è None), il frontend usa il default statico in
    web/public/images/crea/. L'upload converte in WebP (come Esplora).
    """

    __tablename__ = "crea_images"

    slot: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # ^ dashboard | step-testo | step-stile | step-personaggi | step-genera | step-impagina
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
