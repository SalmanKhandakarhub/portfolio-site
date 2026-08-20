"""Email sending.

Two messages go out per enquiry:

  1. Notification  -> your inbox, with Reply-To set to the visitor, so
                      hitting reply in your mail client answers them directly.
  2. Acknowledgement -> the visitor, confirming you received it.

Both are sent from a background task. The HTTP response does not wait on
SMTP, because a slow mail server should never become a slow form.
"""

import logging
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import settings

log = logging.getLogger("contact.mailer")

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(["html"]),  # visitor input is escaped, not injected
)


async def _send(
    *,
    to: str,
    subject: str,
    html: str,
    text: str,
    reply_to: str | None = None,
) -> None:
    """Build and deliver one message. Raises on failure so the caller can log it."""
    msg = EmailMessage()
    msg["From"] = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    # Plain text first, HTML as the alternative. Clients that block HTML
    # still get a readable message.
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=int(settings.SMTP_PORT),
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=True, 
        start_tls=False,
        timeout=20,
    )


async def send_enquiry_emails(
    *, name: str, email: str, kind: str, message: str, ip: str
) -> None:
    """Send both emails. Called as a background task, so it must never raise
    into the request cycle — failures are logged with full context instead."""

    ctx = {
        "name": name,
        "email": email,
        "kind": kind,
        "message": message,
        "ip": ip,
        "site_name": settings.SITE_NAME,
        "site_url": settings.SITE_URL,
        "from_name": settings.FROM_NAME,
    }

    # --- 1. to you ----------------------------------------------------
    try:
        await _send(
            to=settings.INBOX_EMAIL,
            subject=f"New enquiry — {kind} — {name}",
            html=_env.get_template("notification.html").render(**ctx),
            text=(
                f"New enquiry via {settings.SITE_NAME}\n\n"
                f"Name:  {name}\n"
                f"Email: {email}\n"
                f"Needs: {kind}\n"
                f"IP:    {ip}\n\n"
                f"{message}\n"
            ),
            reply_to=email,  # reply goes straight to the visitor
        )
        log.info("notification sent for enquiry from %s", email)
    except Exception:
        # This one matters most — if it fails you never learn about the lead.
        log.error("FAILED to send notification for %s", email, exc_info=True)

    # --- 2. to the visitor --------------------------------------------
    try:
        await _send(
            to=email,
            subject=f"Thanks — I've got your message, {name.split()[0]}",
            html=_env.get_template("acknowledgement.html").render(**ctx),
            text=(
                f"Hi {name.split()[0]},\n\n"
                f"Thanks for getting in touch. Your message reached me and "
                f"I'll reply within one working day.\n\n"
                f"Here's what you sent, for your records:\n\n"
                f"Topic: {kind}\n\n"
                f"{message}\n\n"
                f"— {settings.FROM_NAME}\n{settings.SITE_URL}\n"
            ),
            reply_to=settings.INBOX_EMAIL,
        )
        log.info("acknowledgement sent to %s", email)
    except Exception:
        # Less critical: you still have the enquiry, they just did not get
        # a confirmation. Worth logging, not worth failing over.
        log.warning("failed to send acknowledgement to %s", email, exc_info=True)
