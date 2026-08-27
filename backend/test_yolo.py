import cv2
from ultralytics import YOLO

# load image
img_path = r"d:\Projects\CrimeRakshak\backend\storage\investigation\uploads\af92110d353d9fa4_WhatsApp Image 2026-08-25 at 5.07.59 PM.jpeg"
model = YOLO('yolov8n.pt')

results = model(img_path)
print("Detected boxes:", len(results[0].boxes))
for box in results[0].boxes:
    cls_id = int(box.cls[0].item())
    conf = box.conf[0].item()
    name = model.names[cls_id]
    print(f"Detected {name} with conf {conf}")
