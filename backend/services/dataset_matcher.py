"""
Dataset Matcher Service for SwasthyaSarthi.
Matches extracted medicine names with products from the dataset.

Uses fuzzy string matching with cosine similarity for best matching.
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dataset paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products-export.xlsx")

# Similarity threshold for matching (0-1)
DEFAULT_THRESHOLD = 0.6
HIGH_CONFIDENCE_THRESHOLD = 0.75


class DatasetMatcher:
    """
    Matches medicine names from prescriptions with products in the dataset.
    Uses fuzzy string matching to find the best matches.
    """
    
    def __init__(self, products_file: str = None):
        """
        Initialize the dataset matcher.
        
        Args:
            products_file: Path to products Excel file
        """
        self.products_file = products_file or PRODUCTS_FILE
        self.products_df = None
        self.product_names = []
        self.product_lookup = {}
        self._load_products()
    
    def _load_products(self):
        """Load products from the Excel file."""
        try:
            if os.path.exists(self.products_file):
                self.products_df = pd.read_excel(self.products_file)
                
                # Find the product name column (common names)
                name_column = self._find_name_column()
                
                if name_column and name_column in self.products_df.columns:
                    # Clean and store product names
                    self.products_df[name_column] = self.products_df[name_column].astype(str)
                    self.product_names = self.products_df[name_column].tolist()
                    
                    # Create lookup dictionary
                    for idx, name in enumerate(self.product_names):
                        self.product_lookup[name.lower().strip()] = {
                            "index": idx,
                            "name": name,
                            "original_name": name
                        }
                    
                    logger.info(f"[Dataset Matcher] Loaded {len(self.product_names)} products from {self.products_file}")
                else:
                    logger.warning(f"[Dataset Matcher] Could not find product name column in {self.products_file}")
                    logger.warning(f"[Dataset Matcher] Available columns: {list(self.products_df.columns)}")
            else:
                logger.warning(f"[Dataset Matcher] Products file not found: {self.products_file}")
                
        except Exception as e:
            logger.error(f"[Dataset Matcher] Error loading products: {e}")
    
    def _find_name_column(self) -> Optional[str]:
        """Find the product name column in the dataframe."""
        if self.products_df is None:
            return None
        
        # Common column names for product names
        name_columns = [
            'product_name', 'Product Name', 'name', 'Name',
            'product', 'Product', 'item_name', 'Item Name',
            'medicine_name', 'Medicine Name', 'title', 'Title'
        ]
        
        for col in name_columns:
            if col in self.products_df.columns:
                return col
        
        # If no standard column found, return first string column
        for col in self.products_df.columns:
            if self.products_df[col].dtype == 'object':
                logger.info(f"[Dataset Matcher] Using column '{col}' as product name")
                return col
        
        return None
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using multiple methods.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0-1)
        """
        # Normalize strings
        s1 = str1.lower().strip()
        s2 = str2.lower().strip()
        
        # Method 1: SequenceMatcher (best for substring matching)
        seq_ratio = SequenceMatcher(None, s1, s2).ratio()
        
        # Method 2: Token-based matching (for multi-word products)
        tokens1 = set(s1.split())
        tokens2 = set(s2.split())
        
        if tokens1 and tokens2:
            intersection = len(tokens1 & tokens2)
            union = len(tokens1 | tokens2)
            token_ratio = intersection / union if union > 0 else 0
            
            # Method 3: Check if one is substring of another
            substring_score = 0.0
            if s1 in s2 or s2 in s1:
                substring_score = 0.9
            elif any(t in s2 for t in tokens1 if len(t) > 3):
                substring_score = 0.8
            
            # Combine scores with weights
            combined_score = (seq_ratio * 0.4) + (token_ratio * 0.3) + (substring_score * 0.3)
            return max(combined_score, seq_ratio)
        
        return seq_ratio
    
    def find_match(self, medicine_name: str, threshold: float = DEFAULT_THRESHOLD) -> Optional[Dict]:
        """
        Find the best matching product for a medicine name.
        
        Args:
            medicine_name: Medicine name to match
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            Dictionary with match information or None if no match found
        """
        if not medicine_name or not self.product_names:
            return None
        
        best_match = None
        best_score = 0.0
        
        # Search through all products
        for product_name in self.product_names:
            score = self._calculate_similarity(medicine_name, product_name)
            
            if score > best_score:
                best_score = score
                best_match = product_name
        
        # Check if best match meets threshold
        if best_score >= threshold:
            # Get additional product info if available
            product_info = self._get_product_info(best_match)
            
            return {
                "input_name": medicine_name,
                "matched_name": best_match,
                "confidence": best_score,
                "is_high_confidence": best_score >= HIGH_CONFIDENCE_THRESHOLD,
                "product_info": product_info
            }
        
        return None
    
    def find_matches(self, medicine_names: List[str], threshold: float = DEFAULT_THRESHOLD) -> List[Dict]:
        """
        Find matches for multiple medicine names.
        
        Args:
            medicine_names: List of medicine names to match
            threshold: Minimum similarity threshold
            
        Returns:
            List of match dictionaries
        """
        matches = []
        
        for medicine_name in medicine_names:
            match = self.find_match(medicine_name, threshold)
            if match:
                matches.append(match)
        
        return matches
    
    def _get_product_info(self, product_name: str) -> Optional[Dict]:
        """Get additional product information from the dataset."""
        if self.products_df is None:
            return None
        
        try:
            # Find the row with this product
            name_column = self._find_name_column()
            if not name_column:
                return None
            
            row = self.products_df[self.products_df[name_column] == product_name]
            
            if not row.empty:
                row_data = row.iloc[0].to_dict()
                # Convert any non-serializable types
                clean_data = {}
                for k, v in row_data.items():
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        clean_data[k] = v
                    else:
                        clean_data[k] = str(v)
                return clean_data
            
        except Exception as e:
            logger.warning(f"[Dataset Matcher] Error getting product info: {e}")
        
        return None
    
    def get_all_products(self) -> List[Dict]:
        """Get all products from the dataset."""
        if self.products_df is None:
            return []
        
        name_column = self._find_name_column()
        if not name_column:
            return []
        
        products = []
        for name in self.product_names:
            info = self._get_product_info(name)
            if info:
                products.append(info)
        
        return products
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for products matching a query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching products
        """
        if not query or not self.product_names:
            return []
        
        query_lower = query.lower().strip()
        
        # Find matches with their scores
        matches = []
        for product_name in self.product_names:
            score = self._calculate_similarity(query_lower, product_name)
            if score > 0.3:  # Lower threshold for search
                matches.append((product_name, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        # Get product info for top matches
        results = []
        for product_name, score in matches[:limit]:
            info = self._get_product_info(product_name)
            if info:
                info["search_score"] = score
                results.append(info)
        
        return results


# Global instance
_matcher: Optional[DatasetMatcher] = None


def get_dataset_matcher() -> DatasetMatcher:
    """Get or create dataset matcher instance."""
    global _matcher
    if _matcher is None:
        _matcher = DatasetMatcher()
    return _matcher


def match_medicine(medicine_name: str, threshold: float = DEFAULT_THRESHOLD) -> Optional[Dict]:
    """
    Convenience function to match a medicine name.
    
    Args:
        medicine_name: Medicine name to match
        threshold: Minimum similarity threshold
        
    Returns:
        Match dictionary or None
    """
    matcher = get_dataset_matcher()
    return matcher.find_match(medicine_name, threshold)


def match_medicines(medicine_names: List[str], threshold: float = DEFAULT_THRESHOLD) -> List[Dict]:
    """
    Convenience function to match multiple medicine names.
    
    Args:
        medicine_names: List of medicine names
        threshold: Minimum similarity threshold
        
    Returns:
        List of match dictionaries
    """
    matcher = get_dataset_matcher()
    return matcher.find_matches(medicine_names, threshold)


# Export
__all__ = [
    'DatasetMatcher',
    'get_dataset_matcher',
    'match_medicine',
    'match_medicines',
    'DEFAULT_THRESHOLD',
    'HIGH_CONFIDENCE_THRESHOLD'
]
