"""Email service — placeholder implementation.

Currently logs to console. Replace with actual SMTP sending
once SMTP settings are configured in app/config.py.
"""

import logging

logger = logging.getLogger(__name__)


async def send_notification_email(to_email: str, to_name: str, subject: str, body: str) -> bool:
    """Send a notification email. Currently a placeholder that logs the action."""
    logger.info(
        "[EMAIL PLACEHOLDER] To: %s <%s> | Subject: %s | Body: %s",
        to_name, to_email, subject, body[:100],
    )
    # TODO: implement actual SMTP sending using config.settings.SMTP_*
    return True
