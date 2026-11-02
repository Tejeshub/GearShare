import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.db.dependencies import get_db
from app.db.seed import seed_database
from app.db.seed_inventory import seed_inventory
# Import models to register them on Base.metadata
import app.models  # noqa: F401
from app.main import create_application

# Use an in-memory SQLite database for unit tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def get_test_settings() -> Settings:
    return Settings(
        APP_NAME="GearShare API Test",
        APP_ENV="test",
        DEBUG=True,
        DATABASE_URL=TEST_DATABASE_URL,
        ALLOWED_ORIGINS="*",
        ADMIN_API_KEY="test-admin-secret-key",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db_session():
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def seeded_db(db_session):
    """Provides a database session pre-populated with catalogue seed data."""
    seed_database(db_session)
    return db_session


@pytest.fixture
def inventory_seeded_db(seeded_db):
    """Provides a database session pre-populated with catalogue AND physical inventory seed data."""
    seed_inventory(seeded_db)
    return seeded_db


@pytest.fixture
def client(db_session):
    app = create_application()
    app.dependency_overrides[get_settings] = get_test_settings
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app, headers={"X-Admin-Key": "test-admin-secret-key"}) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(seeded_db):
    app = create_application()
    app.dependency_overrides[get_settings] = get_test_settings
    app.dependency_overrides[get_db] = lambda: seeded_db

    with TestClient(app, headers={"X-Admin-Key": "test-admin-secret-key"}) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def inventory_client(inventory_seeded_db):
    app = create_application()
    app.dependency_overrides[get_settings] = get_test_settings
    app.dependency_overrides[get_db] = lambda: inventory_seeded_db

    with TestClient(app, headers={"X-Admin-Key": "test-admin-secret-key"}) as test_client:
        yield test_client

    app.dependency_overrides.clear()
