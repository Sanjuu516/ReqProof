import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

# Store recent reset emails in memory for instant verification/testing in development
recent_reset_links: Dict[str, Any] = {}

def send_password_reset_email(
    to_email: str,
    reset_url: str,
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends a password reset email to the user's Gmail/email address.
    If SMTP credentials are not configured, records the simulated email
    with the direct link so the user can still reset their password.
    """
    smtp_host = smtp_host or os.getenv("SMTP_HOST")
    smtp_user = smtp_user or os.getenv("SMTP_USER")
    smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    subject = "ReqProof - Reset Your Password"
    body_text = f"""Hello,

You requested a password reset for your ReqProof account.
Click the link below to set a new password (valid for 1 hour):

{reset_url}

If you did not request this change, please ignore this email.

Best regards,
ReqProof Verification Team
"""

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; rounded: 12px; background-color: #ffffff;">
        <div style="margin-bottom: 20px;">
            <span style="font-size: 20px; font-weight: bold; color: #0284c7;">ReqProof</span>
            <span style="font-size: 11px; font-family: monospace; background: #e0f2fe; color: #0369a1; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">VERIFICATION</span>
        </div>
        <h2 style="color: #0f172a; font-size: 18px; margin-bottom: 12px;">Reset Your Password</h2>
        <p style="color: #475569; font-size: 14px; line-height: 1.5; margin-bottom: 24px;">
            We received a request to reset the password for your ReqProof account associated with <strong>{to_email}</strong>.
        </p>
        <div style="margin-bottom: 28px;">
            <a href="{reset_url}" style="background-color: #0284c7; color: #ffffff; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: bold; display: inline-block;">
                Reset Password
            </a>
        </div>
        <p style="color: #64748b; font-size: 12px; margin-bottom: 8px;">
            Or copy and paste this URL into your browser:
        </p>
        <p style="color: #0284c7; font-size: 12px; word-break: break-all; background-color: #f8fafc; padding: 8px; border-radius: 4px; border: 1px solid #e2e8f0;">
            {reset_url}
        </p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
        <p style="color: #94a3b8; font-size: 11px;">
            This link is valid for 1 hour. If you did not request this, you can safely ignore this message.
        </p>
    </div>
    """

    # Record in development storage
    recent_reset_links[to_email] = {
        "reset_url": reset_url,
        "sent_at": str(os.getenv("CURRENT_TIME", "")),
        "delivered_via": "smtp" if (smtp_host and smtp_user and smtp_password) else "simulated"
    }

    # If real SMTP credentials (e.g. Gmail) are provided, attempt to send
    if smtp_host and smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = to_email

            part1 = MIMEText(body_text, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [to_email], msg.as_string())

            return {
                "success": True,
                "delivered_via": "smtp",
                "message": f"Password reset email sent to {to_email} via {smtp_host}."
            }
        except Exception as e:
            # Fallback to simulated delivery with clear notice
            return {
                "success": True,
                "delivered_via": "simulated",
                "warning": f"SMTP dispatch failed ({str(e)}). Using simulated delivery for local testing.",
                "reset_url": reset_url
            }

    # Default simulated delivery mode (useful for zero-setup local dev)
    return {
        "success": True,
        "delivered_via": "simulated",
        "message": f"Password reset link generated for {to_email}.",
        "reset_url": reset_url
    }
