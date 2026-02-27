# SwasthyaSarthi - Feature Implementation TODO

## New Features Implementation ✅ COMPLETED

### 1. Drug Interaction Detection ✅
- [x] Create `data/drug_interactions.json` - predefined drug interaction database
- [x] Create `agents/drug_interaction_agent.py` - checks patient's existing medicines
- [x] Modify `orchestration/graph.py` - add new agent node to workflow
- [x] Update `agents/state_schema.py` - add new fields for interaction warnings

### 2. Smart Alternative Recommendation ✅
- [x] Create `tools/recommendation_tool.py` - uses string similarity for alternatives
- [x] Modify `agents/safety_agent.py` - integrate alternatives when out of stock/prescription required

### 3. Automatic Procurement Trigger ✅
- [x] Create `tools/procurement_tool.py` - trigger warehouse orders
- [x] Modify `tools/inventory_tool.py` - add stock monitoring
- [x] Add backend endpoint `/auto-procurement` in `backend/main.py`
- [x] Update `backend/models.py` - add ProcurementLog model

## Implementation Notes
- Drug Interaction Agent runs after Safety Agent in the workflow
- Alternative Recommendations integrated into Safety Agent responses
- Procurement triggered automatically when stock < 10 units

## Demo Lines Ready:
🥇 "SwasthyaSarthi doesn't just check stock. It checks patient safety."
🥈 Smart alternatives from products-export.xlsx when out of stock
🥉 "Inventory fell below 10 units, system auto-ordered replenishment."
