import os
import sys
import pytest
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import database
from models import Base
from app import app
import auth_service

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    """
    Configure isolated temporary SQLite database for all test runs.
    Guarantees 0 pollution of dev or production databases.
    """
    temp_dir = tmp_path_factory.mktemp("db")
    test_db_path = str(temp_dir / "test_tracker.db")
    
    from config import settings
    settings.DB_PATH = test_db_path
    database.DB_PATH = test_db_path
    database.DB_URL = f"sqlite:///{test_db_path}"
    
    # Re-bind engine and session factory to test database
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    database.engine = create_engine(database.DB_URL, connect_args={"check_same_thread": False})
    database.SessionFactory = sessionmaker(bind=database.engine, expire_on_commit=False)
    
    database.init_db()
    yield

@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client

@pytest.fixture
def test_user(client):
    """Create and return a clean test user fixture with JWT token."""
    username = "pytest_runner"
    pwd_hash = auth_service.hash_user_password("TestSecretPass123!")
    
    user = database.get_user_by_username(username)
    if not user:
        user = database.create_user(username, pwd_hash)
    
    token = auth_service.create_access_token(user["id"], user["username"])
    return {
        "id": user["id"],
        "username": user["username"],
        "token": token,
        "auth_headers": {"Authorization": f"Bearer {token}"}
    }

@pytest.fixture
def second_user(client):
    """Second user fixture to verify multi-user isolation."""
    username = "second_user_isolated"
    pwd_hash = auth_service.hash_user_password("SecondSecretPass123!")
    
    user = database.get_user_by_username(username)
    if not user:
        user = database.create_user(username, pwd_hash)
    
    token = auth_service.create_access_token(user["id"], user["username"])
    return {
        "id": user["id"],
        "username": user["username"],
        "token": token,
        "auth_headers": {"Authorization": f"Bearer {token}"}
    }
