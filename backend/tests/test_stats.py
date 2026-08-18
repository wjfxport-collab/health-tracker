import pytest
from datetime import datetime, timedelta
import database
import auth_service

def test_stats_zero_state(client):
    # Brand new clean user with exactly 0 entries
    clean_username = "stats_zero_user"
    pwd_hash = auth_service.hash_user_password("Pass123!")
    user = database.create_user(clean_username, pwd_hash)
    token = auth_service.create_access_token(user["id"], user["username"])
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/stats", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    stats = data["stats"]
    assert stats["total_days_logged"] == 0
    assert stats["today_steps"] == 0
    assert stats["current_step_streak"] == 0

def test_stats_averages_and_streaks(client):
    streak_username = "stats_streak_user"
    pwd_hash = auth_service.hash_user_password("Pass123!")
    user = database.create_user(streak_username, pwd_hash)
    token = auth_service.create_access_token(user["id"], user["username"])
    headers = {"Authorization": f"Bearer {token}"}

    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10)]

    # Populate 10 consecutive days with 15,000 steps (goal is default 10,000)
    for i, d in enumerate(dates):
        database.upsert_entry(
            user_id=user["id"],
            date_str=d,
            weight=185.0 - (i * 0.5),
            steps=15000 + (i * 100)
        )

    res = client.get("/api/stats", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    stats = data["stats"]

    assert stats["total_days_logged"] >= 10
    assert stats["avg_steps_7d"] >= 15000
    assert stats["current_step_streak"] >= 10
    assert stats["best_step_day"] >= 15900
    assert stats["latest_weight"] is not None
