"""
Email Notifier

Sends notifications via SMTP email.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from .base import AbstractNotifier, Notification


logger = logging.getLogger(__name__)


class EmailNotifier(AbstractNotifier):
    """
    Email notifier using SMTP.

    Configuration example:
        {
            "enabled": true,
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "your_email@gmail.com",
            "smtp_password": "your_password",
            "from_email": "your_email@gmail.com",
            "to_emails": ["recipient@example.com"],
            "use_tls": true,
            "min_level": "WARNING"
        }
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize email notifier"""
        super().__init__("Email", config)

        self.smtp_host = config.get("smtp_host", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_user = config.get("smtp_user")
        self.smtp_password = config.get("smtp_password")
        self.from_email = config.get("from_email", self.smtp_user)
        self.to_emails = config.get("to_emails", [])
        self.use_tls = config.get("use_tls", True)

        if not self.to_emails:
            logger.warning("Email notifier configured but no recipients specified")

    async def send(self, notification: Notification) -> bool:
        """Send email notification"""
        if not self.to_emails:
            logger.warning("No email recipients configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{notification.level.value}] {notification.title}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)

            # Plain text version
            text_content = self._format_text(notification)
            text_part = MIMEText(text_content, "plain")

            # HTML version
            html_content = self._format_html(notification)
            html_part = MIMEText(html_content, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)

                server.send_message(msg)

            logger.info(f"Email notification sent: {notification.title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}", exc_info=True)
            return False

    def _format_text(self, notification: Notification) -> str:
        """Format notification as plain text"""
        return notification.format_for_display()

    def _format_html(self, notification: Notification) -> str:
        """Format notification as HTML"""
        from .base import NotificationLevel

        # Color mapping
        color_map = {
            NotificationLevel.INFO: "#17a2b8",
            NotificationLevel.SUCCESS: "#28a745",
            NotificationLevel.WARNING: "#ffc107",
            NotificationLevel.ERROR: "#dc3545",
            NotificationLevel.CRITICAL: "#dc3545",
        }

        emoji_map = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.SUCCESS: "✅",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨",
        }

        color = color_map.get(notification.level, "#6c757d")
        emoji = emoji_map.get(notification.level, "•")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ padding: 20px; }}
                .details {{ background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{emoji} {notification.title}</h2>
                <p>Level: {notification.level.value} | Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            <div class="content">
        """

        if notification.message:
            html += f"<p>{notification.message}</p>"

        if notification.data:
            html += '<div class="details"><h3>Details:</h3><ul>'
            for key, value in notification.data.items():
                html += f"<li><strong>{key}:</strong> {value}</li>"
            html += "</ul></div>"

        if notification.source:
            html += f'<div class="footer">Source: {notification.source}</div>'

        html += """
            </div>
        </body>
        </html>
        """

        return html
