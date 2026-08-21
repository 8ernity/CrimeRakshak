"""Unit tests for Video Analysis pipeline in AI Investigation Support module."""
import os
import sys
import tempfile
import cv2
import numpy as np

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


def generate_sample_mp4(num_frames: int = 30, fps: int = 10, width: int = 320, height: int = 240) -> str:
    """Generate a temporary synthetic MP4 video file."""
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, "incident_sample.mp4")
    
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(video_path, fourcc, float(fps), (width, height))
    
    for i in range(num_frames):
        # Create a frame with a colored rectangle moving across
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.rectangle(frame, (10 + i * 5, 20), (60 + i * 5, 80), (0, 255, 0), -1)
        out.write(frame)
        
    out.release()
    return video_path


def test_analyze_video_invalid_format():
    files = {"file": ("malicious_executable.exe", b"MZ dummy binary payload", "application/octet-stream")}
    response = client.post("/api/v1/investigation/analyze-video", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "invalid_extension"


def test_analyze_video_success():
    video_path = generate_sample_mp4(num_frames=30, fps=10, width=320, height=240)
    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        files = {"file": ("traffic_cam_01.mp4", video_bytes, "video/mp4")}
        data_form = {
            "fir_id": "FIR-2026-VIDEO-001",
            "sample_rate_fps": "2",
            "confidence_threshold": "0.1",
        }

        response = client.post("/api/v1/investigation/analyze-video", files=files, data=data_form)
        assert response.status_code == 200, f"Response text: {response.text}"

        data = response.json()
        assert "media" in data
        assert "job" in data
        assert "video_metadata" in data
        assert data["media"]["file_name"] == "traffic_cam_01.mp4"
        assert data["media"]["file_type"] == "video"
        assert data["job"]["status"] == "completed"

        v_meta = data["video_metadata"]
        assert v_meta["fps"] == 10.0
        assert v_meta["total_frames"] == 30
        assert v_meta["duration_seconds"] == 3.0
        assert v_meta["width"] == 320
        assert v_meta["height"] == 240
        assert v_meta["sample_rate_fps"] == 2
        assert v_meta["sampled_frames_count"] > 0
        assert isinstance(data["detections"], list)

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


def test_analyze_existing_video_media():
    video_path = generate_sample_mp4(num_frames=20, fps=10, width=320, height=240)
    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        upload_res = client.post(
            "/api/v1/investigation/upload",
            files={"file": ("cctv_footage.mp4", video_bytes, "video/mp4")},
        )
        assert upload_res.status_code == 200
        media_id = upload_res.json()["media_id"]

        analyze_res = client.post(
            f"/api/v1/investigation/media/{media_id}/analyze-video?sample_rate_fps=2&confidence_threshold=0.1"
        )
        assert analyze_res.status_code == 200
        data = analyze_res.json()
        assert data["media"]["media_id"] == media_id
        assert data["job"]["status"] == "completed"
        assert data["video_metadata"]["total_frames"] == 20
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


if __name__ == "__main__":
    test_analyze_video_invalid_format()
    print("[PASS] test_analyze_video_invalid_format")
    test_analyze_video_success()
    print("[PASS] test_analyze_video_success")
    test_analyze_existing_video_media()
    print("[PASS] test_analyze_existing_video_media")
    print("ALL VIDEO ANALYSIS TESTS PASSED CLEANLY!")
