# Chatbot Integration Fix - TODO List

## Task: Fix chatbot to handle all user intents (medicines, prescription, orders, profile, refills)

### Steps:
1. [x] Analyze codebase and understand the issue
2. [x] Create agents/router_agent.py - Intent detection router
3. [x] Update orchestration/graph.py - Add router at entry point
4. [ ] Test the fix

## Intent Types Supported:
- SHOW_MEDICINES: Show available medicines list
- UPLOAD_PRESCRIPTION: Upload a prescription
- ORDER_HISTORY: Show user's order history
- REFILL_REMINDERS: Check refill reminders
- SHOW_PROFILE: Show user profile
- MEDICINE_ORDER: Place a medicine order (existing)
- GENERAL_CHAT: General conversation

## Files Created/Modified:
- CREATE: agents/router_agent.py (NEW - handles all intents)
- MODIFY: orchestration/graph.py (added router at entry point)
