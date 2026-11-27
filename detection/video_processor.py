import cv2
import os
import random
from datetime import datetime
from detection.plate_detector import PlateDetector
from detection.speed_estimator import SpeedEstimator

PANCHAGARH_LOCATIONS = [
    "Station Road, Panchagarh",
    "Thana Road, Panchagarh",
    "College Road, Panchagarh",
    "Hospital Road, Panchagarh",
    "Sadar Road, Panchagarh",
    "DC Office Road, Panchagarh",
    "Boda Road, Panchagarh",
    "Tetulia Highway, Panchagarh",
]


class VideoProcessor:
    def __init__(self, source, session_id, flask_app):
        self.source = source
        self.session_id = session_id
        self.flask_app = flask_app
        self.plate_detector = PlateDetector()
        self.speed_estimator = SpeedEstimator()
        self.running = True
        self.results = []
        self.frame_count = 0
        self.processed_plates = set()
        self.error = None
        self.done = False

    def _save_to_db(self, plate, speed, location, violation, camera_id):
        try:
            with self.flask_app.app_context():
                from models.vehicle import Vehicle
                from database.db import db

                v = Vehicle(
                    plate_number=plate,
                    speed_kmh=speed,
                    location=location,
                    violation_type=violation,
                    camera_id=camera_id,
                    detected_at=datetime.utcnow(),
                )
                db.session.add(v)
                db.session.commit()
        except Exception as exc:
            pass

    def _draw_annotation(self, frame, bbox, plate, speed):
        x1, y1, x2, y2 = bbox
        if speed > 90:
            color = (0, 0, 255)
        elif speed > 60:
            color = (0, 165, 255)
        else:
            color = (0, 220, 80)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"{plate}  {speed} km/h"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
        cv2.putText(
            frame,
            label,
            (x1 + 3, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )

    def process(self, progress_callback=None):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            self.error = "Cannot open video source. Check file or camera."
            self.done = True
            if progress_callback:
                progress_callback({"error": self.error})
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25
        self.speed_estimator.fps = fps

        frame_idx = 0
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            self.frame_count = frame_idx

            if frame_idx % 3 != 0:
                continue

            detections = self.plate_detector.process_frame(frame)

            for det in detections:
                plate = det["plate"]
                bbox = det["bbox"]
                x1, y1, x2, y2 = bbox
                centroid = ((x1 + x2) // 2, (y1 + y2) // 2)

                speed = self.speed_estimator.estimate_speed(plate, centroid, frame_idx)
                if speed is None:
                    speed = self.speed_estimator.get_speed(plate)
                speed = round(max(10.0, min(130.0, speed)), 1)

                self._draw_annotation(frame, bbox, plate, speed)

                if plate not in self.processed_plates and plate != "UNREAD":
                    self.processed_plates.add(plate)
                    violation = "Overspeeding" if speed > 80 else None
                    location = random.choice(PANCHAGARH_LOCATIONS)
                    camera_id = f"VIDEO-{self.session_id[:6].upper()}"

                    result = {
                        "plate": plate,
                        "speed": speed,
                        "violation": violation,
                        "location": location,
                        "camera_id": camera_id,
                        "class_name": det["class_name"],
                        "confidence": det["confidence"],
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    self.results.append(result)
                    self._save_to_db(plate, speed, location, violation, camera_id)

                    if progress_callback:
                        progress_callback(
                            {
                                "frame_count": self.frame_count,
                                "detections_so_far": len(self.results),
                                "latest_result": result,
                            }
                        )

            if progress_callback and frame_idx % 60 == 0:
                progress_callback(
                    {
                        "frame_count": self.frame_count,
                        "detections_so_far": len(self.results),
                        "latest_result": None,
                    }
                )

        cap.release()
        self._cleanup_source()
        self.running = False
        self.done = True

    def _cleanup_source(self):
        if isinstance(self.source, str) and os.path.exists(self.source):
            try:
                os.remove(self.source)
            except OSError:
                pass

    def stop(self):
        self.running = False
