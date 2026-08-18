import pytest
from sqlalchemy import select
import database
from models import Goal
import secrets_vault

def test_get_goals_default(client, test_user):
    res = client.get("/api/goals", headers=test_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["goals"]["daily_steps_goal"] == 10000
    assert data["goals"]["target_weight"] == 165.0

def test_update_goals_and_fernet_encryption(client, test_user):
    raw_api_key = "AIzaSyTestSecretEncryptionKey998877"
    
    res = client.post("/api/goals", headers=test_user["auth_headers"], json={
        "daily_steps_goal": 12500,
        "target_weight": 160.0,
        "starting_weight": 185.0,
        "weight_unit": "lbs",
        "gemini_api_key": raw_api_key
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["goals"]["daily_steps_goal"] == 12500
    assert data["goals"]["has_gemini_api_key"] is True
    assert data["goals"]["gemini_api_key_masked"] == "AIzaSy...8877"

    # Inspect raw SQLite database to verify data on disk is Fernet ciphertext
    with database.get_session() as session:
        goal_row = session.scalars(
            select(Goal).where(Goal.user_id == test_user["id"])
        ).first()
        assert goal_row is not None
        # Must start with enc:v1: and NOT contain plaintext
        assert goal_row.gemini_api_key.startswith("enc:v1:")
        assert raw_api_key not in goal_row.gemini_api_key

        # Verify Fernet vault decryption reproduces exact plaintext
        decrypted = secrets_vault.decrypt_secret(goal_row.gemini_api_key)
        assert decrypted == raw_api_key

def test_goal_validation_constraints(client, test_user):
    # Invalid unit (e.g. 'miles')
    res = client.post("/api/goals", headers=test_user["auth_headers"], json={
        "weight_unit": "invalid_unit"
    })
    assert res.status_code == 400
