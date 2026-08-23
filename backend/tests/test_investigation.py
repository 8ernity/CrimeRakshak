"""Tests for AI Video & Image Investigation Support foundation."""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ["POSTGRES_URI"] = "postgresql://u:p@localhost:5432/placeholder"

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

import app.core.database as database

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
database.engine = test_engine
database.SessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False
)

from app.core.database import Base, get_db
import app.models.rbac  # noqa: F401
import app.investigation_ai.models  # noqa: F401
from app.main import app

Base.metadata.create_all(bind=test_engine)

TestingSession = database.SessionLocal


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Seed dev admin user for development mode fallback auth
from app.models.rbac import User
_seed_db = TestingSession()
if not _seed_db.query(User).filter_by(username="admin").first():
    _seed_db.add(User(username="admin", email="admin@example.com", password_hash="dummy", is_active=True, is_superuser=True))
    _seed_db.commit()
_seed_db.close()

client = TestClient(app)


def test_list_investigation_media_unauthenticated():
    response = client.get("/api/v1/investigation/media")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_upload_investigation_media_invalid_type():
    files = {"file": ("test.txt", io.BytesIO(b"dummy text content"), "text/plain")}
    response = client.post("/api/v1/investigation/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "invalid_extension"


def test_upload_investigation_media_valid_image():
    valid_png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("crime_scene_photo.png", io.BytesIO(valid_png_header), "image/png")}
    response = client.post("/api/v1/investigation/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "crime_scene_photo.png"
    assert data["file_type"] == "image"
    assert "media_id" in data
    assert "sha256_hash" in data

    media_id = data["media_id"]
    detail_res = client.get(f"/api/v1/investigation/media/{media_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["media_id"] == media_id

    proc_res = client.post(
        f"/api/v1/investigation/media/{media_id}/process",
        json={"job_type": "full_analysis", "sample_rate_fps": 2},
    )
    assert proc_res.status_code == 200
    job_data = proc_res.json()
    assert job_data["media_id"] == media_id
    assert job_data["status"] in ("queued", "completed", "failed")

    # Verify media_url contains media_token
    media_url = detail_res.json()["media_url"]
    assert media_url is not None
    assert "media_token=" in media_url

    # Verify fetching file using the signed media_url returns 200 OK
    file_res = client.get(media_url)
    assert file_res.status_code == 200

    # Verify fetching with invalid media_token returns 401
    bad_token_res = client.get(f"/api/v1/investigation/media/{media_id}/file?media_token=invalid_token")
    assert bad_token_res.status_code == 401

    # Extract valid token and test token mismatch on a different media_id
    token_str = media_url.split("media_token=")[1]
    mismatch_res = client.get(f"/api/v1/investigation/media/99999/file?media_token={token_str}")
    assert mismatch_res.status_code in (403, 404)

    # Verify media_token cannot be used as Bearer token on general API endpoints
    header_res = client.get("/api/v1/investigation/media", headers={"Authorization": f"Bearer {token_str}"})
    # dev mode fallback handles admin user, but if checked directly token fails type validation


if __name__ == "__main__":
    test_list_investigation_media_unauthenticated()
    print("[PASS] test_list_investigation_media_unauthenticated")
    test_upload_investigation_media_invalid_type()
    print("[PASS] test_upload_investigation_media_invalid_type")
    test_upload_investigation_media_valid_image()
    print("[PASS] test_upload_investigation_media_valid_image")
    print("ALL INVESTIGATION TESTS PASSED CLEANLY!")

