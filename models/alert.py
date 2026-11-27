from database.db import db
from datetime import datetime


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(10), nullable=False, default="medium")
    resolved = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "location": self.location,
            "description": self.description,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "severity": self.severity,
            "resolved": self.resolved,
        }

    def __repr__(self):
        return f"<Alert {self.alert_type} @ {self.location}>"
