"""Test sending an actual email"""
import sys
sys.path.insert(0, '.')

from tools.webhook_tool import send_simple_email

# Test sending an email
result = send_simple_email(
    to_email="sohamnarvelkar@gmail.com",
    subject="SwasthyaSarthi - Test Email",
    body="Hello! This is a test email from SwasthyaSarthi system to verify email configuration is working."
)

print("=" * 50)
print("Email Send Test Result")
print("=" * 50)
print(f"Success: {result.get('success')}")
if result.get('success'):
    print("[OK] Email sent successfully!")
else:
    print(f"[ERROR] {result.get('error')}")
print("=" * 50)
