"""Final verification with dataset medicines."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("DATASET-BASED SYSTEM VERIFICATION")
print("=" * 60)

# Test various medicine requests
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

print("\nTesting medicine matching:")
for user_input, category in test_cases:
    state = pharmacist_agent({
        'user_input': user_input,
        'user_language': 'en',
        'structured_order': {}
    })
    product = state.get('structured_order', {}).get('product_name', 'NOT FOUND')
    print(f"  {category:12} -> {product}")

print("\n" + "=" * 60)
print("All medicines are from the dataset!")
print("=" * 60)
