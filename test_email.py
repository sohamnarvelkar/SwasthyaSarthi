"""Test email configuration and send a test email."""
import os
from tools.webhook_tool import send_simple_email, set_gmail_config

# Test configuration - these would come from .env in production
# For testing, we need to set these up

def test_email_configured():
    """Check if email is configured."""
    from tools.webhook_tool import GMAIL_EMAIL, GMAIL_APP_PASSWORD
    
    if GMAIL_EMAIL and GMAIL_APP_PASSWORD:
        print("✅ Email is configured!")
        print(f"   Email: {GMAIL_EMAIL}")
        return True
    else:
        print("⚠️  Email is NOT configured.")
        print("   To enable email notifications, add to .env file:")
        print("   GMAIL_EMAIL=your-email@gmail.com")
        print("   GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx")
        return False

def send_test_email(to_email: str, subject: str = "Test Email"):
    """Send a test email to verify configuration."""
    from tools.webhook_tool import GMAIL_EMAIL, GMAIL_APP_PASSWORD
    
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        print("❌ Cannot send email - not configured")
        return False
    
    body = """
This is a test email from SwasthyaSarthi.

If you received this, your email configuration is working correctly!

Best regards,
SwasthyaSarthi System
    """
    
    result = send_simple_email(to_email, subject, body)
    if result.get("success"):
        print(f"✅ Test email sent successfully to {to_email}")
        return True
    else:
        print(f"❌ Failed to send email: {result.get('error')}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Email Configuration Test")
    print("=" * 50)
    
    is_configured = test_email_configured()
    
    if is_configured:
        print("\nWould you like to send a test email?")
        print("Uncomment the line below to send a test email:")
        # send_test_email("your-email@gmail.com", "SwasthyaSarthi Test")
    else:
        print("\nPlease configure your .env file to enable email notifications.")
