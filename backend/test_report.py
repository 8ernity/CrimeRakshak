import json
from app.core.database import SessionLocal
from app.core.database import SessionLocal
from app.investigation_ai.services import get_ai_investigation_report, get_investigation_summary

db = SessionLocal()

print("Testing summary...")
summary = get_investigation_summary(db=db, media_id=16, user=None)
print("Summary length:", len(str(summary)))

print("Testing report...")
report = get_ai_investigation_report(db=db, media_id=16, user=None)
print("Report keys:", report.keys())
print(json.dumps(report, indent=2))
