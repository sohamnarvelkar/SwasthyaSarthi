"""Simple email test that writes to file"""
import sys
sys.path.insert(0, '.')

# Set UTF-8 encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from tools.webhook_tool import send_simple_email

# Test sending an email
result = send_simple_email(
    to_email="sohamnarvelkar@gmail.com",
    subject="SwasthyaSarthi - Test Email",
    body="Hello! This is a test email from SwasthyaSarthi system."
)

# Write result to file
with open('email_test_result.txt', 'w', encoding='utf-8') as f:
    f.write("Email Test Result\n")
    f.write("=" * 30 + "\n")
    f.write(f"Success: {result.get('success')}\n")
    if result.get('success'):
        f.write("Email sent successfully!\n")
    else:
        f.write(f"Error: {result.get('error')}\n")

print("Result written to email_test_result.txt")
