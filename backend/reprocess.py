import sys
from app.core.database import SessionLocal
from app.investigation_ai.models import DetectionResult, InvestigationCrimeDecision, InvestigationMedia, InvestigationAnalysisJob
import app.investigation_ai.services as services

db = SessionLocal()
media = db.query(InvestigationMedia).filter(InvestigationMedia.media_id == 16).first()
if not media:
    print("Media 16 not found")
    sys.exit(0)

print(f"Found media 16: {media.file_name}")

# Delete old detections
db.query(DetectionResult).filter(DetectionResult.media_id == 16).delete()
# Delete old decisions
db.query(InvestigationCrimeDecision).filter(InvestigationCrimeDecision.media_id == 16).delete()
# Delete old jobs
db.query(InvestigationAnalysisJob).filter(InvestigationAnalysisJob.media_id == 16).delete()

# Reset media status
media.status = 'uploaded'
db.commit()
print("Reset media 16. Now processing...")

# Create a fake job
job = InvestigationAnalysisJob(media_id=media.media_id, status="processing")
db.add(job)
db.commit()

from app.investigation_ai.processors.image_processor import ImageProcessor
processor = ImageProcessor()
results = processor.process_image(media.file_path)

print(f"Found {len(results.get('detections', []))} detections in image processor!")

for det in results.get("detections", []):
    bbox = det["bbox"]
    detection_rec = DetectionResult(
        job_id=job.job_id,
        media_id=media.media_id,
        frame_number=0,
        timestamp_seconds=0.0,
        object_class=det["object_class"],
        tracking_id=det.get("tracking_id"),
        confidence=det["confidence"],
        bbox_xmin=bbox["xmin"],
        bbox_ymin=bbox["ymin"],
        bbox_xmax=bbox["xmax"],
        bbox_ymax=bbox["ymax"],
    )
    db.add(detection_rec)

job.status = "completed"
job.progress_pct = 100.0
media.status = "processed"
db.commit()

try:
    # also call event extraction
    services.extract_events_for_media(db=db, media_id=media.media_id, user=None, job_id=job.job_id, ip_address="127.0.0.1")
except Exception as e:
    print("Event extraction error:", e)

print("Done processing media 16.")
