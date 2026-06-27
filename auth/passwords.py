"""Hash e verifica password con bcrypt."""

from __future__ import annotations

import bcrypt


# Costo bcrypt: 12 è bilanciamento sicurezza/velocità (default raccomandato).
BCRYPT_ROUNDS = 12

MIN_PASSWORD_LENGTH = 8


class PasswordTooShort(ValueError):
    pass


def hash_password(plain: str) -> str:
    """Genera hash bcrypt da password in chiaro."""
    if len(plain) < MIN_PASSWORD_LENGTH:
        raise PasswordTooShort(
            f"La password deve essere lunga almeno {MIN_PASSWORD_LENGTH} caratteri."
        )
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica password contro hash bcrypt salvato.

    Ritorna False (non solleva) se l'hash è malformato — protegge da
    attacchi via hash corrotti che farebbero crashare il login.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
