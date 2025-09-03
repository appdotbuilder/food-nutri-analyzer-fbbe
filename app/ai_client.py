"""Simple AI client interface for food analysis."""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AIClient:
    """Simple AI client for food image analysis."""

    def analyze_food_image(self, image_data: str) -> Optional[Dict[str, Any]]:
        """
        Analyze food image and return nutritional information.
        For now, returns a realistic sample response.
        In production, this would call the actual AI service.
        """
        try:
            # For demonstration, return a sample analysis
            # In production, this would send image_data to AI service
            sample_response = {
                "food_items": ["mixed salad", "grilled chicken"],
                "confidence_score": 0.85,
                "nutritional_info": {
                    "calories": 185.0,
                    "protein_g": 25.3,
                    "carbohydrates_g": 8.2,
                    "total_fat_g": 6.1,
                    "saturated_fat_g": 1.4,
                    "fiber_g": 3.2,
                    "sugar_g": 4.1,
                    "sodium_mg": 320.0,
                },
                "estimated_portion_g": 250.0,
                "vitamins": {"vitamin_c_mg": 35.2, "vitamin_a_iu": 1250.0, "folate_mcg": 65.0},
                "minerals": {"calcium_mg": 85.0, "iron_mg": 2.8, "potassium_mg": 420.0},
                "allergens": [{"name": "dairy", "confidence": 0.2, "detected_in": "possible dressing"}],
            }

            logger.info("Generated sample food analysis response")
            return sample_response

        except Exception as e:
            logger.error(f"Error in AI food analysis: {e}")
            return None


def get_ai_client() -> AIClient:
    """Get AI client instance."""
    return AIClient()
