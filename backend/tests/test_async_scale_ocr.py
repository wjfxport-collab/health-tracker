import io
import time
import pytest
from unittest.mock import patch
import ocr_service
import database

def test_async_scale_upload_endpoint_returns_202(client, test_user):
    dummy_img = io.BytesIO(b"FakeJPEGDataForTest")
    res = client.post(
        "/api/upload-scale-photo/async",
        headers=test_user["auth_headers"],
        data={"photo": (dummy_img, "test_scale.jpg")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 202
    data = res.get_json()
    assert data["success"] is True
    assert "job_id" in data
    assert data["status"] == "processing"

def test_async_ocr_worker_success_mock(client, test_user):
    mock_gemini_resp = {
        "success": True,
        "weight": 208.4,
        "unit": "lbs",
        "confidence": 98,
        "notes": "Aqua LCD display reading 208.4 lbs",
        "engine": "gemini-flash-latest"
    }

    job_id = database.create_scale_upload_job(test_user["id"])

    with patch("gemini_service.parse_scale_with_gemini", return_value=mock_gemini_resp):
        with patch("ocr_service.extract_exif_timestamp", return_value=("2026-08-18", "08:30 AM", "2026:08:18 08:30:00")):
            # Run worker synchronously for testing
            ocr_service._run_async_worker(test_user["id"], job_id, "/tmp/mock_scale_valid.jpg", "fake_key")

    jobs = database.get_active_scale_upload_jobs(test_user["id"])
    target_job = next((j for j in jobs if j["id"] == job_id), None)
    assert target_job is not None
    assert target_job["status"] == "completed"
    assert target_job["weight"] == 208.4

    entry = database.get_entry_by_date(test_user["id"], "2026-08-18")
    assert entry is not None
    assert entry["weight"] == 208.4

def test_async_ocr_worker_unreadable_scale_mock(client, test_user):
    mock_fail_resp = {
        "success": False,
        "error": "Scale reading was not legible due to reflection.",
        "engine": "gemini-error"
    }

    job_id = database.create_scale_upload_job(test_user["id"])

    with patch("gemini_service.parse_scale_with_gemini", return_value=mock_fail_resp):
        with patch("ocr_service.extract_exif_timestamp", return_value=(None, None, None)):
            ocr_service._run_async_worker(test_user["id"], job_id, "/tmp/mock_scale_blurry.jpg", "fake_key")

    jobs = database.get_active_scale_upload_jobs(test_user["id"])
    target_job = next((j for j in jobs if j["id"] == job_id), None)
    assert target_job is not None
    assert target_job["status"] == "failed"
    assert "not legible" in target_job["error"]

def test_dismiss_scale_upload_job(client, test_user):
    job_id = database.create_scale_upload_job(test_user["id"])
    database.update_scale_upload_job(job_id, status="failed", error="Blurry photo")

    res = client.post(f"/api/upload-scale-photo/jobs/{job_id}/dismiss", headers=test_user["auth_headers"])
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    jobs = database.get_active_scale_upload_jobs(test_user["id"])
    assert not any(j["id"] == job_id for j in jobs)
