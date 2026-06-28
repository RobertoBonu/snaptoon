"""SnapToon — pagina 👥 Personaggi.

Gestione del cast del progetto: nome + descrizione visiva + reference image
(slot 1 = principale; slot 2-7 = varianti in V1.1).

Flusso:
  1. Lista cast (bootstrap automatico dall'adattamento Claude in Testo)
  2. Per ogni personaggio: edit visual_description + genera/upload reference
  3. Bulk: genera reference per tutti i mancanti
  4. Aggiungi/elimina personaggio manualmente
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Personaggi — SnapToon",
    page_icon="👥",
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
import time
import uuid

import app_state as appstate
from auth import current_user, logout
from billing.plans import cost_for_operation, plan_config
from db.models import CreditOperation
from db.repos import cast_archive as cast_archive_repo
from db.repos import characters as characters_repo
from db.repos import credits as credits_repo
from db.repos import projects as projects_repo
from db.repos import usage as usage_repo
from db.repos.credits import InsufficientCreditsError
from db.session import session_scope
from snaptoon_core.styles_library import get_preset
from storage.client import (
    delete_object,
    download_bytes,
    object_exists,
    upload_bytes,
)
from storage.keys import reference_key


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
    st.title("👥 Personaggi")
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
        if st.button("🚪 Esci", key="_sb_logout_pers", use_container_width=True):
            with session_scope() as s:
                logout(s)
            appstate.clear_session_keys()
            st.switch_page("app.py")


# ============================================================
# Helper: generazione reference AI
# ============================================================


def _build_reference_prompt(
    character_name: str,
    visual_description: str,
    style_id: str | None,
) -> str:
    """Costruisce un prompt minimal per reference image.

    Versione MVP: combina espansione dello stile (se presente) con
    visual_description del personaggio + clausole standard.

    NB: il prompt builder ricco di Creative Studio (build_character_reference_prompt
    con tutti i campi Style YAML) verrà integrato in V1.1 quando avremo i preset
    Style completi nel DB.
    """
    parts: list[str] = []

    # Stile
    style_preset = get_preset(style_id) if style_id else None
    if style_preset:
        parts.append(f"=== STILE ===\n{style_preset.expansion.strip()}")

    # Character
    parts.append(
        f"=== CHARACTER REFERENCE ===\n"
        f"Subject: {character_name}\n"
        f"Visual description: {visual_description.strip()}"
    )

    # Render directives
    parts.append(
        "=== RENDER MODE ===\n"
        "Full-body single character, neutral standing pose, centered composition. "
        "Clean uniform background, no environment. "
        "Studio reference shot for character consistency across multiple scenes. "
        "The image must show the character at full body, including face, hands and feet. "
        "Edge-to-edge full-bleed image. No frame, no border, no caption, no text."
    )

    # Negative
    negative_terms = ["text in image", "caption", "watermark", "frame", "border",
                      "comic panel", "speech bubble", "multiple characters"]
    if style_preset and style_preset.extra_negative_terms:
        negative_terms.extend(style_preset.extra_negative_terms)
    parts.append("=== AVOID ===\n" + ", ".join(negative_terms))

    return "\n\n".join(parts)


def _generate_reference_image(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    char_id: uuid.UUID,
    char_name: str,
    visual_description: str,
    style_id: str | None,
) -> tuple[bool, str | None]:
    """Genera una reference image via OpenAI gpt-image-2 e la salva.

    Returns:
        (success, error_msg)
    """
    from snaptoon_core.generator import OpenAIImageGenerator
    from db.repos import users as users_repo

    if not visual_description.strip():
        return False, "Manca la descrizione visiva del personaggio."

    cost = cost_for_operation("generate_reference")
    t0 = time.time()
    storage_key_path = reference_key(project_id, char_id, 1)

    # Charge crediti atomico
    with session_scope() as s:
        user_db = users_repo.get_by_id(s, user_id)
        if user_db is None:
            return False, "Utente non trovato."
        try:
            credits_repo.charge(
                s,
                user_db,
                cost=cost,
                operation=CreditOperation.generate_reference,
                reason=f"Reference image per personaggio «{char_name}»",
                reference_id=str(char_id),
            )
        except InsufficientCreditsError as e:
            return False, f"Crediti insufficienti: ti servono {e.required}, ne hai {e.available}."

    # Chiama OpenAI fuori dalla session DB (è una chiamata lunga, non vogliamo tenere lock)
    try:
        prompt = _build_reference_prompt(char_name, visual_description, style_id)
        generator = OpenAIImageGenerator()
        # Uso _generate_bytes direttamente (non passa dal filesystem)
        image_bytes = generator._generate_bytes(
            prompt=prompt,
            size="1024x1024",
            reference_images=None,
            quality="medium",
        )
        # Upload in Object Storage
        upload_bytes(storage_key_path, image_bytes, content_type="image/png")

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
                    reason=f"Refund per generate_reference fallito: {err}",
                    reference_id=str(char_id),
                )
                usage_repo.log_operation(
                    s,
                    user=user_db,
                    operation="generate_reference",
                    credits_spent=0,
                    success=False,
                    error_message=err,
                    latency_ms=int((time.time() - t0) * 1000),
                    project_id=project_id,
                )
        return False, f"Errore durante la generazione: {err}"

    # Save record DB + log
    with session_scope() as s:
        user_db = users_repo.get_by_id(s, user_id)
        project = projects_repo.get_by_id(s, project_id)
        cs = next((c for c in project.character_sheets if c.id == char_id), None) if project else None
        if cs is None:
            return False, "Personaggio non trovato (forse eliminato)."

        characters_repo.upsert_reference(
            s,
            cs,
            slot_number=1,
            storage_key=storage_key_path,
            mime_type="image/png",
            file_size=len(image_bytes),
        )
        usage_repo.log_operation(
            s,
            user=user_db,
            operation="generate_reference",
            credits_spent=cost,
            success=True,
            latency_ms=int((time.time() - t0) * 1000),
            project_id=project_id,
        )

    return True, None


# ============================================================
# Helper: upload manuale
# ============================================================


def _upload_reference_image(
    project_id: uuid.UUID, char_id: uuid.UUID, file_bytes: bytes, mime_type: str
) -> tuple[bool, str | None]:
    """Carica direttamente un'immagine caricata dall'utente."""
    if len(file_bytes) > 5 * 1024 * 1024:
        return False, "File troppo grande (max 5 MB)."

    storage_key_path = reference_key(project_id, char_id, 1)
    try:
        upload_bytes(storage_key_path, file_bytes, content_type=mime_type)
    except Exception as e:
        return False, f"Errore upload: {e}"

    with session_scope() as s:
        project = projects_repo.get_by_id(s, project_id)
        cs = next((c for c in project.character_sheets if c.id == char_id), None) if project else None
        if cs is None:
            return False, "Personaggio non trovato."
        characters_repo.upsert_reference(
            s,
            cs,
            slot_number=1,
            storage_key=storage_key_path,
            mime_type=mime_type,
            file_size=len(file_bytes),
        )
    return True, None


# ============================================================
# Render: card singolo personaggio
# ============================================================


def _render_character_card(
    char_dict: dict,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    style_id: str | None,
    user_credits_left: int,
) -> None:
    char_id = char_dict["id"]
    char_name = char_dict["name"]
    visual_description = char_dict["visual_description"]
    ref_storage_key = char_dict.get("ref_storage_key")

    has_ref = ref_storage_key and object_exists(ref_storage_key)
    status_emoji = "🟢" if has_ref else "⚪"

    with st.expander(f"{status_emoji}  **{char_name}**", expanded=not has_ref):
        col_img, col_form = st.columns([1, 2])

        with col_img:
            if has_ref:
                try:
                    image_data = download_bytes(ref_storage_key)
                    st.image(image_data, caption=f"Slot 1", use_container_width=True)
                except Exception:
                    st.warning("Errore lettura immagine. Rigenera o ricarica.")
            else:
                st.markdown(
                    """
                    <div style="background:#161B26;border:1.5px dashed #2D3748;
                                border-radius:8px;padding:3rem 1rem;text-align:center;
                                color:#475569;">
                      <div style="font-size:2rem;">📸</div>
                      <div style="margin-top:0.5rem;">Nessuna reference</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_form:
            # Edit nome + descrizione dentro form (bottone salva sempre attivo)
            with st.form(f"_edit_char_form_{char_id}", border=False):
                new_name = st.text_input(
                    "Nome",
                    value=char_name,
                )
                new_desc = st.text_area(
                    "Descrizione visiva",
                    value=visual_description,
                    placeholder="Es. uomo sui 40, barba grigia corta, occhi nocciola, giacca di pelle marrone consumata",
                    height=120,
                )
                save_submitted = st.form_submit_button(
                    "💾 Salva modifiche",
                    type="secondary",
                    use_container_width=True,
                )
                if save_submitted:
                    changed = (new_name != char_name) or (new_desc != visual_description)
                    if changed:
                        try:
                            with session_scope() as s:
                                project = projects_repo.get_by_id(s, project_id)
                                cs = next((c for c in project.character_sheets if c.id == char_id), None) if project else None
                                if cs is not None:
                                    if new_name != char_name:
                                        characters_repo.rename_character(s, cs, new_name)
                                    characters_repo.update_character(s, cs, visual_description=new_desc)
                            st.toast("Personaggio salvato.", icon="✅")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                    else:
                        st.info("Nessuna modifica da salvare.")

            # Variabili usate sotto (genera/rigenera prendono i valori salvati DB)
            new_desc = new_desc if save_submitted else visual_description
            new_name = new_name if save_submitted else char_name

            st.markdown("---")
            cost = cost_for_operation("generate_reference")
            st.caption(f"Costa **{cost} credito** per generare/rigenerare la reference.")

            col_gen, col_upload, col_delete = st.columns([2, 2, 1])
            with col_gen:
                btn_label = "🔄 Rigenera" if has_ref else "✨ Genera con AI"
                gen_disabled = (
                    not new_desc.strip()
                    or user_credits_left < cost
                )
                gen_help = None
                if not new_desc.strip():
                    gen_help = "Aggiungi prima una descrizione visiva."
                elif user_credits_left < cost:
                    gen_help = f"Crediti insufficienti (servono {cost})."

                if st.button(
                    btn_label,
                    key=f"gen_{char_id}",
                    type="primary",
                    disabled=gen_disabled,
                    help=gen_help,
                    use_container_width=True,
                ):
                    with st.spinner(f"Genero reference di {new_name}..."):
                        success, err = _generate_reference_image(
                            user_id=user_id,
                            project_id=project_id,
                            char_id=char_id,
                            char_name=new_name,
                            visual_description=new_desc,
                            style_id=style_id,
                        )
                    if success:
                        st.toast(f"Reference di {new_name} generata.", icon="✨")
                        st.rerun()
                    else:
                        st.error(err)

            with col_upload:
                uploaded = st.file_uploader(
                    "📤 Carica file",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"upload_{char_id}",
                    label_visibility="collapsed",
                )
                if uploaded is not None:
                    success, err = _upload_reference_image(
                        project_id=project_id,
                        char_id=char_id,
                        file_bytes=uploaded.read(),
                        mime_type=uploaded.type,
                    )
                    if success:
                        st.toast(f"Reference caricata.", icon="📤")
                        st.rerun()
                    else:
                        st.error(err)

            with col_delete:
                if st.button(
                    "🗑",
                    key=f"del_{char_id}",
                    use_container_width=True,
                    help="Elimina questo personaggio",
                ):
                    st.session_state[f"_confirm_del_char_{char_id}"] = True
                    st.rerun()

            # Conferma elimina
            if st.session_state.get(f"_confirm_del_char_{char_id}"):
                st.warning(f"Eliminare **{char_name}**? L'azione è irreversibile.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Sì, elimina", key=f"_yes_del_{char_id}", type="primary"):
                        with session_scope() as s:
                            project = projects_repo.get_by_id(s, project_id)
                            cs = next((c for c in project.character_sheets if c.id == char_id), None) if project else None
                            if cs is not None:
                                # Cleanup storage
                                if ref_storage_key:
                                    try:
                                        delete_object(ref_storage_key)
                                    except Exception:
                                        pass
                                characters_repo.delete_character(s, cs)
                        st.session_state.pop(f"_confirm_del_char_{char_id}", None)
                        st.toast("Personaggio eliminato.")
                        st.rerun()
                with col_no:
                    if st.button("Annulla", key=f"_no_del_{char_id}"):
                        st.session_state.pop(f"_confirm_del_char_{char_id}", None)
                        st.rerun()


# ============================================================
# Lookup project + cast
# ============================================================


def _load_cast_view(user_id, project_slug: str) -> tuple[dict | None, list[dict]]:
    with session_scope() as s:
        project = projects_repo.get_by_slug(s, user_id, project_slug)
        if project is None:
            return None, []
        project_view = {
            "id": project.id,
            "name": project.name,
            "style_id": project.style_id,
        }
        cast_view = []
        for cs in project.character_sheets:
            ref = next((r for r in cs.references if r.slot_number == 1), None)
            cast_view.append({
                "id": cs.id,
                "name": cs.name,
                "visual_description": cs.visual_description,
                "color_palette": cs.color_palette,
                "ref_storage_key": ref.storage_key if ref else None,
            })
        return project_view, cast_view


# ============================================================
# RENDER
# ============================================================

_project_view, _cast_view = _load_cast_view(_user.id, _current_slug)
if _project_view is None:
    appstate.clear_current_project()
    st.error("Il progetto attivo non esiste più.")
    st.markdown("[← Vai alla home](/)")
    st.stop()


_plan_cfg = plan_config(_user.plan)
_render_sidebar(
    _user,
    project_name=_project_view["name"],
    plan_label=_plan_cfg.label,
    credits_left=_user.credits_remaining,
    credits_total=_user.credits_total_this_period,
)

st.title("👥 Personaggi")
st.caption(f"Progetto: **{_project_view['name']}**")

# Stato globale + bulk
n_total = len(_cast_view)
n_with_ref = sum(
    1 for c in _cast_view
    if c.get("ref_storage_key") and object_exists(c["ref_storage_key"])
)
n_missing = n_total - n_with_ref

if n_total > 0:
    st.markdown(f"**Reference:** {n_with_ref}/{n_total} personaggi hanno un'immagine di riferimento")
    st.progress(n_with_ref / n_total if n_total else 0)

    if n_missing > 0:
        cost_bulk = n_missing * cost_for_operation("generate_reference")
        can_bulk = _user.credits_remaining >= cost_bulk
        col_bulk_btn, col_bulk_caption = st.columns([1, 3])
        with col_bulk_btn:
            if st.button(
                f"🚀 Genera reference mancanti ({n_missing})",
                type="primary",
                disabled=not can_bulk,
                help=(
                    None if can_bulk
                    else f"Servono {cost_bulk} crediti, ne hai {_user.credits_remaining}."
                ),
            ):
                progress = st.progress(0)
                status = st.empty()
                errors = []
                missing = [c for c in _cast_view if not c.get("ref_storage_key")]
                for i, ch in enumerate(missing, start=1):
                    status.write(f"⏳ {ch['name']}...")
                    success, err = _generate_reference_image(
                        user_id=_user.id,
                        project_id=_project_view["id"],
                        char_id=ch["id"],
                        char_name=ch["name"],
                        visual_description=ch["visual_description"],
                        style_id=_project_view["style_id"],
                    )
                    if not success:
                        errors.append(f"{ch['name']}: {err}")
                    progress.progress(i / len(missing))
                status.write(f"✅ Generate {len(missing) - len(errors)}/{len(missing)} reference.")
                if errors:
                    for err in errors:
                        st.error(err)
                st.rerun()
        with col_bulk_caption:
            st.caption(f"Costo: {cost_bulk} crediti totali (1 per personaggio).")

st.markdown("---")

# ============================================================
# Lista personaggi
# ============================================================

if not _cast_view:
    st.info(
        "Nessun personaggio nel progetto. "
        "Vai su **📝 Testo** e adatta una sceneggiatura per popolare automaticamente il cast, "
        "oppure aggiungi un personaggio manualmente in fondo a questa pagina."
    )
else:
    for ch in _cast_view:
        _render_character_card(
            char_dict=ch,
            project_id=_project_view["id"],
            user_id=_user.id,
            style_id=_project_view["style_id"],
            user_credits_left=_user.credits_remaining,
        )

st.markdown("---")

# ============================================================
# 📚 Archivio personale del cast
# ============================================================

with st.expander("📚 Archivio personale del cast (riusabile tra progetti)", expanded=False):
    st.caption(
        "Salva i tuoi personaggi nell'archivio per riutilizzarli in altri progetti. "
        "La reference image NON viene archiviata (è specifica del progetto e dello stile)."
    )

    with session_scope() as _s:
        _archive = cast_archive_repo.list_for_user(_s, _user)
        _archive_view = [
            {"id": e.id, "name": e.name, "visual_description": e.visual_description,
             "color_palette": e.color_palette, "notes": e.notes}
            for e in _archive
        ]

    # Importa archivio → cast progetto
    if _archive_view:
        st.markdown(f"**Archivio attuale: {len(_archive_view)} personaggi**")
        for entry in _archive_view:
            with st.container(border=True):
                col_info, col_imp, col_del = st.columns([4, 1, 1])
                with col_info:
                    st.markdown(f"**{entry['name']}**")
                    st.caption(entry["visual_description"][:200] + ("…" if len(entry["visual_description"]) > 200 else ""))
                with col_imp:
                    # Check se già nel progetto
                    already = any(c["name"].lower() == entry["name"].lower() for c in _cast_view)
                    if st.button(
                        "📥 Importa",
                        key=f"_arc_imp_{entry['id']}",
                        disabled=already,
                        help="Già nel cast di questo progetto." if already else None,
                        use_container_width=True,
                    ):
                        try:
                            with session_scope() as s:
                                project = projects_repo.get_by_id(s, _project_view["id"])
                                if project is not None:
                                    characters_repo.create_character(
                                        s, project=project,
                                        name=entry["name"],
                                        visual_description=entry["visual_description"],
                                        color_palette=entry["color_palette"],
                                    )
                            st.toast(f"«{entry['name']}» importato nel progetto.", icon="📥")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                with col_del:
                    if st.button(
                        "🗑",
                        key=f"_arc_del_{entry['id']}",
                        use_container_width=True,
                        help="Rimuovi dall'archivio (NON rimuove dal progetto attuale)",
                    ):
                        with session_scope() as s:
                            arc_entry = next(
                                (e for e in cast_archive_repo.list_for_user(s, _user)
                                 if e.id == entry["id"]), None
                            )
                            if arc_entry is not None:
                                cast_archive_repo.delete(s, arc_entry)
                        st.toast("Rimosso dall'archivio.")
                        st.rerun()
    else:
        st.caption("_L'archivio è vuoto. Salva qualche personaggio dal cast di questo progetto._")

    # Salva cast progetto → archivio
    st.markdown("---")
    st.markdown("**Salva un personaggio del progetto nell'archivio**")
    if _cast_view:
        savable = [c for c in _cast_view if not any(
            a["name"].lower() == c["name"].lower() for a in _archive_view
        )]
        if savable:
            options = [c["name"] for c in savable]
            sel = st.selectbox("Personaggio da archiviare", options=options, key="_arc_save_sel")
            if st.button("💾 Salva nell'archivio", key="_arc_save_btn", type="secondary"):
                chosen = next(c for c in savable if c["name"] == sel)
                try:
                    with session_scope() as s:
                        cast_archive_repo.upsert(
                            s, user=_user,
                            name=chosen["name"],
                            visual_description=chosen["visual_description"],
                            color_palette=chosen.get("color_palette", ""),
                        )
                    st.toast(f"«{chosen['name']}» salvato nell'archivio.", icon="📚")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        else:
            st.caption("_Tutti i personaggi del progetto sono già nell'archivio._")
    else:
        st.caption("_Aggiungi prima qualche personaggio al progetto._")

st.markdown("---")

# ============================================================
# Aggiungi personaggio manualmente
# ============================================================

with st.expander("➕ Aggiungi personaggio manualmente", expanded=False):
    with st.form("_add_character_form", clear_on_submit=True):
        new_char_name = st.text_input("Nome", placeholder="Es. Marco Riccio")
        new_char_desc = st.text_area(
            "Descrizione visiva",
            placeholder="Es. uomo sui 40, barba grigia corta, giacca di pelle marrone",
            height=100,
        )
        if st.form_submit_button("Aggiungi al cast", type="primary"):
            if not new_char_name.strip():
                st.error("Serve un nome.")
            else:
                try:
                    with session_scope() as s:
                        project = projects_repo.get_by_id(s, _project_view["id"])
                        if project is not None:
                            characters_repo.create_character(
                                s,
                                project=project,
                                name=new_char_name.strip(),
                                visual_description=new_char_desc.strip(),
                            )
                    st.toast(f"Personaggio «{new_char_name}» aggiunto al cast.", icon="✨")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
