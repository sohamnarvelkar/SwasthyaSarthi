# ElevenLabs Integration TODO List

## Step 1: Create ElevenLabs Service Layer
- [x] Create `backend/services/elevenlabs_service.py`
- [x] Create `backend/services/__init__.py`

## Step 2: Update Environment Configuration
- [ ] Add `ELEVENLABS_API_KEY` to `.env`

## Step 3: Modify Voice Loop Controller
- [x] Update `frontend/components/voice_loop_controller.py` to use ElevenLabs

## Step 4: Test Integration
- [ ] Verify chat mode remains text-only
- [ ] Verify voice mode uses ElevenLabs
