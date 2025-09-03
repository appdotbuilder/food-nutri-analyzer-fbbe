import time
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from sqlmodel import Session, select
from app.database import get_session
from app.models import NutritionalAnalysis, AllergenDetection, Allergen, FoodImage, AnalysisStatus
from app.ai_client import get_ai_client


class NutritionAnalysisService:
    """Service for analyzing food images and extracting nutritional information."""

    def __init__(self):
        self.ai_client = get_ai_client()

    def analyze_food_image(self, food_image_id: int) -> Optional[NutritionalAnalysis]:
        """
        Analyze a food image using AI and create nutritional analysis.
        Returns the analysis record or None if failed.
        """
        with get_session() as session:
            # Get the food image
            food_image = session.get(FoodImage, food_image_id)
            if not food_image:
                return None

            # Create initial analysis record
            analysis = NutritionalAnalysis(
                food_image_id=food_image_id, status=AnalysisStatus.PROCESSING, ai_model_used="food-vision-ai"
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)

            try:
                start_time = time.time()

                # Analyze the image using DBRX
                analysis_result = self._analyze_with_ai(food_image.file_path)

                processing_time = int((time.time() - start_time) * 1000)

                if analysis_result:
                    # Update analysis with results
                    self._update_analysis_with_results(session, analysis, analysis_result, processing_time)

                    # Create allergen detections
                    self._create_allergen_detections(session, analysis, analysis_result.get("allergens", []))

                    analysis.status = AnalysisStatus.COMPLETED
                else:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = "Failed to analyze image with AI"

                analysis.processing_time_ms = processing_time
                session.commit()
                session.refresh(analysis)

                return analysis

            except Exception as e:
                import logging

                logging.info(f"Error analyzing food image {food_image_id}: {str(e)}")
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)[:1000]
                session.commit()
                session.refresh(analysis)
                return analysis

    def _analyze_with_ai(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Use AI client to analyze the food image."""
        # Read image as base64
        import base64

        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode()
        except Exception as e:
            import logging

            logging.info(f"Error reading image file {image_path}: {e}")
            return None

        try:
            return self.ai_client.analyze_food_image(image_data)
        except Exception as e:
            import logging

            logging.info(f"Error analyzing image with AI: {e}")
            return None

    def _update_analysis_with_results(
        self, session: Session, analysis: NutritionalAnalysis, result: Dict[str, Any], processing_time: int
    ) -> None:
        """Update analysis record with AI results."""
        analysis.food_items = result.get("food_items", [])
        analysis.confidence_score = Decimal(str(result.get("confidence_score", 0.0)))

        nutrition = result.get("nutritional_info", {})
        analysis.calories = Decimal(str(nutrition.get("calories", 0))) if nutrition.get("calories") else None
        analysis.protein_g = Decimal(str(nutrition.get("protein_g", 0))) if nutrition.get("protein_g") else None
        analysis.carbohydrates_g = (
            Decimal(str(nutrition.get("carbohydrates_g", 0))) if nutrition.get("carbohydrates_g") else None
        )
        analysis.total_fat_g = Decimal(str(nutrition.get("total_fat_g", 0))) if nutrition.get("total_fat_g") else None
        analysis.saturated_fat_g = (
            Decimal(str(nutrition.get("saturated_fat_g", 0))) if nutrition.get("saturated_fat_g") else None
        )
        analysis.fiber_g = Decimal(str(nutrition.get("fiber_g", 0))) if nutrition.get("fiber_g") else None
        analysis.sugar_g = Decimal(str(nutrition.get("sugar_g", 0))) if nutrition.get("sugar_g") else None
        analysis.sodium_mg = Decimal(str(nutrition.get("sodium_mg", 0))) if nutrition.get("sodium_mg") else None

        portion_g = result.get("estimated_portion_g")
        if portion_g and analysis.calories:
            analysis.estimated_portion_g = Decimal(str(portion_g))
            analysis.total_calories = (analysis.calories * analysis.estimated_portion_g) / Decimal("100")

        analysis.vitamins = result.get("vitamins", {})
        analysis.minerals = result.get("minerals", {})
        analysis.processing_time_ms = processing_time

    def _create_allergen_detections(
        self, session: Session, analysis: NutritionalAnalysis, detected_allergens: List[Dict[str, Any]]
    ) -> None:
        """Create allergen detection records."""
        for allergen_data in detected_allergens:
            allergen_name = allergen_data.get("name", "").lower().strip()
            if not allergen_name:
                continue

            # Get or create allergen
            stmt = select(Allergen).where(Allergen.name == allergen_name)
            allergen = session.exec(stmt).first()

            if not allergen:
                allergen = Allergen(
                    name=allergen_name, description=f"Common allergen: {allergen_name}", severity_level="moderate"
                )
                session.add(allergen)
                session.commit()
                session.refresh(allergen)

            # Create detection record
            if analysis.id and allergen.id:
                detection = AllergenDetection(
                    nutritional_analysis_id=analysis.id,
                    allergen_id=allergen.id,
                    confidence_score=Decimal(str(allergen_data.get("confidence", 0.5))),
                    detected_in=allergen_data.get("detected_in"),
                )
                session.add(detection)

        session.commit()

    def get_analysis_with_allergens(
        self, analysis_id: int
    ) -> Optional[Tuple[NutritionalAnalysis, List[AllergenDetection]]]:
        """Get analysis with associated allergen detections."""
        with get_session() as session:
            analysis = session.get(NutritionalAnalysis, analysis_id)
            if not analysis:
                return None

            stmt = select(AllergenDetection).where(AllergenDetection.nutritional_analysis_id == analysis_id)
            allergen_detections = session.exec(stmt).all()

            # Load allergen data
            for detection in allergen_detections:
                allergen = session.get(Allergen, detection.allergen_id)
                if allergen:
                    detection.allergen = allergen

            return analysis, list(allergen_detections)

    def get_recent_analyses(self, limit: int = 10) -> List[NutritionalAnalysis]:
        """Get recent nutritional analyses."""
        with get_session() as session:
            stmt = select(NutritionalAnalysis).limit(limit)
            return list(session.exec(stmt).all())
