import pytest

def test_add_entry_success(client, test_user):
    res = client.post("/api/entries", headers=test_user["auth_headers"], json={
        "date": "2026-08-10",
        "weight": 182.5,
        "steps": 10500,
        "notes": "Morning jog around the lake"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert data["entry"]["date"] == "2026-08-10"
    assert data["entry"]["weight"] == 182.5
    assert data["entry"]["steps"] == 10500

def test_upsert_entry_same_date(client, test_user):
    # Upsert with new weight on the same date updates the existing record
    res = client.post("/api/entries", headers=test_user["auth_headers"], json={
        "date": "2026-08-10",
        "weight": 181.8,
        "steps": 12000,
        "notes": "Updated evening weigh-in"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["entry"]["weight"] == 181.8
    assert data["entry"]["steps"] == 12000

def test_get_entries_list(client, test_user):
    res = client.get("/api/entries", headers=test_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) >= 1

def test_multi_user_data_isolation(client, test_user, second_user):
    # Test User 1 logs 205.5 lbs on 2026-08-15
    client.post("/api/entries", headers=test_user["auth_headers"], json={
        "date": "2026-08-15",
        "weight": 205.5,
        "steps": 8000
    })

    # Test User 2 logs 145.0 lbs on 2026-08-15
    client.post("/api/entries", headers=second_user["auth_headers"], json={
        "date": "2026-08-15",
        "weight": 145.0,
        "steps": 15000
    })

    # User 1 queries entries: must ONLY see 205.5 lbs
    res_1 = client.get("/api/entries", headers=test_user["auth_headers"])
    u1_entry = next((e for e in res_1.get_json()["entries"] if e["date"] == "2026-08-15"), None)
    assert u1_entry is not None
    assert u1_entry["weight"] == 205.5

    # User 2 queries entries: must ONLY see 145.0 lbs
    res_2 = client.get("/api/entries", headers=second_user["auth_headers"])
    u2_entry = next((e for e in res_2.get_json()["entries"] if e["date"] == "2026-08-15"), None)
    assert u2_entry is not None
    assert u2_entry["weight"] == 145.0

def test_update_entry_by_id(client, test_user):
    # Create entry to update
    res_create = client.post("/api/entries", headers=test_user["auth_headers"], json={
        "date": "2026-08-16",
        "weight": 180.0,
        "steps": 9000
    })
    entry_id = res_create.get_json()["entry"]["id"]

    res_update = client.put(f"/api/entries/{entry_id}", headers=test_user["auth_headers"], json={
        "date": "2026-08-16",
        "weight": 179.5,
        "steps": 9500,
        "notes": "Fast walk"
    })
    assert res_update.status_code == 200
    assert res_update.get_json()["entry"]["weight"] == 179.5

def test_delete_entry(client, test_user):
    res_create = client.post("/api/entries", headers=test_user["auth_headers"], json={
        "date": "2026-08-17",
        "weight": 178.0
    })
    entry_id = res_create.get_json()["entry"]["id"]

    res_del = client.delete(f"/api/entries/{entry_id}", headers=test_user["auth_headers"])
    assert res_del.status_code == 200
    assert res_del.get_json()["success"] is True

def test_entry_validation_errors(client, test_user):
    # Invalid date format
    res = client.post("/api/entries", headers=test_user["auth_headers"], json={
        "date": "08-10-2026", # Not YYYY-MM-DD
        "weight": 180.0
    })
    assert res.status_code == 400
