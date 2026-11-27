import re
import numpy as np


class PlateDetector:
    VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

    def __init__(self):
        self._available = False
        try:
            from ultralytics import YOLO
            import easyocr

            self.model = YOLO("yolov8n.pt")
            self.reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            self._available = True
        except ImportError:
            pass
        except Exception:
            pass

    @property
    def available(self):
        return self._available

    def detect_vehicles(self, frame):
        if not self._available:
            return []
        results = self.model(frame, verbose=False)[0]
        detections = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id in self.VEHICLE_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append(
                    {
                        "bbox": [x1, y1, x2, y2],
                        "class_name": self.VEHICLE_CLASSES[cls_id],
                        "confidence": round(float(box.conf[0]), 3),
                    }
                )
        return detections

    def extract_plate(self, frame, bbox):
        if not self._available:
            return "UNREAD"
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return "UNREAD"
        try:
            ocr_results = self.reader.readtext(crop)
        except Exception:
            return "UNREAD"
        raw = " ".join(r[1] for r in ocr_results)
        cleaned = re.sub(r"[^A-Z0-9\-]", "", raw.upper())
        if 6 <= len(cleaned) <= 12:
            return cleaned
        return "UNREAD"

    def process_frame(self, frame):
        detections = self.detect_vehicles(frame)
        results = []
        for det in detections:
            plate = self.extract_plate(frame, det["bbox"])
            results.append(
                {
                    "plate": plate,
                    "class_name": det["class_name"],
                    "confidence": det["confidence"],
                    "bbox": det["bbox"],
                }
            )
        return results
