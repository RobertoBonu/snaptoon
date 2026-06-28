"""SnapToon — pagina 🖼 Genera vignette.

Per ogni vignetta della sceneggiatura, genera immagine con OpenAI gpt-image-2
usando lo stile attivo + reference image dei personaggi in scena come visual
ground truth per la coerenza.

Flusso per vignetta:
  1. Auto-detect cast in scena dal testo della descrizione
  2. Carica reference image dei personaggi rilevati
  3. Build prompt: stile + scena + cast + consistency + render mode
  4. Charge 1 credito
  5. OpenAI generate (con reference images via images.edit)
  6. Upload PNG in Object Storage
  7. Save record Vignette + usage_log

MVP V1: aspect_ratio fissa 1024x1024, quality medium, niente balloon editor
V1.1: scelta aspect per vignetta, quality, balloon editor, scene parameters
"""

from __future__ import annotations

import hashlib
import tempfile
import time
import uuid
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Genera — SnapToon",
    page_icon="🖼",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _inject_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "style" / "custom.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


_inject_css()

from app_state.ui import enforce_sidebar_visibility
enforce_sidebar_visibility()


# ============================================================
# Imports backend
# ============================================================
import app_state as appstate
from auth import current_user, logout
from billing.plans import cost_for_operation, plan_config
from db.models import CreditOperation
from db.repos import credits as credits_repo
from db.repos import page_layouts as page_layouts_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import usage as usage_repo
from db.repos import users as users_repo
from db.repos import vignettes as vignettes_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from snaptoon_core.layout import DEFAULT_SHAPE, GRIDS, SHAPES
from snaptoon_core.models import Panel, Script as PydScript
from snaptoon_core.scene import ASPECT_RATIOS, MOODS, SHOT_ANGLES, SHOT_DISTANCES
from snaptoon_core.styles_library import get_preset
from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import reference_key, vignette_key


# ============================================================
# Auth + project gate
# ============================================================
with session_scope() as _s:
    _user = current_user(_s)

if _user is None:
    st.error("Devi accedere per usare questa pagina.")
    st.markdown("[← Torna al login](/)")
    st.stop()

if _user.must_change_password:
    st.warning("Devi prima impostare una password personale dalla home.")
    st.markdown("[← Torna alla home](/)")
    st.stop()


_current_slug = appstate.get_current_project_slug()
if _current_slug is None:
    st.title("🖼 Genera")
    st.error("Nessun progetto attivo.")
    st.info("Apri un progetto dalla **home** o creane uno nuovo.")
    st.markdown("[← Vai alla home](/)")
    st.stop()


# ============================================================
# Sidebar
# ============================================================


def _render_sidebar(user, project_name: str, plan_label: str, credits_left: int, credits_total: int) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="snaptoon-sidebar-logo">
              <span class="snaptoon-sidebar-logo__wordmark">
                SnapToon<span class="snaptoon-sidebar-logo__dot"></span>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(user.email)
        st.caption(f"Piano: **{plan_label}** · {credits_left}/{credits_total} crediti")
        st.divider()
        st.markdown("**Progetto attivo:**")
        st.markdown(f"_{project_name}_")
        st.divider()
        if st.button("🚪 Esci", key="_sb_logout_gen", use_container_width=True):
            with session_scope() as s:
                logout(s)
            appstate.clear_session_keys()
            st.switch_page("app.py")


# ============================================================
# Helper: salvataggi script + page layout
# ============================================================


def _save_grid_for_page(project_id: uuid.UUID, page_number: int, grid_id: str) -> None:
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None:
            return
        pl = page_layouts_repo.get_or_create(s, project, page_number, default_grid=grid_id)
        page_layouts_repo.set_grid(s, pl, grid_id)


def _update_panel_in_script(
    project_id: uuid.UUID,
    page_number: int,
    panel_number: int,
    *,
    characters_in_scene: list[str] | None = None,
    aspect_ratio: str | None = None,
    shot_distance: str | None = None,
    shot_angle: str | None = None,
    mood: str | None = None,
) -> None:
    """Aggiorna campi scena di un Panel dentro lo Script JSONB."""
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None or project.script is None:
            return
        pyd_script = scripts_repo.load_pydantic(project.script)
        for page in pyd_script.pages:
            if page.number != page_number:
                continue
            for panel in page.panels:
                if panel.number != panel_number:
                    continue
                if characters_in_scene is not None:
                    panel.characters_in_scene = characters_in_scene
                if aspect_ratio is not None:
                    panel.aspect_ratio = aspect_ratio or None
                if shot_distance is not None:
                    panel.shot_distance = shot_distance or None
                if shot_angle is not None:
                    panel.shot_angle = shot_angle or None
                if mood is not None:
                    panel.mood = mood or None
                break
        scripts_repo.save_pydantic(s, project.script, pyd_script)


def _update_dialogue_in_script(
    project_id: uuid.UUID,
    page_number: int,
    panel_number: int,
    dialogue_index: int,
    *,
    shape: str | None = None,
    position_x: float | None = None,
    position_y: float | None = None,
    show_tail: bool | None = None,
) -> None:
    """Aggiorna campi balloon di un Dialogue dentro lo Script JSONB."""
    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        if project is None or project.script is None:
            return
        pyd_script = scripts_repo.load_pydantic(project.script)
        for page in pyd_script.pages:
            if page.number != page_number:
                continue
            for panel in page.panels:
                if panel.number != panel_number:
                    continue
                if not panel.dialogues or dialogue_index >= len(panel.dialogues):
                    return
                dlg = panel.dialogues[dialogue_index]
                if shape is not None:
                    dlg.shape = shape or None
                if position_x is not None:
                    dlg.position_x = position_x
                if position_y is not None:
                    dlg.position_y = position_y
                if show_tail is not None:
                    dlg.show_tail = show_tail
                break
        scripts_repo.save_pydantic(s, project.script, pyd_script)


# ============================================================
# Helper: auto-detect cast in scena
# ============================================================


def _detect_cast_in_panel(panel_description: str, cast_view: list[dict]) -> list[dict]:
    """Cerca nei caratteri del cast quelli citati nel testo del panel.

    Match case-insensitive sui nomi (parola intera o sostringa).
    """
    desc_lc = panel_description.lower()
    detected = []
    for cs in cast_view:
        name_lc = cs["name"].lower()
        if name_lc in desc_lc:
            detected.append(cs)
    return detected


def _resolve_cast_for_panel(panel: Panel, cast_view: list[dict]) -> list[dict]:
    """Cast da usare per la generazione: esplicito vince su auto-detect."""
    if panel.characters_in_scene:
        explicit_set = {n.lower() for n in panel.characters_in_scene}
        return [cs for cs in cast_view if cs["name"].lower() in explicit_set]
    return _detect_cast_in_panel(panel.description, cast_view)


# ============================================================
# Aspect ratio → OpenAI size mapping
# ============================================================

_ASPECT_TO_OPENAI_SIZE = {
    "1_1": "1024x1024",
    "3_4": "1024x1536",
    "2_3": "1024x1536",
    "9_16": "1024x1536",
    "4_3": "1536x1024",
    "3_2": "1536x1024",
    "16_9": "1536x1024",
    "2_1": "1536x1024",
}


def _resolve_openai_size(aspect_key: str | None) -> str:
    if aspect_key and aspect_key in _ASPECT_TO_OPENAI_SIZE:
        return _ASPECT_TO_OPENAI_SIZE[aspect_key]
    return "1024x1024"


# ============================================================
# Helper: prompt builder
# ============================================================


def _scene_clauses(panel: Panel) -> str:
    """Costruisce le clausole 'regia' della scena (aspect + framing + mood)."""
    clauses: list[str] = []

    # Aspect ratio
    if panel.aspect_ratio:
        opt = next((o for o in ASPECT_RATIOS if o.key == panel.aspect_ratio), None)
        if opt:
            clauses.append(f"FORMAT: {opt.prompt_en}.")

    # Distanza inquadratura
    if panel.shot_distance:
        opt = next((o for o in SHOT_DISTANCES if o.key == panel.shot_distance), None)
        if opt:
            clauses.append(f"SHOT DISTANCE: {opt.prompt_en}.")

    # Angolo
    if panel.shot_angle:
        opt = next((o for o in SHOT_ANGLES if o.key == panel.shot_angle), None)
        if opt:
            clauses.append(f"CAMERA ANGLE: {opt.prompt_en}.")

    # Mood
    if panel.mood:
        opt = next((o for o in MOODS if o.key == panel.mood), None)
        if opt:
            clauses.append(f"MOOD: {opt.prompt_en}.")

    return " ".join(clauses)


def _build_panel_prompt(
    panel: Panel,
    preset_expansion: str,
    preset_negative: tuple[str, ...],
    cast_in_scene: list[dict],
) -> str:
    """Costruisce il prompt per generare una vignetta.

    Combina: render-mode + stile + scena + clausole regia + cast + negative.
    """
    parts: list[str] = []

    # Render directive (FIRST — più peso)
    parts.append(
        "=== RENDER MODE ===\n"
        "Edge-to-edge full-bleed image, no frame, no border, no caption, no text. "
        "Cinematic single-panel composition. The image must be a finished comic panel "
        "rendered in the specified visual style."
    )

    # Stile
    if preset_expansion:
        parts.append(f"=== STYLE ===\n{preset_expansion.strip()}")

    # Scena
    parts.append(f"=== SCENE ===\n{panel.description.strip()}")

    # Clausole regia (aspect + framing + mood) se settate
    scene_directives = _scene_clauses(panel)
    if scene_directives:
        parts.append(f"=== DIRECTING ===\n{scene_directives}")

    # Cast in scena con visual_description (rinforza consistency)
    if cast_in_scene:
        cast_block = ["=== CHARACTERS IN THIS PANEL ==="]
        for cs in cast_in_scene:
            cast_block.append(f"- {cs['name']}: {cs['visual_description']}")
        cast_block.append(
            "These characters MUST look IDENTICAL to the reference images provided. "
            "Match face, hair, clothing, body type exactly. The reference images are "
            "the visual ground truth."
        )
        parts.append("\n".join(cast_block))

    # AVOID
    negative_base = [
        "text in image", "speech bubble in image", "caption", "watermark",
        "frame", "border", "panel grid", "comic page layout",
        "multiple panels", "thumbnail mosaic",
    ]
    if preset_negative:
        negative_base.extend(preset_negative)
    parts.append("=== AVOID ===\n" + ", ".join(negative_base))

    return "\n\n".join(parts)


def _prompt_hash(prompt: str, ref_keys: list[str], quality: str, size: str) -> str:
    """Hash per cache: cambia se cambia uno qualsiasi degli input."""
    h = hashlib.sha256()
    h.update(prompt.encode("utf-8"))
    for k in sorted(ref_keys):
        h.update(b"|")
        h.update(k.encode("utf-8"))
    h.update(f"|q={quality}|s={size}".encode("utf-8"))
    return h.hexdigest()


# ============================================================
# Helper: generazione vignetta
# ============================================================


def _generate_vignette(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    project_slug: str,
    page_number: int,
    panel: Panel,
    preset_expansion: str,
    preset_negative: tuple[str, ...],
    cast_view: list[dict],
) -> tuple[bool, str | None]:
    """Genera una vignetta singola e la salva.

    Returns (success, error_msg).
    """
    from snaptoon_core.generator import OpenAIImageGenerator

    cost = cost_for_operation("generate_panel", quality="medium")
    t0 = time.time()
    size = _resolve_openai_size(panel.aspect_ratio)
    quality = "medium"

    # Detect cast in scena: esplicito vince su auto-detect
    cast_in_scene = _resolve_cast_for_panel(panel, cast_view)

    # Raccogli reference keys (slot 1 di ogni personaggio in scena, se esiste)
    ref_keys: list[str] = []
    for cs in cast_in_scene:
        if cs.get("ref_storage_key") and object_exists(cs["ref_storage_key"]):
            ref_keys.append(cs["ref_storage_key"])

    # Prompt
    prompt = _build_panel_prompt(panel, preset_expansion, preset_negative, cast_in_scene)
    p_hash = _prompt_hash(prompt, ref_keys, quality, size)
    vignette_storage_key = vignette_key(project_id, page_number, panel.number)

    # Charge atomic
    with session_scope() as s:
        user_db = users_repo.get_by_id(s, user_id)
        if user_db is None:
            return False, "Utente non trovato."
        try:
            credits_repo.charge(
                s,
                user_db,
                cost=cost,
                operation=CreditOperation.generate_panel,
                reason=f"Vignetta pag.{page_number} #{panel.number}",
                reference_id=f"{project_slug}:p{page_number:02d}:v{panel.number:02d}",
            )
        except InsufficientCreditsError as e:
            return False, f"Crediti insufficienti: ti servono {e.required}, ne hai {e.available}."

    # Scarica reference in temp files (richiesto da OpenAI images.edit)
    tmp_files: list[Path] = []
    try:
        for rk in ref_keys:
            data = download_bytes(rk)
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(data)
            tmp.close()
            tmp_files.append(Path(tmp.name))

        # Generazione vera
        generator = OpenAIImageGenerator()
        image_bytes = generator._generate_bytes(
            prompt=prompt,
            size=size,
            reference_images=tmp_files if tmp_files else None,
            quality=quality,
        )

        # Upload Object Storage
        upload_bytes(vignette_storage_key, image_bytes, content_type="image/png")

    except Exception as e:
        # Refund + usage log
        err = str(e)[:500]
        with session_scope() as s:
            user_db = users_repo.get_by_id(s, user_id)
            if user_db is not None:
                credits_repo.refund(
                    s,
                    user_db,
                    amount=cost,
                    reason=f"Refund per generate_panel fallito: {err}",
                    reference_id=f"{project_slug}:p{page_number:02d}:v{panel.number:02d}",
                )
                usage_repo.log_operation(
                    s,
                    user=user_db,
                    operation="generate_panel",
                    credits_spent=0,
                    success=False,
                    error_message=err,
                    latency_ms=int((time.time() - t0) * 1000),
                    project_id=project_id,
                )
        return False, f"Errore generazione: {err}"
    finally:
        # Cleanup temp files
        for tmp in tmp_files:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass

    # Save record DB + usage log
    with session_scope() as s:
        user_db = users_repo.get_by_id(s, user_id)
        project = projects_repo.get_by_id(s, project_id)
        if project is None:
            return False, "Progetto non trovato."

        vignettes_repo.upsert(
            s,
            project=project,
            page_number=page_number,
            panel_number=panel.number,
            storage_key=vignette_storage_key,
            prompt_hash=p_hash,
            quality=quality,
            aspect_ratio_key=panel.aspect_ratio or "1_1",
            provider="openai",
            model="gpt-image-2",
        )
        usage_repo.log_operation(
            s,
            user=user_db,
            operation="generate_panel",
            credits_spent=cost,
            success=True,
            latency_ms=int((time.time() - t0) * 1000),
            project_id=project_id,
        )

    return True, None


# ============================================================
# Lookup project + script + cast
# ============================================================


def _load_view(user_id, project_slug: str) -> dict | None:
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, project_slug)
        if project is None:
            return None
        if project.script is None or not project.script.payload.get("pages"):
            return {
                "id": project.id,
                "name": project.name,
                "style_id": project.style_id,
                "script": None,
                "cast": [],
                "vignettes_by_coords": {},
            }
        pyd_script = scripts_repo.load_pydantic(project.script)

        cast_view = []
        for cs in project.character_sheets:
            ref = next((r for r in cs.references if r.slot_number == 1), None)
            cast_view.append({
                "id": cs.id,
                "name": cs.name,
                "visual_description": cs.visual_description,
                "ref_storage_key": ref.storage_key if ref else None,
            })

        vigs = vignettes_repo.list_for_project(s, project)
        vigs_by_coords = {
            (v.page_number, v.panel_number): {
                "storage_key": v.storage_key,
                "quality": v.quality,
                "generated_at": v.created_at,
            }
            for v in vigs
        }

        # Page layouts (gabbie scelte per ogni pagina)
        grid_by_page: dict[int, str] = {}
        for pl in project.page_layouts:
            grid_by_page[pl.page_number] = pl.grid_id

        return {
            "id": project.id,
            "name": project.name,
            "style_id": project.style_id,
            "script": pyd_script,
            "cast": cast_view,
            "vignettes_by_coords": vigs_by_coords,
            "grid_by_page": grid_by_page,
        }


# ============================================================
# Render vignetta singola (card)
# ============================================================


def _render_vignette_card(
    panel: Panel,
    page_number: int,
    view: dict,
    user_id: uuid.UUID,
    user_credits_left: int,
    preset_expansion: str,
    preset_negative: tuple[str, ...],
) -> None:
    coords = (page_number, panel.number)
    has_image = coords in view["vignettes_by_coords"]
    cost = cost_for_operation("generate_panel", quality="medium")

    cast_in_scene = _detect_cast_in_panel(panel.description, view["cast"])
    refs_available = sum(
        1 for cs in cast_in_scene
        if cs.get("ref_storage_key") and object_exists(cs["ref_storage_key"])
    )

    with st.container(border=True):
        col_img, col_meta = st.columns([1, 2])

        with col_img:
            if has_image:
                try:
                    sk = view["vignettes_by_coords"][coords]["storage_key"]
                    image_data = download_bytes(sk)
                    st.image(image_data, use_container_width=True)
                except Exception:
                    st.warning("Errore lettura immagine. Rigenera.")
            else:
                st.markdown(
                    f"""
                    <div style="background:#161B26;border:1.5px dashed #2D3748;
                                border-radius:8px;padding:2.5rem 1rem;text-align:center;
                                color:#475569;min-height:200px;display:flex;
                                flex-direction:column;justify-content:center;">
                      <div style="font-size:1.75rem;">🖼</div>
                      <div style="margin-top:0.5rem;font-size:13px;">Vignetta {panel.number}</div>
                      <div style="margin-top:0.25rem;font-size:11px;">non ancora generata</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_meta:
            st.markdown(f"**Vignetta {panel.number}**")
            st.caption(panel.description[:300] + ("…" if len(panel.description) > 300 else ""))

            if cast_in_scene:
                names = [cs["name"] for cs in cast_in_scene]
                st.caption(f"👥 In scena: {', '.join(names)}  ({refs_available}/{len(cast_in_scene)} con reference)")
            else:
                st.caption("_Nessun personaggio del cast rilevato in scena._")

            n_dlg = len(panel.dialogues) if hasattr(panel, "dialogues") else 0
            if n_dlg > 0:
                st.caption(f"💬 {n_dlg} dialog{'o' if n_dlg == 1 else 'hi'} (rendering balloon nella pagina Impagina)")

            # Bottoni
            gen_label = "🔄 Rigenera" if has_image else "✨ Genera con AI"
            gen_disabled = user_credits_left < cost
            gen_help = None
            if gen_disabled:
                gen_help = f"Crediti insufficienti (servono {cost})."

            if st.button(
                gen_label,
                key=f"gen_p{page_number}_v{panel.number}",
                type="primary",
                disabled=gen_disabled,
                help=gen_help,
                use_container_width=True,
            ):
                with st.spinner(f"Genero vignetta {panel.number}..."):
                    success, err = _generate_vignette(
                        user_id=user_id,
                        project_id=view["id"],
                        project_slug=_current_slug,
                        page_number=page_number,
                        panel=panel,
                        preset_expansion=preset_expansion,
                        preset_negative=preset_negative,
                        cast_view=view["cast"],
                    )
                if success:
                    st.toast(f"Vignetta {panel.number} generata.", icon="✨")
                    st.rerun()
                else:
                    st.error(err)

            # Popover 🎬 Scena: cast esplicito + aspect/distance/angle/mood
            with st.popover("🎬 Scena", use_container_width=True):
                st.caption(
                    "Parametri di regia per questa vignetta. Vincolano "
                    "cast, formato, inquadratura, mood. Override del auto-detect."
                )

                # Cast esplicito
                all_cast_names = [cs["name"] for cs in view["cast"]]
                _all_set = set(all_cast_names)
                default_cast = [n for n in (panel.characters_in_scene or []) if n in _all_set]
                stale = [n for n in (panel.characters_in_scene or []) if n not in _all_set]
                if stale:
                    st.caption(f"⚠️ Personaggi non più nel cast: {', '.join(stale)}")
                if all_cast_names:
                    sel_cast = st.multiselect(
                        "👥 Personaggi nella vignetta",
                        options=all_cast_names,
                        default=default_cast,
                        key=f"sc_cast_p{page_number}_v{panel.number}",
                    )
                else:
                    sel_cast = []
                    st.caption("_Nessun personaggio nel cast. Vai su 👥 Personaggi._")

                # Aspect ratio
                aspect_opts = [("(default)", None)] + [(o.label, o.key) for o in ASPECT_RATIOS]
                aspect_labels = [lbl for lbl, _ in aspect_opts]
                current_aspect = panel.aspect_ratio
                current_idx = next(
                    (i for i, (_, k) in enumerate(aspect_opts) if k == current_aspect), 0
                )
                aspect_label = st.selectbox(
                    "📐 Formato vignetta",
                    aspect_labels,
                    index=current_idx,
                    key=f"sc_ar_p{page_number}_v{panel.number}",
                )
                sel_aspect_key = next(k for lbl, k in aspect_opts if lbl == aspect_label) or ""

                # Distanza
                dist_opts = [("(default)", None)] + [(o.label, o.key) for o in SHOT_DISTANCES]
                dist_labels = [lbl for lbl, _ in dist_opts]
                current_dist = panel.shot_distance
                d_idx = next((i for i, (_, k) in enumerate(dist_opts) if k == current_dist), 0)
                dist_label = st.selectbox(
                    "🎥 Distanza inquadratura",
                    dist_labels,
                    index=d_idx,
                    key=f"sc_sd_p{page_number}_v{panel.number}",
                )
                sel_dist_key = next(k for lbl, k in dist_opts if lbl == dist_label) or ""

                # Angolo
                angle_opts = [("(default)", None)] + [(o.label, o.key) for o in SHOT_ANGLES]
                angle_labels = [lbl for lbl, _ in angle_opts]
                current_angle = panel.shot_angle
                a_idx = next((i for i, (_, k) in enumerate(angle_opts) if k == current_angle), 0)
                angle_label = st.selectbox(
                    "🎞 Angolo",
                    angle_labels,
                    index=a_idx,
                    key=f"sc_sa_p{page_number}_v{panel.number}",
                )
                sel_angle_key = next(k for lbl, k in angle_opts if lbl == angle_label) or ""

                # Mood
                mood_opts = [("(default)", None)] + [(o.label, o.key) for o in MOODS]
                mood_labels = [lbl for lbl, _ in mood_opts]
                current_mood = panel.mood
                m_idx = next((i for i, (_, k) in enumerate(mood_opts) if k == current_mood), 0)
                mood_label = st.selectbox(
                    "🎭 Mood",
                    mood_labels,
                    index=m_idx,
                    key=f"sc_md_p{page_number}_v{panel.number}",
                )
                sel_mood_key = next(k for lbl, k in mood_opts if lbl == mood_label) or ""

                col_save, col_reset = st.columns(2)
                with col_save:
                    if st.button(
                        "💾 Salva scena",
                        key=f"sc_save_p{page_number}_v{panel.number}",
                        type="primary",
                        use_container_width=True,
                    ):
                        _update_panel_in_script(
                            project_id=view["id"],
                            page_number=page_number,
                            panel_number=panel.number,
                            characters_in_scene=sel_cast,
                            aspect_ratio=sel_aspect_key,
                            shot_distance=sel_dist_key,
                            shot_angle=sel_angle_key,
                            mood=sel_mood_key,
                        )
                        st.toast("Scena salvata.", icon="✅")
                        st.rerun()
                with col_reset:
                    if st.button(
                        "↩️ Reset",
                        key=f"sc_reset_p{page_number}_v{panel.number}",
                        use_container_width=True,
                    ):
                        _update_panel_in_script(
                            project_id=view["id"],
                            page_number=page_number,
                            panel_number=panel.number,
                            characters_in_scene=[],
                            aspect_ratio="",
                            shot_distance="",
                            shot_angle="",
                            mood="",
                        )
                        st.toast("Scena ripristinata.", icon="↩️")
                        st.rerun()

            # Popover 🎈 Balloon: posizionamento dialoghi
            if panel.dialogues:
                with st.popover(
                    f"🎈 Balloon ({len(panel.dialogues)})",
                    use_container_width=True,
                ):
                    st.caption(
                        "Forma e posizione di ogni dialogo. Verranno disegnati "
                        "come overlay nel rendering della pagina (📐 Impagina)."
                    )
                    for d_idx, dlg in enumerate(panel.dialogues):
                        st.markdown(f"**{d_idx + 1}. {dlg.kind}** — _{dlg.text[:50]}_")
                        speaker_label = f"({dlg.speaker})" if dlg.speaker else ""
                        if speaker_label:
                            st.caption(speaker_label)

                        # Shape
                        default_shape = DEFAULT_SHAPE.get(dlg.kind, "oval")
                        current_shape = dlg.shape or default_shape
                        sel_shape = st.selectbox(
                            "Forma",
                            options=SHAPES,
                            index=SHAPES.index(current_shape) if current_shape in SHAPES else 0,
                            key=f"bal_shape_p{page_number}_v{panel.number}_d{d_idx}",
                            format_func=lambda s, ds=default_shape: f"{s}{' (default)' if s == ds else ''}",
                        )

                        # Position
                        col_x, col_y = st.columns(2)
                        with col_x:
                            cur_x_pct = int((dlg.position_x or 0.5) * 100)
                            new_x = st.slider(
                                "X (%)",
                                0, 100, cur_x_pct,
                                key=f"bal_x_p{page_number}_v{panel.number}_d{d_idx}",
                            )
                        with col_y:
                            cur_y_pct = int((dlg.position_y or 0.15) * 100)
                            new_y = st.slider(
                                "Y (%)",
                                0, 100, cur_y_pct,
                                key=f"bal_y_p{page_number}_v{panel.number}_d{d_idx}",
                            )

                        show_tail = st.toggle(
                            "Tail visibile",
                            value=dlg.show_tail,
                            key=f"bal_tail_p{page_number}_v{panel.number}_d{d_idx}",
                        )

                        if st.button(
                            "💾 Salva balloon",
                            key=f"bal_save_p{page_number}_v{panel.number}_d{d_idx}",
                            type="primary",
                            use_container_width=True,
                        ):
                            _update_dialogue_in_script(
                                project_id=view["id"],
                                page_number=page_number,
                                panel_number=panel.number,
                                dialogue_index=d_idx,
                                shape=sel_shape,
                                position_x=new_x / 100.0,
                                position_y=new_y / 100.0,
                                show_tail=show_tail,
                            )
                            st.toast(f"Balloon {d_idx + 1} salvato.", icon="🎈")
                            st.rerun()
                        st.divider()


# ============================================================
# RENDER
# ============================================================

_view = _load_view(_user.id, _current_slug)
if _view is None:
    appstate.clear_current_project()
    st.error("Il progetto attivo non esiste più.")
    st.markdown("[← Vai alla home](/)")
    st.stop()


_plan_cfg = plan_config(_user.plan)
_render_sidebar(
    _user,
    project_name=_view["name"],
    plan_label=_plan_cfg.label,
    credits_left=_user.credits_remaining,
    credits_total=_user.credits_total_this_period,
)

st.title("🖼 Genera vignette")
st.caption(f"Progetto: **{_view['name']}**")

# Guard rails
if _view["script"] is None:
    st.error("Nessuna sceneggiatura nel progetto.")
    st.info("Vai su **📝 Testo** e adatta un sorgente in sceneggiatura prima.")
    st.stop()

if _view["style_id"] is None:
    st.warning(
        "Nessuno stile applicato al progetto. "
        "Vai su **🎨 Stile** e seleziona un preset prima di generare. "
        "(Lo stile è ciò che dà identità visiva al tuo fumetto.)"
    )
    st.stop()

_preset = get_preset(_view["style_id"])
if _preset is None:
    st.error(f"Lo stile salvato `{_view['style_id']}` non è più nella libreria. Riselezionalo in 🎨 Stile.")
    st.stop()

# Avviso character_sheets senza reference (compromette consistency)
chars_without_ref = [
    cs for cs in _view["cast"]
    if not cs.get("ref_storage_key") or not object_exists(cs["ref_storage_key"])
]
if chars_without_ref:
    names = ", ".join(cs["name"] for cs in chars_without_ref)
    st.warning(
        f"⚠️ {len(chars_without_ref)} personaggio/i senza reference image: **{names}**. "
        "La coerenza visiva tra vignette è garantita SOLO dai personaggi con reference. "
        "Vai su **👥 Personaggi** per generarle prima."
    )

# Status globale
all_panels = [(p.number, panel) for p in _view["script"].pages for panel in p.panels]
n_total = len(all_panels)
n_generated = sum(
    1 for page_num, panel in all_panels
    if (page_num, panel.number) in _view["vignettes_by_coords"]
)
n_missing = n_total - n_generated

st.markdown(f"### Stato: {n_generated}/{n_total} vignette generate")
st.progress(n_generated / n_total if n_total else 0)

# Bulk
if n_missing > 0:
    cost_per_vignette = cost_for_operation("generate_panel", quality="medium")
    cost_bulk = n_missing * cost_per_vignette
    can_bulk = _user.credits_remaining >= cost_bulk
    col_bulk, col_caption = st.columns([1, 3])
    with col_bulk:
        if st.button(
            f"🚀 Genera vignette mancanti ({n_missing})",
            type="primary",
            disabled=not can_bulk,
            help=None if can_bulk else f"Servono {cost_bulk} crediti, ne hai {_user.credits_remaining}.",
        ):
            progress = st.progress(0)
            status = st.empty()
            errors = []
            todo = [(p.number, panel) for p in _view["script"].pages for panel in p.panels
                    if (p.number, panel.number) not in _view["vignettes_by_coords"]]
            for i, (page_num, panel) in enumerate(todo, start=1):
                status.write(f"⏳ Pagina {page_num}, vignetta {panel.number}...")
                success, err = _generate_vignette(
                    user_id=_user.id,
                    project_id=_view["id"],
                    project_slug=_current_slug,
                    page_number=page_num,
                    panel=panel,
                    preset_expansion=_preset.expansion,
                    preset_negative=_preset.extra_negative_terms,
                    cast_view=_view["cast"],
                )
                if not success:
                    errors.append(f"p{page_num}v{panel.number}: {err}")
                progress.progress(i / len(todo))
            status.write(f"✅ Generate {len(todo) - len(errors)}/{len(todo)} vignette.")
            if errors:
                for e in errors:
                    st.error(e)
            st.rerun()
    with col_caption:
        st.caption(f"Costo: {cost_bulk} crediti totali ({cost_per_vignette} per vignetta).")

st.divider()

# ============================================================
# Lista pagine + vignette
# ============================================================

# Build lista opzioni grid: prima quelle con capienza esatta per N vignette
_GRID_OPTIONS_ALL = [(gid, g.name, g.capacity) for gid, g in GRIDS.items()]


def _grid_options_sorted(n_panels: int) -> list[tuple[str, str]]:
    """Restituisce (grid_id, label) ordinati: capienza esatta prima, poi altri."""
    matching = [(gid, lbl) for gid, lbl, cap in _GRID_OPTIONS_ALL if cap == n_panels]
    others = [(gid, lbl) for gid, lbl, cap in _GRID_OPTIONS_ALL if cap != n_panels]
    return matching + others


for page in _view["script"].pages:
    n_pg_generated = sum(
        1 for panel in page.panels
        if (page.number, panel.number) in _view["vignettes_by_coords"]
    )
    n_pg_total = len(page.panels)
    with st.expander(
        f"📖 Pagina {page.number} — {n_pg_generated}/{n_pg_total} vignette generate",
        expanded=True,
    ):
        # ============================================================
        # Selettore gabbia per la pagina
        # ============================================================
        current_grid = _view["grid_by_page"].get(page.number, "2x2")
        if current_grid not in GRIDS:
            current_grid = "2x2"
        grid_opts = _grid_options_sorted(n_pg_total)
        labels = [f"⭐ {lbl}" if GRIDS[gid].capacity == n_pg_total else lbl
                  for gid, lbl in grid_opts]
        ids = [gid for gid, _ in grid_opts]
        try:
            cur_idx = ids.index(current_grid)
        except ValueError:
            cur_idx = 0

        col_grid_sel, col_grid_save = st.columns([3, 1])
        with col_grid_sel:
            sel_grid_label = st.selectbox(
                f"🗂 Gabbia pagina {page.number}",
                options=labels,
                index=cur_idx,
                key=f"grid_sel_p{page.number}",
                help=(
                    f"La pagina ha {n_pg_total} vignette. "
                    "Le gabbie con la capienza esatta sono marcate ⭐."
                ),
            )
            sel_grid_id = ids[labels.index(sel_grid_label)]
            sel_grid_capacity = GRIDS[sel_grid_id].capacity
        with col_grid_save:
            if st.button(
                "💾 Salva",
                key=f"grid_save_p{page.number}",
                disabled=(sel_grid_id == current_grid),
                use_container_width=True,
                type="secondary",
            ):
                _save_grid_for_page(_view["id"], page.number, sel_grid_id)
                st.toast(f"Gabbia «{sel_grid_id}» salvata.", icon="🗂")
                st.rerun()

        if sel_grid_capacity != n_pg_total:
            st.caption(
                f"⚠️ Capienza gabbia: {sel_grid_capacity} celle vs {n_pg_total} vignette in pagina. "
                f"{'Le ultime ' + str(n_pg_total - sel_grid_capacity) + ' vignette saranno ignorate.' if sel_grid_capacity < n_pg_total else 'Resteranno ' + str(sel_grid_capacity - n_pg_total) + ' celle vuote.'}"
            )

        st.markdown("---")

        for panel in page.panels:
            _render_vignette_card(
                panel=panel,
                page_number=page.number,
                view=_view,
                user_id=_user.id,
                user_credits_left=_user.credits_remaining,
                preset_expansion=_preset.expansion,
                preset_negative=_preset.extra_negative_terms,
            )
