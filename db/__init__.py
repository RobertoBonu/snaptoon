"""SnapToon — layer persistenza.

DB managed di Replit (PostgreSQL).
SQLAlchemy 2.0 + Alembic per migrazioni.

Architettura:
- base.py: Base declarative + tipi comuni (UUID, timestamps)
- models.py: tutte le 12 tabelle
- session.py: engine + session factory + helper context
- repos/: un repository per aggregato (CRUD + query)
- migrations/: Alembic env + versions/
"""

from __future__ import annotations
