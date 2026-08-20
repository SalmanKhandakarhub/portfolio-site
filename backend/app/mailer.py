"""Email sending.

Two messages go out per enquiry:

  1. Notification  -> your inbox, with Reply-To set to the visitor, so
                      hitting reply in your mail client answers them directly.
  2. Acknowledgement -> the visitor, confirming you received it.

Both are sent from a background task over a single persistent SMTP connection.
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
    autoescape=select_autoescape(["html"]),
)


def _build_message(
    *,
    to: str,
    subject: str,
    html: str,
    text: str,
    reply_to: str | None = None,
) -> EmailMessage:
    """Build an email message object without sending it."""
    msg = EmailMessage()
    msg["From"] = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to

    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


async def send_enquiry_emails(
    *, name: str, email: str, kind: str, message: str, ip: str
) -> None:
    """Send both emails over a single SMTP connection."""

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

    # 1. Build message objects
    notification_msg = _build_message(
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
        reply_to=email,
    )

    acknowledgement_msg = _build_message(
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

    # 2. Connect once, login once, deliver both
    smtp_client = aiosmtplib.SMTP(
        hostname=settings.SMTP_HOST,
        port=int(settings.SMTP_PORT),
        use_tls=True,
        timeout=25,
    )

    try:
        await smtp_client.connect()
        await smtp_client.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        # Send admin notification
        try:
            await smtp_client.send_message(notification_msg)
            log.info("notification sent for enquiry from %s", email)
        except Exception:
            log.error("FAILED to send notification for %s", email, exc_info=True)

        # Send user acknowledgement immediately over the same socket
        try:
            await smtp_client.send_message(acknowledgement_msg)
            log.info("acknowledgement sent to %s", email)
        except Exception:
            log.warning("failed to send acknowledgement to %s", email, exc_info=True)

    except Exception:
        log.error("Failed to connect/authenticate to SMTP server", exc_info=True)
    finally:
        if smtp_client.is_connected:
            await smtp_client.quit()