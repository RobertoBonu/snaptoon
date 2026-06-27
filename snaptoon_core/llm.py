"""Client Claude condiviso.

L'SDK risolve le credenziali in quest'ordine (automaticamente):
  1. ANTHROPIC_API_KEY env var
  2. ANTHROPIC_AUTH_TOKEN env var
  3. Profilo di `ant auth login` (cartella ~/.config/anthropic/)
"""

from __future__ import annotations

import os
from functools import lru_cache

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv("CREATIVE_STUDIO_MODEL", "claude-opus-4-8")


@lru_cache(maxsize=1)
def client() -> Anthropic:
    return Anthropic()
