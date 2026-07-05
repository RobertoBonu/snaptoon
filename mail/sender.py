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
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

    if text:
        msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        port = int(cfg["port"])
        with smtplib.SMTP(cfg["host"], port, timeout=15) as server:
            server.ehlo()
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


def send_registration_confirmation(email: str, plan_label: str) -> bool:
    """Email inviata immediatamente dopo la registrazione."""
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
