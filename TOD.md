# SwasthyaSarthi - Feature Updates

## Voice Agent Integration ✅ COMPLETED

### STT (Speech-to-Text)
- Faster Whisper (runs locally, free)
- Google Speech Recognition (fallback)
- File: `frontend/components/voice_input.py`

### TTS (Text-to-Speech)
- Microsoft Edge TTS (natural voices)
- Male/Female voice options
- File: `frontend/components/tts_helper.py`

### Languages
- English, Hindi, Marathi

---

## Webhook & Notifications ✅ COMPLETED

### Features Added:
- **Email Notifications**: Gmail SMTP for order confirmations
- **SMS Notifications**: Twilio integration (optional)
- **Generic Webhooks**: Send to any URL
- **Multi-channel**: Email, SMS, Webhook, Fulfillment

### Files Modified:
- `tools/webhook_tool.py` - Complete notification system with Gmail SMTP
- `agents/execution_agent.py` - Integrated notifications on order placement

### Configuration:
Add to your `.env` file:
```
# Gmail Configuration (for sending emails)
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# SMS (optional - requires Twilio)
SMS_API_KEY=your_twilio_api_key
```

### How to get Gmail App Password:
1. Go to **myaccount.google.com**
2. Enable **2-Step Verification** 
3. Go to **App passwords** (https://myaccount.google.com/apppasswords)
4. Create new app password for "Mail"
5. Use the 16-character password in GMAIL_APP_PASSWORD

⚠️ Note: You need 2-Step Verification enabled to create App Passwords

### Usage:
```
python
from tools.webhook_tool import trigger_order_notifications

order_details = {
    "order_id": "12345",
    "customer_email": "customer@example.com",
    "customer_phone": "+1234567890",
    "items": [{"name": "Medicine", "quantity": 2, "price": 100}],
    "total": 200
}

# Send notifications
trigger_order_notifications(order_details, channels=["email", "sms"])
