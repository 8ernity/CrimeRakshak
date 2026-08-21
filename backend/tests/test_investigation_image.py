"""Unit tests for YOLO Image Analysis in AI Investigation Support module."""
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
from app.models.rbac import User
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

# Seed admin user for development mode auth fallback
_seed_db = TestingSession()
if not _seed_db.query(User).filter_by(username="admin").first():
    _seed_db.add(User(username="admin", email="admin@example.com", password_hash="dummy", is_active=True, is_superuser=True))
    _seed_db.commit()
_seed_db.close()

client = TestClient(app)


def test_analyze_image_invalid_extension():
    files = {"file": ("document.pdf", io.BytesIO(b"%PDF-1.4 dummy content"), "application/pdf")}
    response = client.post("/api/v1/investigation/analyze-image", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "invalid_extension"


def test_analyze_image_success():
    # Generate a small valid PNG image using PIL
    from PIL import Image
    img_byte_arr = io.BytesIO()
    img = Image.new("RGB", (300, 300), color="blue")
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    files = {"file": ("street_scene.png", io.BytesIO(img_bytes), "image/png")}
    data_form = {"fir_id": "FIR-2026-IMAGE01", "confidence_threshold": "0.1"}

    response = client.post("/api/v1/investigation/analyze-image", files=files, data=data_form)
    assert response.status_code == 200, f"Response text: {response.text}"

    data = response.json()
    assert "media" in data
    assert "job" in data
    assert data["media"]["file_name"] == "street_scene.png"
    assert data["media"]["file_type"] == "image"
    assert data["job"]["status"] == "completed"
    assert data["image_width"] == 300
    assert data["image_height"] == 300
    assert isinstance(data["detections"], list)
    assert "total_detected_objects" in data


def test_analyze_existing_image_media():
    from PIL import Image
    img_byte_arr = io.BytesIO()
    img = Image.new("RGB", (200, 200), color="red")
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    upload_res = client.post(
        "/api/v1/investigation/upload",
        files={"file": ("evidence.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )
    assert upload_res.status_code == 200
    media_id = upload_res.json()["media_id"]

    analyze_res = client.post(f"/api/v1/investigation/media/{media_id}/analyze-image")
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["media"]["media_id"] == media_id
    assert data["job"]["status"] == "completed"


if __name__ == "__main__":
    test_analyze_image_invalid_extension()
    print("[PASS] test_analyze_image_invalid_extension")
    test_analyze_image_success()
    print("[PASS] test_analyze_image_success")
    test_analyze_existing_image_media()
    print("[PASS] test_analyze_existing_image_media")
    print("ALL IMAGE ANALYSIS TESTS PASSED CLEANLY!")
