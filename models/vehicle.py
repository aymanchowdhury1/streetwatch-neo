from database.db import db
from datetime import datetime


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    speed_kmh = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    violation_type = db.Column(db.String(50), nullable=True)
    camera_id = db.Column(db.String(20), nullable=False)
    challan_issued = db.Column(db.Boolean, default=False)
    challan_number = db.Column(db.String(30), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "plate_number": self.plate_number,
            "detected_at": self.detected_at.strftime("%Y-%m-%d %H:%M:%S"),
            "speed_kmh": round(self.speed_kmh, 1),
            "location": self.location,
            "violation_type": self.violation_type,
            "camera_id": self.camera_id,
            "challan_issued": self.challan_issued,
            "challan_number": self.challan_number,
        }

    def __repr__(self):
        return f"<Vehicle {self.plate_number}>"
