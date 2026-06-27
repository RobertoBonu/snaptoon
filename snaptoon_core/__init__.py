"""SnapToon Core — logica di dominio del prodotto.

Package Python PURO: nessuna dipendenza da Streamlit, nessun I/O su file
system o database. Tutta la persistenza vive nei layer esterni:
- db/ (SQLAlchemy + Alembic)
- storage/ (Replit Object Storage)

Cosa contiene:
- models: Pydantic models del dominio (Script, Page, Panel, Dialogue,
  Character, CharacterSheet, PageLayout, Cover, TextBox, ProjectMeta)
- styles_library: parser dei 98 preset di stile (.md)
- styles: Pydantic Style + costruzione prompt per vignetta/copertina
- scene: opzioni di regia (aspect_ratio, shot_distance, shot_angle, mood)
- generator: wrapper OpenAI / Gemini per generazione immagini
- layout: rendering PIL pagine fumetto (gabbie, balloon, copertina)
- cast: modelli archivio cast globale
- script: adattamento testo → sceneggiatura via Claude
- soggetto: workflow Claude per scrittura soggetto guidata
- llm: client Anthropic lazy + modello default
"""

from __future__ import annotations

__version__ = "0.1.0"
