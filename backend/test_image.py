import os
import sys

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.investigation_ai.processors.image_processor import ImageProcessor
from app.investigation_ai.services import get_media_by_id
from app.investigation_ai.models import DetectionResult, InvestigationCrimeDecision
from app.core.models import Media
import json

db = SessionLocal()
media = db.query(Media).filter(Media.file_name.like("%WhatsApp%")).first()

if not media:
    print("No media found")
    sys.exit(0)

print(f"Media ID: {media.media_id}, File path: {media.file_path}")

processor = ImageProcessor()
results = processor.process_image(media.file_path)

print(json.dumps(results, indent=2))
