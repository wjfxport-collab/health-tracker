import pytest
import json
from plugin_engine import plugin_engine

def test_plugin_discovery_and_manifest_loading(client):
    res = client.get("/api/plugins")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    
    plugin_ids = [p["id"] for p in data["plugins"]]
    assert "weight" in plugin_ids
    assert "steps" in plugin_ids
    assert "camera_log" in plugin_ids

def test_camera_log_manifest_fields(client):
    manifest = plugin_engine.get_plugin("camera_log")
    assert manifest is not None
    assert manifest["name"] == "Camera & Lens Gear Log"
    assert manifest["category"] == "equipment"
    
    field_ids = [f["id"] for f in manifest["fields"]]
    assert "camera_body" in field_ids
    assert "lens" in field_ids
    assert "timedate_of_use" in field_ids
    assert "focal_length" in field_ids
    assert "aperture" in field_ids
    assert "comment" in field_ids

def test_camera_log_payload_validation_success(client, test_user):
    payload = {
        "camera_body": "Sony A7 IV",
        "lens": "FE 24-70mm f/2.8 GM II",
        "timedate_of_use": "2026-08-18T14:30",
        "focal_length": 50,
        "aperture": "f/2.8",
        "iso": 400,
        "shutter_speed": "1/500s",
        "comment": "Golden hour portrait shoot outdoors"
    }

    res = client.post(
        "/api/metrics/camera_log/entries",
        headers=test_user["auth_headers"],
        json={
            "date": "2026-08-18",
            "payload": payload,
            "notes": "Outdoor session"
        }
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    entry = data["entry"]
    assert entry["metric_id"] == "camera_log"
    assert entry["payload"]["camera_body"] == "Sony A7 IV"
    assert entry["payload"]["lens"] == "FE 24-70mm f/2.8 GM II"
    assert entry["payload"]["focal_length"] == 50

def test_camera_log_missing_required_field(client, test_user):
    # Missing required 'lens'
    payload = {
        "camera_body": "Sony A7 IV",
        "timedate_of_use": "2026-08-18T14:30"
    }
    res = client.post(
        "/api/metrics/camera_log/entries",
        headers=test_user["auth_headers"],
        json={"date": "2026-08-18", "payload": payload}
    )
    assert res.status_code == 400
    assert "required" in res.get_json()["error"].lower()

def test_camera_log_stats_and_aggregations(client, test_user):
    sessions = [
        {"camera_body": "Sony A7 IV", "lens": "50mm f/1.2", "timedate_of_use": "2026-08-16T10:00"},
        {"camera_body": "Sony A7 IV", "lens": "24-70mm f/2.8", "timedate_of_use": "2026-08-17T11:00"},
        {"camera_body": "Canon EOS R5", "lens": "85mm f/1.4", "timedate_of_use": "2026-08-18T12:00"}
    ]

    for i, s in enumerate(sessions):
        client.post(
            "/api/metrics/camera_log/entries",
            headers=test_user["auth_headers"],
            json={"date": f"2026-08-1{6+i}", "payload": s}
        )

    res = client.get("/api/metrics/camera_log/stats", headers=test_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    stats = data["stats"]

    assert stats["total_sessions"] >= 3
    assert stats["top_camera"] == "Sony A7 IV"
    assert stats["latest_session"]["camera_body"] is not None

def test_all_metrics_summary_endpoint(client, test_user):
    res = client.get("/api/metrics/summary", headers=test_user["auth_headers"])
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    summary = data["summary"]

    assert "weight" in summary
    assert "steps" in summary
    assert "camera_log" in summary
    assert "stats" in summary["camera_log"]
