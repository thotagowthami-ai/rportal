import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.smtp_ssl = settings.SMTP_SSL
        self.from_email = settings.FROM_EMAIL
        self.smtp_timeout = 10  # seconds
        
        # Check if SMTP is configured
        self.smtp_enabled = bool(self.smtp_host and self.smtp_user and self.smtp_password)
        
        # Back-compat for SendGrid if SMTP is not configured
        self.sendgrid_api_key = settings.SENDGRID_API_KEY
        self.sendgrid_enabled = bool(self.sendgrid_api_key and not self.smtp_enabled)

    def send_reset_password_email(self, to_email: str, reset_link: str) -> bool:
        """
        Send a password reset email using SMTP (primary) or SendGrid (legacy).
        If no provider is configured, it logs the link for debugging.
        """
        subject = "Reset your AuraRecruiting password"
        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #3525cd;">AuraRecruiting</h2>
            <p>Hello,</p>
            <p>We received a request to reset your password. Click the button below to set a new one:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #3525cd; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Reset Password</a>
            </div>
            <p style="font-size: 13px; color: #475569;">If the button doesn't work, copy and paste this link:</p>
            <p style="word-break: break-all; font-size: 12px;">
                <a href="{reset_link}">{reset_link}</a>
            </p>
            <p>This link will expire in 15 minutes.</p>
            <p>If you didn't request this, you can safely ignore this email.</p>
            <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 20px 0;" />
            <p style="font-size: 12px; color: #64748b;">AuraRecruiting - Hiring intelligence platform</p>
        </div>
        """

        if not self.smtp_enabled and not self.sendgrid_enabled:
            logger.warning(
                "No email provider (SMTP or SendGrid) configured — "
                "password reset email NOT delivered to %s.",
                to_email,
            )
            # Only emit a debug hint in non-production environments,
            # and never log the full token — only the last 4 characters.
            if settings.DEBUG:
                token_hint = reset_link[-4:] if len(reset_link) >= 4 else "****"
                logger.debug(
                    "[DEV] Reset link tail for %s: ...%s  "
                    "(full link intentionally redacted — configure SMTP to deliver email)",
                    to_email,
                    token_hint,
                )
            return False  # Signal to callers that delivery failed

        if self.smtp_enabled:
            return self._send_via_smtp(to_email, subject, html_content)
        else:
            return self._send_via_sendgrid(to_email, subject, html_content)

    def _send_via_smtp(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SMTP."""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            # Add HTML body
            part = MIMEText(html_content, "html")
            message.attach(part)

            # Connect and send — context manager guarantees socket cleanup on any exit
            smtp_cls = smtplib.SMTP_SSL if self.smtp_ssl else smtplib.SMTP
            with smtp_cls(self.smtp_host, self.smtp_port, timeout=self.smtp_timeout) as server:
                if not self.smtp_ssl and self.smtp_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, message.as_string())

            logger.info(f"Password reset email sent via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP failed to send email to {to_email}: {str(e)}")
            return False

    def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email using SendGrid (legacy implementation)."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, TrackingSettings, ClickTracking
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )
            message.tracking_settings = TrackingSettings(
                click_tracking=ClickTracking(enable=False, enable_text=False)
            )

            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Password reset email accepted by SendGrid for {to_email}. Status: {response.status_code}")
                return True
            else:
                logger.error(f"SendGrid rejected email to {to_email}. Status: {response.status_code}, Body: {response.body}")
                return False
        except Exception as e:
            logger.error(f"SendGrid failed to send email to {to_email}: {str(e)}")
            return False


email_service = EmailService()
