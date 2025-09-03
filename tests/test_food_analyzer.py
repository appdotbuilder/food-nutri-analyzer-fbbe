import pytest
from app.services.user_service import UserService
from app.services.nutrition_service import NutritionAnalysisService
from app.ai_client import get_ai_client
from app.models import UserCreate
from app.database import reset_db


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


def test_ai_client_works():
    """Test that the AI client can analyze images."""
    client = get_ai_client()
    result = client.analyze_food_image("fake_image_data")

    assert result is not None
    assert "food_items" in result
    assert "confidence_score" in result
    assert "nutritional_info" in result


def test_user_service_basic_operations(new_db):
    """Test basic user service operations."""
    service = UserService()

    # Create user
    user_data = UserCreate(name="John Doe", email="john@example.com")
    user = service.create_user(user_data)

    assert user.id is not None
    assert user.name == "John Doe"
    assert user.email == "john@example.com"

    # Get user by email
    retrieved = service.get_user_by_email("john@example.com")
    assert retrieved is not None
    assert retrieved.id == user.id

    # Test get_or_create with existing user
    user2 = service.get_or_create_user("john@example.com", "Different Name")
    assert user2.id == user.id
    assert user2.name == "John Doe"  # Should keep original


def test_nutrition_service_initialization(new_db):
    """Test nutrition service can be created."""
    service = NutritionAnalysisService()
    assert service.ai_client is not None


def test_mime_type_detection():
    """Test MIME type detection utility."""
    service = UserService()

    assert service._get_mime_type("test.jpg") == "image/jpeg"
    assert service._get_mime_type("test.png") == "image/png"
    assert service._get_mime_type("test.webp") == "image/webp"
    assert service._get_mime_type("unknown.xyz") == "image/jpeg"  # Default
