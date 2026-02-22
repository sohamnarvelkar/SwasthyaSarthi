# SwasthyaSarthi - Implementation Plan

## Phase 1: Core Backend Enhancements
- [ ] 1. Update `backend/models.py` - Add Patient model with contact info
- [ ] 2. Update `backend/database.py` - Add patient table creation
- [ ] 3. Update `backend/seed_loader.py` - Load patient data from Excel
- [ ] 4. Update `backend/main.py` - Add new endpoints:
  - `/check-refills` - Get refill alerts
  - `/patients` - Get all patients
  - `/patients/{patient_id}` - Get patient details
  - `/patients/{patient_id}/orders` - Get patient order history

## Phase 2: Agent State & Tools
- [ ] 5. Update `agents/state_schema.py` - Add user identification fields
- [ ] 6. Enhance `tools/inventory_tool.py` - Add fuzzy search, batch check
- [ ] 7. Enhance `tools/history_tool.py` - Add patient contact info retrieval

## Phase 3: Agent Integration
- [ ] 8. Enhance `agents/refill_agent.py` - Return detailed alerts with contact info
- [ ] 9. Create `agents/refill_trigger_agent.py` - Proactive refill checker
- [ ] 10. Update `orchestration/graph.py` - Add refill check node with conditional routing

## Phase 4: Frontend
- [ ] 11. Update `frontend/app.py` - Main app with tabs for Chat and Admin
- [ ] 12. Enhance `frontend/components/chat_ui.py` - Add language selection, voice input
- [ ] 13. Create `frontend/components/admin_panel.py` - Inventory & refill alerts dashboard
- [ ] 14. Update voice components integration

## Phase 5: Testing & Integration
- [ ] 15. Test end-to-end flow
- [ ] 16. Verify all agents work together
