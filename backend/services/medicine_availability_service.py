"""
Medicine Availability Service - Dual Knowledge Architecture
Checks if medicine exists in dataset (internal) or requires external sourcing.

This service implements the core logic:
- INTERNAL_AVAILABLE: Medicine exists in dataset → normal ordering
- EXTERNAL_REQUIRED: Medicine not in dataset → external procurement
"""

from typing import Dict, Optional, Tuple
from backend.services.dataset_matcher import get_dataset_matcher
from tools.inventory_tool import get_medicine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Availability status constants
INTERNAL_AVAILABLE = "INTERNAL_AVAILABLE"
EXTERNAL_REQUIRED = "EXTERNAL_REQUIRED"
DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
INVENTORY_NOT_FOUND = "INVENTORY_NOT_FOUND"


def check_medicine_availability(medicine_name: str, check_inventory: bool = True) -> Dict:
    """
    Check if medicine is available internally or requires external sourcing.
    
    Args:
        medicine_name: Name of the medicine to check
        check_inventory: Whether to also check inventory/stock levels
    
    Returns:
        Dictionary with:
        {
            "status": "INTERNAL_AVAILABLE" | "EXTERNAL_REQUIRED" | "DATASET_NOT_FOUND",
            "medicine_source": "internal" | "external",
            "dataset_match": dict | None,
            "inventory_info": dict | None,
            "message": str
        }
    """
    if not medicine_name or not medicine_name.strip():
        return {
            "status": DATASET_NOT_FOUND,
            "medicine_source": "unknown",
            "dataset_match": None,
            "inventory_info": None,
            "message": "No medicine name provided"
        }
    
    medicine_name = medicine_name.strip()
    logger.info(f"[Availability] Checking availability for: {medicine_name}")
    
    # Step 1: Check dataset for exact/close match
    dataset_matcher = get_dataset_matcher()
    dataset_match = dataset_matcher.find_match(medicine_name, threshold=0.6)
    
    if dataset_match:
        logger.info(f"[Availability] Found in dataset: {dataset_match.get('matched_name')}")
        
        # Step 2: Check inventory if requested
        if check_inventory:
            inventory_info = get_medicine(dataset_match.get("matched_name", ""))
            
            if inventory_info:
                stock = inventory_info.get("stock", 0)
                if stock > 0:
                    return {
                        "status": INTERNAL_AVAILABLE,
                        "medicine_source": "internal",
                        "dataset_match": dataset_match,
                        "inventory_info": inventory_info,
                        "message": f"Available in pharmacy (stock: {stock})"
                    }
                else:
                    # In dataset but out of stock - could still do external
                    return {
                        "status": INTERNAL_AVAILABLE,
                        "medicine_source": "internal",
                        "dataset_match": dataset_match,
                        "inventory_info": inventory_info,
                        "message": "In dataset but currently out of stock"
                    }
            else:
                # In dataset but not in inventory yet
                return {
                    "status": INTERNAL_AVAILABLE,
                    "medicine_source": "internal",
                    "dataset_match": dataset_match,
                    "inventory_info": None,
                    "message": "Found in dataset (inventory not loaded)"
                }
        
        return {
            "status": INTERNAL_AVAILABLE,
            "medicine_source": "internal",
            "dataset_match": dataset_match,
            "inventory_info": None,
            "message": "Available in pharmacy dataset"
        }
    
    # Step 3: Not in dataset - requires external sourcing
    logger.info(f"[Availability] Not in dataset: {medicine_name} - external required")
    return {
        "status": EXTERNAL_REQUIRED,
        "medicine_source": "external",
        "dataset_match": None,
        "inventory_info": None,
        "message": "Not in pharmacy inventory - can be sourced externally"
    }


def check_medicine_source(medicine_name: str) -> Tuple[str, Dict]:
    """
    Quick check to get medicine source only.
    
    Args:
        medicine_name: Name of the medicine
    
    Returns:
        Tuple of (source: "internal" | "external", details: dict)
    """
    result = check_medicine_availability(medicine_name, check_inventory=False)
    return result["medicine_source"], result


def is_internal_medicine(medicine_name: str) -> bool:
    """
    Simple boolean check if medicine is in internal dataset.
    
    Args:
        medicine_name: Name of the medicine
    
    Returns:
        True if medicine is in dataset, False otherwise
    """
    result = check_medicine_availability(medicine_name, check_inventory=False)
    return result["medicine_source"] == "internal"


def get_medicine_info_for_response(medicine_name: str) -> Dict:
    """
    Get comprehensive medicine info for building response messages.
    
    Args:
        medicine_name: Name of the medicine
    
    Returns:
        Dictionary with all relevant info for response generation
    """
    result = check_medicine_availability(medicine_name, check_inventory=True)
    
    return {
        "medicine_name": medicine_name,
        "source": result["medicine_source"],
        "status": result["status"],
        "dataset_match": result["dataset_match"],
        "inventory": result["inventory_info"],
        "response_message": result["message"],
        # Flags for response generation
        "can_order_internally": result["status"] == INTERNAL_AVAILABLE and 
                                result["inventory_info"] is not None and 
                                result["inventory_info"].get("stock", 0) > 0,
        "requires_external": result["status"] == EXTERNAL_REQUIRED,
        "out_of_stock": result["inventory_info"] is not None and 
                        result["inventory_info"].get("stock", 0) == 0
    }


# Export for use in other modules
__all__ = [
    'check_medicine_availability',
    'check_medicine_source',
    'is_internal_medicine',
    'get_medicine_info_for_response',
    'INTERNAL_AVAILABLE',
    'EXTERNAL_REQUIRED',
    'DATASET_NOT_FOUND',
    'INVENTORY_NOT_FOUND'
]
