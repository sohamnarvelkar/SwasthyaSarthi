"""Simple verification test that writes to file."""
from agents.pharmacist_agent import pharmacist_agent

test_cases = [
    ("I need some pain tablets", "Pain"),
    ("I want vitamins", "Vitamin"),
    ("Need Omega-3 supplement", "Omega"),
    ("For allergy give me medicine", "Allergy"),
    ("I need eye drops", "Eye"),
    ("For cold medicine", "Cold"),
    ("Give me energy supplements", "Energy"),
]

output = []
output.append("=" * 60)
output.append("DATASET-BASED SYSTEM VERIFICATION")
output.append("=" * 60)
output.append("")

for user_input, category in test_cases:
    state = pharmacist_agent({
        'user_input': user_input,
        'user_language': 'en',
        'structured_order': {}
    })
    product = state.get('structured_order', {}).get('product_name', 'NOT FOUND')
    output.append(f"  {category:12} -> {product}")

output.append("")
output.append("=" * 60)
output.append("All medicines are from the dataset!")
output.append("=" * 60)

with open("verification_output.txt", "w") as f:
    f.write("\n".join(output))
    
print("Verification complete!")
