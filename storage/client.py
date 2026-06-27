"""Wrapper Replit Object Storage.

Su Replit, l'SDK `replit-object-storage` espone un Client che parla con
il bucket configurato nel Repl (via env REPLIT_OBJECT_STORAGE_BUCKET).

In locale (dev senza Replit), si usa una fallback su filesystem
in storage_cache/ (gitignored). Stesso contratto.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Protocol


# ============================================================
# Interfaccia comune
# ============================================================


class _StorageBackend(Protocol):
    def upload_bytes(self, key: str, data: bytes, *, content_type: str) -> None: ...
    def download_bytes(self, key: str) -> bytes: ...
    def object_exists(self, key: str) -> bool: ...
    def delete_object(self, key: str) -> None: ...


# ============================================================
# Replit backend
# ============================================================


class _ReplitBackend:
    """Wrapper Replit Object Storage SDK."""

    def __init__(self) -> None:
        try:
            from replit.object_storage import Client as ReplitClient
        except ImportError as e:
            raise RuntimeError(
                "replit-object-storage non installato. Aggiungilo a requirements.txt."
            ) from e
        bucket = os.getenv("REPLIT_OBJECT_STORAGE_BUCKET")
        self._client = ReplitClient(bucket_id=bucket) if bucket else ReplitClient()

    def upload_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        self._client.upload_from_bytes(key, data)

    def download_bytes(self, key: str) -> bytes:
        return self._client.download_as_bytes(key)

    def object_exists(self, key: str) -> bool:
        try:
            self._client.download_as_bytes(key)
            return True
        except Exception:
            return False

    def delete_object(self, key: str) -> None:
        try:
            self._client.delete(key)
        except Exception:
            pass


# ============================================================
# Local fallback (dev)
# ============================================================


class _LocalBackend:
    """Fallback su filesystem per sviluppo locale. Path radice: storage_cache/."""

    def __init__(self) -> None:
        self.root = Path("storage_cache")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key

    def upload_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(p)  # atomic

    def download_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def object_exists(self, key: str) -> bool:
        return self._path(key).exists()

    def delete_object(self, key: str) -> None:
        try:
            self._path(key).unlink()
        except FileNotFoundError:
            pass


# ============================================================
# Singleton + API pubblica
# ============================================================


@lru_cache(maxsize=1)
def storage_client() -> _StorageBackend:
    """Restituisce il backend configurato. Singleton.

    - Su Replit (env REPLIT detection): Replit Object Storage
    - In locale: filesystem fallback in storage_cache/
    """
    if os.getenv("REPL_ID") or os.getenv("REPLIT_OBJECT_STORAGE_BUCKET"):
        return _ReplitBackend()
    return _LocalBackend()


def upload_bytes(key: str, data: bytes, *, content_type: str = "image/png") -> None:
    storage_client().upload_bytes(key, data, content_type=content_type)


def download_bytes(key: str) -> bytes:
    return storage_client().download_bytes(key)


def object_exists(key: str) -> bool:
    return storage_client().object_exists(key)


def delete_object(key: str) -> None:
    storage_client().delete_object(key)
