import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """Send email using SMTP configuration."""
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password]):
        logger.warning("SMTP not configured, skipping email send")
        return False
    
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = to_email

        # Add text part if provided
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)

        # Add HTML part
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Send email
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=True,
            username=settings.smtp_user,
            password=settings.smtp_password,
        )

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email."""
    reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
    
    subject = f"Password Reset - {settings.app_name}"
    
    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello,</p>
            <p>You have requested to reset your password for {settings.app_name}.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>{settings.app_name} Team</p>
        </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    Hello,
    
    You have requested to reset your password for {settings.app_name}.
    
    Click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you did not request this password reset, please ignore this email.
    
    Best regards,
    {settings.app_name} Team
    """
    
    return await send_email(email, subject, html_content, text_content)


async def send_verification_email(email: str, verification_token: str) -> bool:
    """Send email verification email."""
    verification_url = f"{settings.frontend_url}/verify-email?token={verification_token}"
    
    subject = f"Email Verification - {settings.app_name}"
    
    html_content = f"""
    <html>
        <body>
            <h2>Email Verification</h2>
            <p>Hello,</p>
            <p>Thank you for registering with {settings.app_name}!</p>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <br>
            <p>Best regards,<br>{settings.app_name} Team</p>
        </body>
    </html>
    """
    
    text_content = f"""
    Email Verification
    
    Hello,
    
    Thank you for registering with {settings.app_name}!
    
    Please click the link below to verify your email address:
    {verification_url}
    
    This link will expire in 24 hours.
    
    Best regards,
    {settings.app_name} Team
    """
    
    return await send_email(email, subject, html_content, text_content)
