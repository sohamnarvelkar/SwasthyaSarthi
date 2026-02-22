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
- **Email Notifications**: SendGrid integration for order confirmations
- **SMS Notifications**: Twilio integration
- **Generic Webhooks**: Send to any URL
- **Multi-channel**: Email, SMS, Webhook, Fulfillment

### Files Modified:
- `tools/webhook_tool.py` - Complete notification system
- `agents/execution_agent.py` - Integrated notifications on order placement

### Configuration:
Add to `.env` file:
```
EMAIL_API_KEY=your_sendgrid_api_key
EMAIL_FROM=noreply@yourdomain.com
SMS_API_KEY=your_twilio_api_key
```

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
