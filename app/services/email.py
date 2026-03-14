import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Check if SendGrid is configured
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")
USE_MOCK_EXTERNAL = os.getenv("USE_MOCK_EXTERNAL", "false").lower() == "true"


def send_password_reset_email(email: str, reset_token: str, reset_url: str) -> bool:
    """
    Send password reset email.
    - Production: SendGrid API
    - Development without SendGrid: Print to console for testing
    - Development with USE_MOCK_EXTERNAL: Log with clear [MOCK] prefix
    """
    full_reset_url = f"{reset_url}?token={reset_token}"

    if not SENDGRID_API_KEY:
        # Development/Mock mode
        dev_msg = f"[MOCK] Password reset link for {email}: {full_reset_url}"
        logger.info(dev_msg)
        # Also print for immediate visibility in development
        print(f"\n{'='*80}")
        print(f"🔐 PASSWORD RESET EMAIL (Development Mode - Not Sent)")
        print(f"{'='*80}")
        print(f"To: {email}")
        print(f"Reset Link: {full_reset_url}")
        print(f"Token expires in: 1 hour")
        print(f"{'='*80}\n")
        return True

    # Production mode - send via SendGrid
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail

        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=email,
            subject="Reset Your Password - Watchlist",
            html_content=f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
                    <h2 style="color: #1f2937;">Reset Your Password</h2>
                    <p>Click the button below to reset your password. This link will expire in 1 hour.</p>
                    <a href="{full_reset_url}"
                       style="display: inline-block; background-color: #1f2937; color: white;
                              padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 20px 0;">
                        Reset Password
                    </a>
                    <p style="color: #6b7280; font-size: 14px;">
                        If you didn't request this, you can safely ignore this email.
                    </p>
                </div>
            """
        )

        response = sg.send(message)
        logger.info(f"Password reset email sent to {email}")
        return response.status_code == 202

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
