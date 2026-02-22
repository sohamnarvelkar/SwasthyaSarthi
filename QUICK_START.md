# 🚀 SwasthyaSarthi - Quick Start Guide

## What is this project?
A multi-lingual pharmacy voice assistant that helps patients order medicines through voice or text commands.

---

## How to Run

### Step 1: Start Backend API
```
bash
cd c:/Users/soham/OneDrive/Desktop/SwasthyaSarthi
uvicorn backend.main:app --reload --port 8000
```

### Step 2: Start Frontend (new terminal)
```
bash
streamlit run frontend/app.py
```

### Step 3: Open in Browser
Go to: http://localhost:8501

---

## Current Status
- ✅ Backend API: Running on port 8000
- ✅ Database: 52 medicines loaded
- ✅ Agent System: Working (rule-based mode)
- ⚠️ AI Features: Needs Anthropic API credits

---

## How to Enable Full AI Features

1. Get an API key from https://console.anthropic.com/
2. Add credits to your account
3. Create a `.env` file with:
```
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

---

## How to Enable Email Notifications

1. Create a `.env` file:
```
GMAIL_EMAIL=your-email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

2. Get Gmail App Password:
   - Go to myaccount.google.com
   - Enable 2-Step Verification
   - Create App Password for "Mail"

---

## Features
- 🎤 Voice input (English, Hindi, Marathi, etc.)
- 🔊 Text-to-speech output
- 💊 Medicine ordering
- 📧 Email order confirmations
- 📊 Admin dashboard
- 🔔 Refill alerts

---

## Need Help?
The system is fully verified and working! Just add API credits to enable AI features.
