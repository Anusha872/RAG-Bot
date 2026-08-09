import pytest
from app.core.database import init_db, Base, engine


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure clean database tables before each test execution."""
    Base.metadata.drop_all(bind=engine)
    init_db()

