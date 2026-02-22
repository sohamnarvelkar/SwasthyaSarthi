"""Test email configuration"""
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
import os

load_dotenv()

gmail_email = os.getenv("GMAIL_EMAIL")
gmail_password = os.getenv("GMAIL_APP_PASSWORD")

print("=" * 50)
print("Email Configuration Test")
print("=" * 50)

if gmail_email:
    print(f"[OK] GMAIL_EMAIL: {gmail_email}")
else:
    print("[ERROR] GMAIL_EMAIL not found in .env")

if gmail_password:
    print(f"[OK] GMAIL_APP_PASSWORD: {'*' * len(gmail_password)}")
else:
    print("[ERROR] GMAIL_APP_PASSWORD not found in .env")

# Test importing webhook tool
print("\nTesting webhook_tool import...")
try:
    from tools.webhook_tool import GMAIL_EMAIL, GMAIL_APP_PASSWORD
    print(f"[OK] webhook_tool loaded GMAIL_EMAIL: {GMAIL_EMAIL}")
    print(f"[OK] webhook_tool loaded GMAIL_APP_PASSWORD: {'*' if GMAIL_APP_PASSWORD else 'None'}")
except Exception as e:
    print(f"[ERROR] Failed to import: {e}")

print("\n" + "=" * 50)
