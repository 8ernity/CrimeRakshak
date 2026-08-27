from app.core.database import SessionLocal
from app.investigation_ai.processors.crime_detection_analyzer import CrimeDetectionAnalyzer
from app.investigation_ai.models import DetectionResult, InvestigationMedia

db = SessionLocal()
media = db.query(InvestigationMedia).filter_by(media_id=16).first()
dets = db.query(DetectionResult).filter_by(media_id=16).all()
dets_dict = [d.__dict__ for d in dets]
analyzer = CrimeDetectionAnalyzer()
crime_detection = analyzer.analyze_video_evidence(detections=dets_dict, events=[], is_video=False, media_id=16)

print(crime_detection)
