from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from ..core.settings import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Simple SMTP email sender for auth flows."""

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send a password reset email if SMTP settings are configured."""
        settings = get_settings()
        if (
            not settings.smtp_host
            or not settings.smtp_from_email
            or not settings.password_reset_url
        ):
            logger.warning(
                "SMTP settings are incomplete; skipping password reset email to %s",
                to_email,
            )
            return False

        separator = "&" if "?" in settings.password_reset_url else "?"
        reset_link = f"{settings.password_reset_url}{separator}token={reset_token}"
        app_name = settings.app_name or "LabGuard"

        message = EmailMessage()
        message["Subject"] = f"{app_name}: Reset your password"
        message["From"] = settings.smtp_from_email
        message["To"] = to_email
        message.set_content(
            """You requested a password reset for your account.

Open this link to reset your password:
{link}

This link expires in 30 minutes and can be used only once.

If you did not request this, you can safely ignore this email.
""".format(
                link=reset_link
            )
        )
        message.add_alternative(
            """<html>
  <body style="font-family: Arial, sans-serif; color: #111827; line-height: 1.5;">
    <p>You requested a password reset for your account.</p>
    <p>
      <a href="{link}" style="display: inline-block; padding: 10px 16px; background: #111827; color: #ffffff; text-decoration: none; border-radius: 6px;">
        Reset Password
      </a>
    </p>
    <p>This link expires in 30 minutes and can be used only once.</p>
    <p>If you did not request this, you can safely ignore this email.</p>
  </body>
</html>
""".format(
                link=reset_link
            ),
            subtype="html",
        )

        def _send() -> None:
            with smtplib.SMTP(
                settings.smtp_host, settings.smtp_port, timeout=10
            ) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)

        try:
            _send()
            return True
        except Exception:
            logger.exception("Failed to send password reset email to %s", to_email)
            return False
