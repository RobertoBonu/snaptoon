"""Invio email transazionali via SMTP.

Configurazione (Replit Secrets):
    SMTP_HOST      es. smtp.gmail.com
    SMTP_PORT      es. 587
    SMTP_USER      es. no-reply@snaptoon.art
    SMTP_PASSWORD  es. app password del provider
    SMTP_FROM      es. "SnapToon <no-reply@snaptoon.art>"

Se SMTP_HOST non è impostato, l'email viene solo LOGGATA (dev/test),
senza sollevare eccezioni: l'app continua a funzionare anche senza SMTP.
"""
from __future__ import annotations

import logging
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid, parseaddr

logger = logging.getLogger(__name__)


def _smtp_config() -> dict[str, str] | None:
    host = os.getenv("SMTP_HOST", "").strip()
    if not host:
        return None
    return {
        "host": host,
        "port": os.getenv("SMTP_PORT", "587").strip(),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from_addr": os.getenv(
            "SMTP_FROM", "SnapToon <no-reply@snaptoon.art>"
        ).strip(),
    }


def send_email(
    *,
    to: str,
    subject: str,
    html: str,
    text: str | None = None,
) -> bool:
    """Invia una email. Ritorna True se inviata, False se fallita/loggata.

    Non solleva mai eccezioni: se SMTP fallisce, logga e ritorna False.
    """
    cfg = _smtp_config()

    if cfg is None:
        # Modalità dev/senza SMTP: logga contenuto
        logger.info(
            "[MAIL DRY-RUN] to=%s subject=%r\n--- HTML ---\n%s",
            to, subject, html,
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = cfg["from_addr"]
    msg["To"] = to
    msg["Subject"] = subject
    # Header standard richiesti dai filtri antispam: senza Date/Message-ID
    # alcuni provider (es. SMTP di dominio) rifiutano con "550 Spam Rejected".
    msg["Date"] = formatdate(localtime=True)
    _from_addr = parseaddr(cfg["from_addr"])[1]
    _from_domain = _from_addr.split("@")[-1] if "@" in _from_addr else None
    msg["Message-ID"] = make_msgid(domain=_from_domain)

    # Parte testo sempre presente (anti-spam): usa `text` se fornito,
    # altrimenti deriva un fallback testuale dall'HTML.
    if not text:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        port = int(cfg["port"])
        # Porta 465 = SSL implicito (SMTP_SSL); 587/25 = STARTTLS su SMTP.
        if port == 465:
            server = smtplib.SMTP_SSL(cfg["host"], port, timeout=15)
        else:
            server = smtplib.SMTP(cfg["host"], port, timeout=15)
        with server:
            server.ehlo()
            if port != 465:
                server.starttls()
                server.ehlo()
            if cfg["user"] and cfg["password"]:
                server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["from_addr"], [to], msg.as_string())
        logger.info("Email inviata a %s (subject=%r)", to, subject)
        return True
    except Exception as e:
        logger.error("Errore invio email a %s: %s", to, e)
        return False


# ============================================================
# Templates
# ============================================================


def _wrap_html(body_html: str) -> str:
    return f"""
<html><body style="font-family:sans-serif;max-width:560px;margin:auto;padding:24px;color:#0D1017">
  <div style="text-align:center;margin-bottom:24px">
    <span style="font-size:32px;font-weight:800;color:#F59E0B">SnapToon</span>
  </div>
  {body_html}
  <hr style="border:none;border-top:1px solid #eee;margin:32px 0">
  <p style="font-size:12px;color:#888;text-align:center">
    Hai ricevuto questa email perché ti sei iscritto a SnapToon.<br>
    Se non l'hai richiesta, ignora questo messaggio.
  </p>
</body></html>
"""


def _public_base_url() -> str:
    """URL base pubblico per costruire link nelle email.

    Priorità:
    1. Env var PUBLIC_BASE_URL (es. https://snaptoon.art)
    2. Env var REPLIT_DEV_DOMAIN (es. xxx-yyy.replit.dev)
    3. Fallback dev locale
    """
    url = os.getenv("PUBLIC_BASE_URL", "").strip()
    if url:
        return url.rstrip("/")
    replit_domain = os.getenv("REPLIT_DEV_DOMAIN", "").strip()
    if replit_domain:
        return f"https://{replit_domain}"
    return "https://snaptoon.art"


def send_email_verification(email: str, token: str, display_name: str = "") -> bool:
    """Prima email: chiede di cliccare il link per verificare l'indirizzo."""
    verify_url = f"{_public_base_url()}/verify?token={token}"
    greeting = f"Ciao {display_name}," if display_name.strip() else "Ciao,"
    body = f"""
<p>{greeting}</p>
<h2>Conferma il tuo indirizzo email</h2>
<p>Grazie per esserti iscritto a SnapToon! Per completare la
registrazione clicca sul pulsante qui sotto:</p>
<p style="text-align:center;margin:32px 0">
  <a href="{verify_url}" style="background:#F59E0B;color:#0D1017;
     padding:14px 32px;text-decoration:none;border-radius:8px;font-weight:700;
     display:inline-block">
    Verifica la mia email →
  </a>
</p>
<p>Oppure copia questo link nel browser:<br>
<a href="{verify_url}" style="color:#F59E0B;word-break:break-all">{verify_url}</a></p>
<p style="color:#888;font-size:13px">Se non hai richiesto questa registrazione,
ignora questo messaggio: il tuo indirizzo non verrà attivato.</p>
"""
    return send_email(
        to=email,
        subject="Conferma il tuo indirizzo email — SnapToon",
        html=_wrap_html(body),
    )


def send_welcome_after_verification(
    email: str,
    first_name: str,
    last_name: str,
    pseudonym: str,
    plan_label: str,
) -> bool:
    """Seconda email: benvenuto post-verifica.

    "Ciao [nome cognome] + [pseudonimo] - Ora sei dei nostri!"
    """
    name_full = f"{first_name} {last_name}".strip()
    if pseudonym.strip() and name_full:
        greeting = f"Ciao {name_full} · {pseudonym}"
    elif name_full:
        greeting = f"Ciao {name_full}"
    elif pseudonym.strip():
        greeting = f"Ciao {pseudonym}"
    else:
        greeting = "Ciao"

    body = f"""
<h2>{greeting},<br>ora sei dei nostri! 🎉</h2>
<p>Il tuo account <b>{plan_label}</b> è attivo!!!</p>
<p style="text-align:center;margin:32px 0">
  <a href="{_public_base_url()}/app" style="background:#F59E0B;color:#0D1017;
     padding:12px 28px;text-decoration:none;border-radius:8px;font-weight:700">
    Entra in SnapToon →
  </a>
</p>
<p>Buon divertimento con SnapToon! Racconta una scintilla e guarda
l'AI trasformarla in un fumetto illustrato.</p>
<p><b>...e non dimenticare di darci un tuo feedback!</b> Rispondi
direttamente a questa email o scrivi a
<a href="mailto:info@snaptoon.art">info@snaptoon.art</a>.
Le prime settimane sono cruciali per capire cosa migliorare.</p>
"""
    return send_email(
        to=email,
        subject=f"Ora sei dei nostri! Account {plan_label} attivo — SnapToon",
        html=_wrap_html(body),
    )


def send_registration_confirmation(email: str, plan_label: str) -> bool:
    """LEGACY (mantenuta): email ricevuta ma non verifica.
    Usa send_email_verification per il nuovo flusso."""
    body = f"""
<h2>Grazie per esserti iscritto a SnapToon!</h2>
<p>Abbiamo ricevuto la tua richiesta di attivazione del piano <b>{plan_label}</b>.</p>
<p>Il nostro team la esaminerà a breve e ti manderemo un'altra email
quando il tuo abbonamento sarà attivo.</p>
<p>Nel frattempo puoi già accedere e configurare il profilo.</p>
"""
    return send_email(
        to=email,
        subject="Registrazione SnapToon ricevuta",
        html=_wrap_html(body),
    )


def send_subscription_activated(email: str, plan_label: str) -> bool:
    """Email inviata quando l'admin approva l'abbonamento."""
    body = f"""
<h2>Abbonamento Attivo — Prova SnapToon</h2>
<p>Il tuo piano <b>{plan_label}</b> è ora attivo!</p>
<p>Puoi già iniziare a creare fumetti, figurine e copertine con l'AI.</p>
<p style="text-align:center;margin:32px 0">
  <a href="https://snaptoon.art/app" style="background:#F59E0B;color:#0D1017;
     padding:12px 28px;text-decoration:none;border-radius:8px;font-weight:700">
    Entra in SnapToon →
  </a>
</p>
<p>Facci sapere come è andata — rispondi a questa email o scrivici a
<a href="mailto:info@snaptoon.art">info@snaptoon.art</a>.</p>
"""
    return send_email(
        to=email,
        subject="Abbonamento Attivo — Prova SnapToon",
        html=_wrap_html(body),
    )


def send_subscription_rejected(
    email: str, plan_label: str, reason: str
) -> bool:
    body = f"""
<h2>La tua richiesta non è stata approvata</h2>
<p>Ci dispiace: la richiesta di attivazione del piano <b>{plan_label}</b>
non è stata approvata.</p>
<p><b>Motivo:</b> {reason or 'non specificato'}</p>
<p>Se pensi si tratti di un errore, scrivici a
<a href="mailto:info@snaptoon.art">info@snaptoon.art</a>.</p>
"""
    return send_email(
        to=email,
        subject="Richiesta abbonamento SnapToon",
        html=_wrap_html(body),
    )
