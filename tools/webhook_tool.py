# tools/webhook_tool.py
import requests
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()

# Try to load from environment variables or .env file
def _load_config():
    """Load configuration from environment variables."""
    return {
        "GMAIL_EMAIL": os.environ.get("GMAIL_EMAIL"),
        "GMAIL_APP_PASSWORD": os.environ.get("GMAIL_APP_PASSWORD"),
        "SMS_API_KEY": os.environ.get("SMS_API_KEY")
    }

# Load config at module import
_config = _load_config()

# Configuration for Gmail
# Set these in your .env file or environment variables
GMAIL_EMAIL = _config.get("GMAIL_EMAIL")      # your-email@gmail.com
GMAIL_APP_PASSWORD = _config.get("GMAIL_APP_PASSWORD")  # Gmail App Password (not your regular password)

# SMS Configuration (optional)
SMS_API_KEY = _config.get("SMS_API_KEY")


def set_gmail_config(email: str, app_password: str):
    """Configure Gmail settings"""
    global GMAIL_EMAIL, GMAIL_APP_PASSWORD
    GMAIL_EMAIL = email
    GMAIL_APP_PASSWORD = app_password


def set_sms_config(api_key: str):
    """Configure SMS settings"""
    global SMS_API_KEY
    SMS_API_KEY = api_key


def trigger_fulfillment(order_id: str):
    """Trigger warehouse fulfillment webhook"""
    print(f"Webhook: order {order_id} sent to warehouse.")
    return {"status": "fulfilled", "order_id": order_id}


def send_order_confirmation_email(
    to_email: str,
    order_details: Dict[str, Any],
    subject: str = "SwasthyaSarthi Order Confirmation"
) -> Dict[str, Any]:
    """
    Send order confirmation email using Gmail SMTP.
    Includes detailed pricing information from the dataset.
    Supports prescription-based orders with detected medicines list.
    
    Args:
        to_email: Recipient email address
        order_details: Dictionary containing order information including:
            - order_id: Order ID
            - items: List of items with name, quantity, unit_price, total_price
            - unit_price: Price per unit
            - total_price: Total order price
            - date: Order date
            - address: Shipping address
            - source: Order source (online/prescription)
            - prescription_image: Filename of prescription image
            - detected_medicines_list: List of detected medicines from prescription
        subject: Email subject line
    
    Returns:
        dict: Status of the email sending
    """
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        return {
            "success": False,
            "error": "Gmail not configured. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env"
        }
    
    # Extract order details
    order_id = order_details.get('order_id', 'N/A')
    order_date = order_details.get('date', 'N/A')
    items = order_details.get('items', [])
    unit_price = order_details.get('unit_price', 0)
    total_price = order_details.get('total_price', 0)
    address = order_details.get('address', 'N/A')
    
    # Prescription-specific fields
    source = order_details.get('source', 'online')
    prescription_image = order_details.get('prescription_image', None)
    detected_medicines_list = order_details.get('detected_medicines_list', [])
    
    # Format items for email
    items_text = format_order_items(items)
    
    # Build source info for prescription orders
    source_info = ""
    if source == 'prescription':
        source_info = f"""
Source: Prescription Upload
Prescription Image: {prescription_image if prescription_image else 'Not attached'}
"""
        if detected_medicines_list:
            medicines_list = "\n".join([f"  - {med}" for med in detected_medicines_list])
            source_info += f"Detected Medicines:\n{medicines_list}\n"
    
    # Email content template with price details
    email_body = f"""
Subject: {subject}

Hello,

Your medicine order has been successfully placed.

Order Details:
--------------------------------
Order ID: {order_id}
{items_text}
--------------------------------
Price per Unit: ₹{unit_price:.2f}
Total Price: ₹{total_price:.2f}
Order Time: {order_date}
{source_info}--------------------------------

Shipping Address:
{address}

Your order will be processed and shipped soon.

Thank you for using SwasthyaSarthi.

Best regards,
SwasthyaSarthi Team
    """
    
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Upgrade connection to secure
        
        # Login
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        
        # Send email
        server.sendmail(GMAIL_EMAIL, to_email, msg.as_string())
        
        # Quit server
        server.quit()
        
        return {"success": True, "message": "Email sent successfully via Gmail"}
        
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False, 
            "error": "Gmail authentication failed. Make sure you're using an App Password, not your regular password."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_simple_email(
    to_email: str,
    subject: str,
    body: str
) -> Dict[str, Any]:
    """
    Send a simple email using Gmail SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body
    
    Returns:
        dict: Status of the email sending
    """
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        return {
            "success": False,
            "error": "Gmail not configured. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env"
        }
    
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_EMAIL, to_email, msg.as_string())
        server.quit()
        
        return {"success": True, "message": "Email sent successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_order_confirmation_sms(
    phone_number: str,
    order_details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send order confirmation SMS with price details.
    """
    if not SMS_API_KEY:
        return {
            "success": False,
            "error": "SMS API not configured. Set SMS_API_KEY in .env"
        }
    
    total_price = order_details.get('total_price', 0)
    order_id = order_details.get('order_id', '')
    
    message = f"SwasthyaSarthi: Your order #{order_id} confirmed! "
    message += f"Total: ₹{total_price:.2f}. "
    message += "We'll notify you when it's shipped."
    
    try:
        account_sid = SMS_API_KEY.split(':')[0] if ':' in SMS_API_KEY else SMS_API_KEY
        auth_token = SMS_API_KEY.split(':')[1] if ':' in SMS_API_KEY else ''
        
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            auth=(account_sid, auth_token),
            data={
                "To": phone_number,
                "From": "+1234567890",
                "Body": message
            },
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            return {"success": True, "message": "SMS sent successfully"}
        else:
            return {"success": False, "error": f"SMS API error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def send_generic_webhook(
    webhook_url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Send a generic webhook to any URL."""
    default_headers = {
        "Content-Type": "application/json",
        "User-Agent": "SwasthyaSarthi/1.0"
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=default_headers,
            timeout=30
        )
        
        if response.status_code < 400:
            return {"success": True, "status_code": response.status_code}
        else:
            return {"success": False, "error": f"Webhook error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_order_items(items: list) -> str:
    """Format order items for display in email"""
    if not items:
        return "No items"
    
    formatted = []
    for item in items:
        name = item.get('name', 'Unknown')
        quantity = item.get('quantity', 1)
        unit_price = item.get('unit_price', item.get('price', 0))
        total_price = item.get('total_price', round(unit_price * quantity, 2))
        
        formatted.append(f"Medicine: {name}")
        formatted.append(f"Quantity: {quantity}")
        formatted.append(f"Price per Unit: ₹{unit_price:.2f}")
        formatted.append(f"Item Total: ₹{total_price:.2f}")
    
    return "\n".join(formatted)


def send_login_notification_email(
    to_email: str,
    full_name: str = None,
    subject: str = "Welcome to SwasthyaSarthi - Login Notification"
) -> Dict[str, Any]:
    """
    Send login/welcome notification email when user registers or logs in.
    
    Args:
        to_email: Recipient email address
        full_name: User's full name (optional)
        subject: Email subject line
    
    Returns:
        dict: Status of the email sending
    """
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        return {
            "success": False,
            "error": "Gmail not configured. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env"
        }
    
    user_greeting = f"Hello{f' {full_name}' if full_name else ''}!"
    
    # Email content template
    email_body = f"""
Subject: {subject}

{user_greeting},

Welcome to SwasthyaSarthi - Your AI Pharmacy Assistant!

We're excited to have you on board. You can now:

- Chat with our AI assistant about health concerns
- Get medicine recommendations
- Upload prescriptions for automatic medicine detection
- Place orders for medicines
- Receive order confirmations via email
- Use voice mode for hands-free conversations

Your account is ready to use. Simply log in with your email and password.

Important: Keep your login credentials safe. All order confirmations 
and important notifications will be sent to this email address.

Need help? Just ask our AI assistant!

Thank you for choosing SwasthyaSarthi.

Best regards,
SwasthyaSarthi Team
    """
    
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(email_body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Upgrade connection to secure
        
        # Login
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        
        # Send email
        server.sendmail(GMAIL_EMAIL, to_email, msg.as_string())
        
        # Quit server
        server.quit()
        
        return {"success": True, "message": "Login notification email sent successfully via Gmail"}
        
    except smtplib.SMTPAuthenticationError:
        return {
            "success": False, 
            "error": "Gmail authentication failed. Make sure you're using an App Password, not your regular password."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def trigger_order_notifications(
    order_details: Dict[str, Any],
    channels: list = ["email"]
) -> Dict[str, Any]:
    """
    Trigger order notifications across multiple channels.
    """
    results = {
        "order_id": order_details.get("order_id"),
        "notifications": {}
    }
    
    # Email notification (Gmail)
    if "email" in channels and order_details.get("customer_email"):
        results["notifications"]["email"] = send_order_confirmation_email(
            to_email=order_details["customer_email"],
            order_details=order_details
        )
    
    # SMS notification
    if "sms" in channels and order_details.get("customer_phone"):
        results["notifications"]["sms"] = send_order_confirmation_sms(
            phone_number=order_details["customer_phone"],
            order_details=order_details
        )
    
    # Generic webhook
    if "webhook" in channels and order_details.get("webhook_url"):
        webhook_payload = {
            "event": "order_confirmed",
            "order": order_details
        }
        results["notifications"]["webhook"] = send_generic_webhook(
            webhook_url=order_details["webhook_url"],
            payload=webhook_payload
        )
    
    # Always trigger fulfillment
    results["notifications"]["fulfillment"] = trigger_fulfillment(
        order_details.get("order_id", "unknown")
    )
    
    return results


__all__ = [
    'trigger_fulfillment',
    'send_order_confirmation_email',
    'send_simple_email',
    'send_order_confirmation_sms',
    'send_generic_webhook',
    'trigger_order_notifications',
    'set_gmail_config',
    'set_sms_config'
]
