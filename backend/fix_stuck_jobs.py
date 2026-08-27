from app.core.database import SessionLocal
from app.investigation_ai.models import InvestigationAnalysisJob, InvestigationMedia
from sqlalchemy import update

db = SessionLocal()
try:
    db.execute(
        update(InvestigationAnalysisJob)
        .where(InvestigationAnalysisJob.status.in_(["queued", "processing"]))
        .values(status="failed", error_message="Job failed due to missing cv2/ultralytics dependencies in prior run")
    )
    db.execute(
        update(InvestigationMedia)
        .where(InvestigationMedia.status.in_(["queued", "processing"]))
        .values(status="failed")
    )
    db.commit()
    print("Fixed stuck jobs!")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
