import pytest
from app.services.user_service import UserService
from app.services.nutrition_service import NutritionAnalysisService
from app.models import UserCreate
from app.database import reset_db


@pytest.fixture()
def new_db():
    reset_db()
    yield
    reset_db()


def test_user_service_basic(new_db):
    """Test basic user service functionality."""
    user_service = UserService()

    # Test user creation
    user_data = UserCreate(name="Test User", email="test@example.com")
    user = user_service.create_user(user_data)

    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.id is not None

    # Test get by email
    retrieved = user_service.get_user_by_email("test@example.com")
    assert retrieved is not None
    assert retrieved.id == user.id


def test_nutrition_service_initialization(new_db):
    """Test nutrition service can be initialized."""
    service = NutritionAnalysisService()
    assert service.ai_client is not None


def test_get_or_create_user(new_db):
    """Test get_or_create_user functionality."""
    user_service = UserService()

    # First call should create user
    user1 = user_service.get_or_create_user("new@test.com", "New User")
    assert user1.name == "New User"
    assert user1.email == "new@test.com"

    # Second call should return existing user
    user2 = user_service.get_or_create_user("new@test.com", "Different Name")
    assert user2.id == user1.id
    assert user2.name == "New User"  # Should keep original name
