"""SnapToon — pagina 📐 Impagina.

Per ogni pagina del progetto:
  - Carica la gabbia (PageLayout.grid_id) e le vignette generate
  - Renderizza la pagina con snaptoon_core.layout.render_page (vignette
    posizionate nelle celle della gabbia + balloon overlay)
  - Salva PNG in Object Storage

Bulk render. Export PDF multipagina via snaptoon_core.layout.export_pdf.

Tutte le operazioni di render/export sono LOCALI Python (no costo crediti AI).
"""

from __future__ import annotations

import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Impagina — SnapToon",
    page_icon="📐",
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
import uuid

import app_state as appstate
from auth import current_user, logout
from billing.plans import plan_config
from db.repos import page_layouts as page_layouts_repo
from db.repos import projects as projects_repo
from db.repos import scripts as scripts_repo
from db.repos import vignettes as vignettes_repo
from db.session import session_scope
from snaptoon_core.layout import GRIDS, export_pdf, render_page
from snaptoon_core.models import Panel, Script as PydScript
from storage.client import download_bytes, object_exists, upload_bytes
from storage.keys import cover_illustration_key, page_render_key, pdf_export_key, vignette_key
from appearance import to_balloon_config


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
    st.title("📐 Impagina")
    st.error("Nessun progetto attivo.")
    st.info("Apri un progetto dalla **home** o creane uno nuovo.")
    st.markdown("[← Vai alla home](/)")
    st.stop()


# ============================================================
# Sidebar
# ============================================================


def _render_sidebar(user, project_name: str, plan_label: str, credits_left: int, credits_total: int) -> None:
    with st.sidebar:
        st.markdown("**Progetto attivo:**")
        st.markdown(f"_{project_name}_")
        st.divider()
        if st.button("🚪 Esci", key="_sb_logout_imp", use_container_width=True):
            with session_scope() as s:
                logout(s)
            appstate.clear_session_keys()
            st.switch_page("app.py")


# ============================================================
# Helper: render singola pagina
# ============================================================


def _render_page_to_storage(
    project_id: uuid.UUID,
    page_number: int,
    panels: list[Panel],
    grid_id: str,
    show_balloons: bool = True,
    appearance: dict | None = None,
) -> tuple[bool, str | None]:
    """Render della pagina con vignette + balloon overlay.

    1. Scarica vignette PNG da Object Storage in temp files
    2. Chiama snaptoon_core.layout.render_page
    3. Upload risultato in Object Storage
    4. Cleanup temp files

    Returns (success, error_msg).
    """
    grid = GRIDS.get(grid_id)
    if grid is None:
        return False, f"Gabbia '{grid_id}' non riconosciuta."

    # Raccogli paths a vignette (scarica da OS in temp se esistono)
    panel_paths: list[tuple[Panel, Path | None]] = []
    temp_files: list[Path] = []

    try:
        for panel in panels:
            vk = vignette_key(project_id, page_number, panel.number)
            if object_exists(vk):
                try:
                    data = download_bytes(vk)
                    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp.write(data)
                    tmp.close()
                    p = Path(tmp.name)
                    temp_files.append(p)
                    panel_paths.append((panel, p))
                except Exception:
                    panel_paths.append((panel, None))
            else:
                panel_paths.append((panel, None))

        # Render in temp file
        out_tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        out_tmp.close()
        out_path = Path(out_tmp.name)
        temp_files.append(out_path)

        cfg = to_balloon_config(appearance)
        render_page(
            panels_with_images=panel_paths,
            grid=grid,
            out_path=out_path,
            show_balloons=show_balloons,
            page_label="",
            cfg=cfg,
        )

        # Upload finale
        result_bytes = out_path.read_bytes()
        storage_key_path = page_render_key(project_id, page_number)
        upload_bytes(storage_key_path, result_bytes, content_type="image/png")

    except Exception as e:
        return False, f"Errore render: {e}"
    finally:
        for tmp_path in temp_files:
            try:
                tmp_path.unlink()
            except (FileNotFoundError, OSError):
                pass

    return True, None


# ============================================================
# Helper: export PDF
# ============================================================


def _generate_copyright_page(copyright_text: str, appearance: dict | None) -> Path:
    """Genera una semplice pagina copyright come PNG temp."""
    from PIL import Image, ImageDraw, ImageFont
    from snaptoon_core.layout import PAGE_W, PAGE_H, RENDER_SCALE

    cfg = to_balloon_config(appearance)
    s = RENDER_SCALE
    w, h = PAGE_W * s, PAGE_H * s

    img = Image.new("RGB", (w, h), cfg.page_bg)
    draw = ImageDraw.Draw(img)

    # Font generico (system fallback)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 32 * s)
    except Exception:
        font = ImageFont.load_default()

    # Layout: testo centrato verticalmente, padding laterale
    pad = 100 * s
    text_color = cfg.balloon_text_color if cfg.page_bg in ("#ffffff", "#fff") else cfg.caption_text_color
    lines = copyright_text.strip().split("\n")
    line_h = 50 * s
    total_h = line_h * len(lines)
    y = (h - total_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (w - line_w) // 2
        draw.text((x, y), line, fill=text_color, font=font)
        y += line_h

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    p = Path(tmp.name)
    img.save(p, "PNG")
    return p


def _export_project_pdf(
    project_id: uuid.UUID,
    page_numbers: list[int],
    copyright_text: str | None = None,
    appearance: dict | None = None,
    include_cover: bool = True,
) -> tuple[bytes | None, str | None]:
    """Esporta un PDF multipagina dalle pagine già renderizzate.

    Se include_cover e la cover illustration esiste, viene messa in cima.
    Se copyright_text presente, accoda una pagina copyright alla fine.

    Returns (pdf_bytes, error_msg) — bytes None se errore.
    """
    if not page_numbers:
        return None, "Nessuna pagina renderizzata da esportare."

    temp_files: list[Path] = []
    try:
        page_temp_paths: list[Path] = []

        # Copertina come prima pagina (se presente)
        if include_cover:
            cv_key = cover_illustration_key(project_id)
            if object_exists(cv_key):
                data = download_bytes(cv_key)
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp.write(data)
                tmp.close()
                p = Path(tmp.name)
                temp_files.append(p)
                page_temp_paths.append(p)

        # Scarica tutte le pagine renderizzate
        for pn in page_numbers:
            sk = page_render_key(project_id, pn)
            if not object_exists(sk):
                continue
            data = download_bytes(sk)
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(data)
            tmp.close()
            p = Path(tmp.name)
            temp_files.append(p)
            page_temp_paths.append(p)

        if not page_temp_paths:
            return None, "Nessuna pagina renderizzata trovata."

        # Pagina copyright alla fine se richiesta
        if copyright_text and copyright_text.strip():
            cp_path = _generate_copyright_page(copyright_text, appearance)
            temp_files.append(cp_path)
            page_temp_paths.append(cp_path)

        # Esporta PDF in temp
        pdf_tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        pdf_tmp.close()
        pdf_path = Path(pdf_tmp.name)
        temp_files.append(pdf_path)

        export_pdf(page_temp_paths, pdf_path)

        pdf_bytes = pdf_path.read_bytes()

        # Upload anche in Object Storage per archivio
        ts = datetime.now(timezone.utc)
        archive_key = pdf_export_key(project_id, ts)
        upload_bytes(archive_key, pdf_bytes, content_type="application/pdf")

        return pdf_bytes, None

    except Exception as e:
        return None, f"Errore export PDF: {e}"
    finally:
        for tmp_path in temp_files:
            try:
                tmp_path.unlink()
            except (FileNotFoundError, OSError):
                pass


# ============================================================
# Lookup dati progetto
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
                "script": None,
                "grids_by_page": {},
                "vignette_count_by_page": {},
            }

        pyd_script = scripts_repo.load_pydantic(project.script)

        grids_by_page = {pl.page_number: pl.grid_id for pl in project.page_layouts}

        # Conteggio vignette per pagina
        vigs = vignettes_repo.list_for_project(s, project)
        vig_by_page: dict[int, int] = {}
        for v in vigs:
            vig_by_page[v.page_number] = vig_by_page.get(v.page_number, 0) + 1

        return {
            "id": project.id,
            "name": project.name,
            "script": pyd_script,
            "grids_by_page": grids_by_page,
            "vignette_count_by_page": vig_by_page,
            "appearance": project.appearance,
            "copyright_text": project.copyright_text or "",
        }


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

st.title("📐 Impagina")
st.caption(f"Progetto: **{_view['name']}**")

if _view["script"] is None:
    st.error("Nessuna sceneggiatura.")
    st.info("Vai su **📝 Testo** per crearne una prima.")
    st.stop()

pages = _view["script"].pages
if not pages:
    st.info("Nessuna pagina ancora.")
    st.stop()

# ============================================================
# Status globale + bulk
# ============================================================

n_pages_total = len(pages)
rendered_pages: list[int] = []
for page in pages:
    if object_exists(page_render_key(_view["id"], page.number)):
        rendered_pages.append(page.number)

n_rendered = len(rendered_pages)
n_missing = n_pages_total - n_rendered

st.markdown(f"### Stato: {n_rendered}/{n_pages_total} pagine renderizzate")
st.progress(n_rendered / n_pages_total if n_pages_total else 0)

col_bulk, col_pdf = st.columns(2)
with col_bulk:
    if st.button(
        f"🎨 Renderizza tutte le pagine ({n_pages_total})",
        type="primary",
        use_container_width=True,
        disabled=(n_pages_total == 0),
    ):
        progress = st.progress(0)
        status = st.empty()
        errors: list[str] = []
        for i, page in enumerate(pages, start=1):
            status.write(f"⏳ Rendering pagina {page.number}...")
            grid_id = _view["grids_by_page"].get(page.number, "2x2")
            success, err = _render_page_to_storage(
                project_id=_view["id"],
                page_number=page.number,
                panels=page.panels,
                grid_id=grid_id,
                show_balloons=True,
                appearance=_view["appearance"],
            )
            if not success:
                errors.append(f"Pagina {page.number}: {err}")
            progress.progress(i / n_pages_total)
        status.write(f"✅ Renderizzate {n_pages_total - len(errors)}/{n_pages_total} pagine.")
        if errors:
            for e in errors:
                st.error(e)
        st.rerun()

with col_pdf:
    can_export = n_rendered > 0
    if st.button(
        f"📥 Esporta PDF ({n_rendered} pagine)",
        type="primary",
        use_container_width=True,
        disabled=not can_export,
        help=None if can_export else "Renderizza almeno una pagina prima di esportare.",
    ):
        with st.spinner("Creazione PDF in corso..."):
            pdf_bytes, err = _export_project_pdf(
                _view["id"],
                rendered_pages,
                copyright_text=_view["copyright_text"],
                appearance=_view["appearance"],
            )
        if err:
            st.error(err)
        elif pdf_bytes:
            st.session_state["_pdf_bytes"] = pdf_bytes
            st.session_state["_pdf_filename"] = f"snaptoon_{_current_slug}.pdf"
            st.success("PDF pronto per il download qui sotto.")

# Download button (se PDF disponibile)
if "_pdf_bytes" in st.session_state:
    st.download_button(
        label="⬇️ Scarica PDF",
        data=st.session_state["_pdf_bytes"],
        file_name=st.session_state["_pdf_filename"],
        mime="application/pdf",
        type="primary",
        use_container_width=True,
        on_click=lambda: st.session_state.pop("_pdf_bytes", None),
    )

st.divider()

# ============================================================
# Pagina copyright (opzionale, accodata al PDF)
# ============================================================
with st.expander("📜 Pagina copyright (opzionale, ultima pagina del PDF)", expanded=False):
    with st.form("_form_copyright"):
        new_copy = st.text_area(
            "Testo copyright",
            value=_view["copyright_text"],
            height=150,
            placeholder="© 2026 Roberto Bonu. Tutti i diritti riservati.\nSnaptoon AI Edition.",
            help="Verrà generata come ultima pagina nel PDF esportato. Lasciare vuoto per ometterla.",
        )
        if st.form_submit_button("💾 Salva copyright", type="secondary"):
            with session_scope() as s:
                project = projects_repo.get_by_id(s, _view["id"])
                if project is not None:
                    project.copyright_text = new_copy or None
            st.toast("Copyright salvato.", icon="📜")
            st.rerun()

st.divider()

# ============================================================
# Lista pagine — preview render + bottoni
# ============================================================

for page in pages:
    grid_id = _view["grids_by_page"].get(page.number, "2x2")
    grid = GRIDS.get(grid_id)
    grid_label = grid.name if grid else grid_id
    n_pn = len(page.panels)
    n_vig_gen = _view["vignette_count_by_page"].get(page.number, 0)
    is_rendered = page.number in rendered_pages

    with st.expander(
        f"📖 Pagina {page.number} — {n_vig_gen}/{n_pn} vignette · gabbia: {grid_label}"
        + ("  ✅" if is_rendered else ""),
        expanded=True,
    ):
        col_preview, col_actions = st.columns([2, 1])

        with col_preview:
            if is_rendered:
                try:
                    sk = page_render_key(_view["id"], page.number)
                    data = download_bytes(sk)
                    st.image(data, use_container_width=True)
                except Exception:
                    st.warning("Errore lettura anteprima. Rigenera il render.")
            else:
                st.markdown(
                    """
                    <div style="background:#161B26;border:1.5px dashed #2D3748;
                                border-radius:8px;padding:4rem 1rem;text-align:center;
                                color:#475569;">
                      <div style="font-size:2rem;">📄</div>
                      <div style="margin-top:0.5rem;">Pagina non ancora renderizzata</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with col_actions:
            st.markdown(f"**Pagina {page.number}**")
            st.caption(f"{n_pn} vignette · {n_vig_gen} generate")
            st.caption(f"Gabbia: `{grid_id}`")

            if n_vig_gen < n_pn:
                st.warning(
                    f"⚠️ {n_pn - n_vig_gen} vignette ancora da generare. "
                    "Vai su 🖼 Genera per completarle, poi torna qui."
                )

            render_label = "🔄 Rigenera render" if is_rendered else "🎨 Renderizza pagina"
            if st.button(
                render_label,
                key=f"_render_p{page.number}",
                type="primary",
                use_container_width=True,
            ):
                with st.spinner(f"Rendering pagina {page.number}..."):
                    success, err = _render_page_to_storage(
                        project_id=_view["id"],
                        page_number=page.number,
                        panels=page.panels,
                        grid_id=grid_id,
                        show_balloons=True,
                    )
                if success:
                    st.toast(f"Pagina {page.number} renderizzata.", icon="📐")
                    st.rerun()
                else:
                    st.error(err)

            if is_rendered:
                try:
                    sk = page_render_key(_view["id"], page.number)
                    data = download_bytes(sk)
                    st.download_button(
                        "⬇️ Scarica PNG",
                        data=data,
                        file_name=f"snaptoon_{_current_slug}_p{page.number:02d}.png",
                        mime="image/png",
                        key=f"_dl_p{page.number}",
                        use_container_width=True,
                    )
                except Exception:
                    pass
