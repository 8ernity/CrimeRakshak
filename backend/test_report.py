import json
from app.core.database import SessionLocal
from app.investigation_ai.services import get_ai_investigation_report, get_investigation_summary
from app.models.rbac import User

db = SessionLocal()
user = db.query(User).first()

print("Testing summary...")
summary = get_investigation_summary(db=db, media_id=14, user=user)
print("Summary object:", summary.summary_text)

print("Testing report...")
report = get_ai_investigation_report(db=db, media_id=14, user=user)
print("Report keys:", report.keys())
print(json.dumps(report, indent=2))
