"""Helper piccolo per il nome pubblico dell'utente sulle card Esplora."""


def public_author_name(user) -> str:
    """Ritorna il nome mostrato al posto dell'email nelle card Esplora.

    Priorità: pseudonym se non vuoto → altrimenti prefisso email.
    """
    if user is None:
        return ""
    pseud = (getattr(user, "pseudonym", "") or "").strip()
    if pseud:
        return pseud
    email = (getattr(user, "email", "") or "")
    if "@" in email:
        return email.split("@")[0]
    return email
