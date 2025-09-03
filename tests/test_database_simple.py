from app.database import reset_db, get_session
from app.models import User


def test_database_connection():
    """Test basic database connectivity."""
    reset_db()

    # Create a simple user
    with get_session() as session:
        user = User(name="Test", email="test@example.com")
        session.add(user)
        session.commit()

        # Verify user was created
        assert user.id is not None
        assert user.name == "Test"
