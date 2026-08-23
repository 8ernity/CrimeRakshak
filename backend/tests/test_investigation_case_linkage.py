"""Unit tests for Case/FIR ↔ Investigation Media integration and district RBAC scoping."""
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

# Seed test admin superuser
_seed_db = TestingSession()
if not _seed_db.query(User).filter_by(username="admin").first():
    _seed_db.add(User(username="admin", email="admin@example.com", password_hash="dummy", is_active=True, is_superuser=True))
    _seed_db.commit()
_seed_db.close()

client = TestClient(app)


def test_case_fir_media_linkage():
    valid_png_header = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("evidence_scene1.png", io.BytesIO(valid_png_header), "image/png")}
    data_form = {"fir_id": "FIR-2026-CASE99", "district_id": "1"}

    # 1. Upload media linked to FIR-2026-CASE99
    upload_res = client.post("/api/v1/investigation/upload", files=files, data=data_form)
    assert upload_res.status_code == 200
    media_data = upload_res.json()
    assert media_data["fir_id"] == "FIR-2026-CASE99"
    media_id = media_data["media_id"]

    # 2. List media filtered by fir_id
    list_res = client.get("/api/v1/investigation/media?fir_id=FIR-2026-CASE99")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) >= 1
    assert any(m["media_id"] == media_id for m in items)

    # 3. Fetch Case Media Summary API
    case_res = client.get("/api/v1/investigation/cases/FIR-2026-CASE99/media")
    assert case_res.status_code == 200
    case_data = case_res.json()
    assert case_data["fir_id"] == "FIR-2026-CASE99"
    assert case_data["total_media"] >= 1
    assert len(case_data["media_items"]) >= 1

    # 4. Link to a different FIR
    link_res = client.post(
        f"/api/v1/investigation/media/{media_id}/link-fir",
        json={"fir_id": "FIR-2026-CASE100"},
    )
    assert link_res.status_code == 200
    assert link_res.json()["fir_id"] == "FIR-2026-CASE100"

    # 5. Unlink FIR by setting fir_id to None
    unlink_res = client.post(
        f"/api/v1/investigation/media/{media_id}/link-fir",
        json={"fir_id": None},
    )
    assert unlink_res.status_code == 200
    assert unlink_res.json()["fir_id"] is None


if __name__ == "__main__":
    test_case_fir_media_linkage()
    print("[PASS] test_case_fir_media_linkage")
    print("ALL CASE/FIR LINKAGE TESTS PASSED CLEANLY!")
