"""Repository pattern per accesso DB tipizzato.

Ogni modulo espone funzioni stateless che prendono `Session` come primo
argomento. Niente classi, niente ORM-magic: query esplicite, leggibili.

Convenzione di naming:
- get_*       → ritorna 1 elemento (o None)
- list_*      → ritorna list
- create_*    → INSERT
- update_*    → UPDATE specifico
- delete_*    → DELETE (soft o hard a seconda del modello)
- find_*      → ricerca con filtri
"""

from __future__ import annotations
