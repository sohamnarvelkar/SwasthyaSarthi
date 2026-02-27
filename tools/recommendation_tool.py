"""
Recommendation Tool - Finds alternative medicines using similarity matching.
Uses products-export.xlsx to find similar products when out of stock or prescription required.

Demo: "If out of stock, system suggests similar product from products-export.xlsx"
"""
import pandas as pd
import os
from difflib import SequenceMatcher
from typing import List, Dict, Optional
from tools.inventory_tool import get_all_medicines

# Cache for products data
_products_cache = None

def _load_products_data() -> pd.DataFrame:
    """Load and cache products data from Excel file."""
    global _products_cache
    if _products_cache is not None:
        return _products_cache
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    products_path = os.path.join(base_path, "data", "products-export.xlsx")
    
    try:
        df = pd.read_excel(products_path)
        _products_cache = df
        return df
    except Exception as e:
        print(f"[Recommendation Tool] Warning: Could not load products data: {e}")
        return pd.DataFrame()

def _calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def _extract_key_features(product_name: str) -> List[str]:
    """Extract key features from product name for better matching."""
    name_lower = product_name.lower()
    features = []
    
    # Common medicine types
    if "tablet" in name_lower or "tabletten" in name_lower:
        features.append("tablet")
    if "capsule" in name_lower or "kapseln" in name_lower:
        features.append("capsule")
    if "gel" in name_lower or "creme" in name_lower:
        features.append("topical")
    if "tropfen" in name_lower or "drops" in name_lower:
        features.append("drops")
    if "spray" in name_lower:
        features.append("spray")
    
    # Package sizes (common patterns)
    import re
    size_match = re.search(r'(\d+)\s*(mg|g|ml)', name_lower)
    if size_match:
        features.append(f"{size_match.group(1)}{size_match.group(2)}")
    
    # Remove common words for better matching
    clean_name = re.sub(r'\b\d+\s*(mg|g|ml|tabletten|kapseln|gel|creme|tropfen|spray)\b', '', name_lower)
    clean_name = re.sub(r'[^\w\s]', '', clean_name)  # Remove punctuation
    features.append(clean_name.strip())
    
    return features

def find_alternatives(product_name: str, reason: str = "out_of_stock", max_suggestions: int = 3) -> List[Dict]:
    """
    Find alternative medicines based on similarity to the requested product.
    
    Args:
        product_name: The original product name
        reason: Why alternative is needed ("out_of_stock", "prescription_required", "unavailable")
        max_suggestions: Maximum number of alternatives to return
    
    Returns:
        List of alternative products with similarity scores
    """
    alternatives = []
    
    try:
        # Load products data
        products_df = _load_products_data()
        if products_df.empty:
            return alternatives
        
        # Get current inventory to check availability
        inventory_medicines = get_all_medicines()
        inventory_names = {med.get("name", "").lower() for med in inventory_medicines}
        
        # Extract features from requested product
        requested_features = _extract_key_features(product_name)
        
        candidates = []
        
        for _, row in products_df.iterrows():
            candidate_name = str(row.get("name", "")).strip()
            if not candidate_name:
                continue
            
            # Skip if it's the same product
            if candidate_name.lower() == product_name.lower():
                continue
            
            # Check if this product is available in inventory
            if candidate_name.lower() not in inventory_names:
                continue
            
            # Calculate similarity
            name_similarity = _calculate_similarity(product_name, candidate_name)
            
            # Feature-based similarity
            candidate_features = _extract_key_features(candidate_name)
            feature_similarity = 0
            for req_feat in requested_features:
                for cand_feat in candidate_features:
                    feat_sim = _calculate_similarity(req_feat, cand_feat)
                    feature_similarity = max(feature_similarity, feat_sim)
            
            # Combined score (weighted average)
            combined_score = (name_similarity * 0.6) + (feature_similarity * 0.4)
            
            if combined_score > 0.3:  # Minimum threshold
                candidates.append({
                    "name": candidate_name,
                    "similarity_score": round(combined_score, 3),
                    "package_size": str(row.get("package_size", "")),
                    "description": str(row.get("description", "")),
                    "reason": reason
                })
        
        # Sort by similarity score and return top suggestions
        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        alternatives = candidates[:max_suggestions]
        
        print(f"[Recommendation Tool] Found {len(alternatives)} alternatives for '{product_name}' (reason: {reason})")
        
    except Exception as e:
        print(f"[Recommendation Tool] Error finding alternatives: {e}")
    
    return alternatives

def get_alternative_recommendations(product_name: str, reason: str = "out_of_stock", 
                                  user_language: str = "en") -> Dict:
    """
    Get formatted alternative recommendations with user-friendly messages.
    
    Args:
        product_name: Original product name
        reason: Reason for recommendation
        user_language: User's language preference
    
    Returns:
        Dictionary with alternatives and formatted message
    """
    alternatives = find_alternatives(product_name, reason)
    
    if not alternatives:
        return {
            "alternatives": [],
            "message": _get_no_alternatives_message(user_language, product_name, reason),
            "has_alternatives": False
        }
    
    # Format alternatives for display
    formatted_alternatives = []
    for alt in alternatives:
        formatted_alternatives.append({
            "name": alt["name"],
            "similarity": f"{alt['similarity_score']:.1%}",
            "package_size": alt["package_size"],
            "description": alt["description"][:100] + "..." if len(alt["description"]) > 100 else alt["description"]
        })
    
    message = _get_alternatives_message(user_language, product_name, reason, formatted_alternatives)
    
    return {
        "alternatives": formatted_alternatives,
        "message": message,
        "has_alternatives": True,
        "reason": reason
    }

def _get_alternatives_message(language: str, product_name: str, reason: str, alternatives: List[Dict]) -> str:
    """Get user-friendly alternative recommendations message."""
    reason_text = {
        "en": {
            "out_of_stock": "currently out of stock",
            "prescription_required": "requires a prescription",
            "unavailable": "not available"
        },
        "hi": {
            "out_of_stock": "वर्तमान में स्टॉक में नहीं है",
            "prescription_required": "नुस्खा आवश्यक है",
            "unavailable": "उपलब्ध नहीं है"
        },
        "mr": {
            "out_of_stock": "सध्या स्टॉकमध्ये नाही",
            "prescription_required": "प्रिस्क्रिप्शन आवश्यक आहे",
            "unavailable": "उपलब्ध नाही"
        }
    }
    
    lang_data = reason_text.get(language, reason_text["en"])
    reason_msg = lang_data.get(reason, lang_data["unavailable"])
    
    messages = {
        "en": f"💡 **Smart Alternative Suggestions**\n\n'{product_name}' is {reason_msg}. Here are some similar alternatives:\n\n",
        "hi": f"💡 **स्मार्ट विकल्प सुझाव**\n\n'{product_name}' {reason_msg}। यहां कुछ समान विकल्प हैं:\n\n",
        "mr": f"💡 **स्मार्ट पर्याय सूचना**\n\n'{product_name}' {reason_msg}। येथे काही समान पर्याय आहेत:\n\n"
    }
    
    msg = messages.get(language, messages["en"])
    
    for i, alt in enumerate(alternatives, 1):
        msg += f"{i}. **{alt['name']}**\n"
        msg += f"   📦 Package: {alt['package_size']}\n"
        msg += f"   📝 {alt['description']}\n"
        msg += f"   🎯 Similarity: {alt['similarity']}\n\n"
    
    msg += "Would you like to order one of these alternatives instead?"
    
    return msg

def _get_no_alternatives_message(language: str, product_name: str, reason: str) -> str:
    """Get message when no alternatives are found."""
    messages = {
        "en": f"Sorry, I couldn't find suitable alternatives for '{product_name}' at this time. Would you like me to notify you when it becomes available?",
        "hi": f"क्षमा करें, मुझे '{product_name}' के लिए उपयुक्त विकल्प नहीं मिले। क्या आप चाहेंगे कि जब यह उपलब्ध हो जाए तो मैं आपको सूचित करूं?",
        "mr": f"क्षमस्व, मला '{product_name}' साठी योग्य पर्याय सापडले नाहीत. तुम्हाला हे उपलब्ध झाल्यावर मी तुम्हाला सूचित करू का?"
    }
    
    return messages.get(language, messages["en"])

# Test function
if __name__ == "__main__":
    # Test the recommendation tool
    test_product = "Paracetamol"
    recommendations = get_alternative_recommendations(test_product, "out_of_stock")
    print("Test Recommendations:")
    print(recommendations["message"])
