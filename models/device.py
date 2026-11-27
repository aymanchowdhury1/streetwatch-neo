from datetime import datetime
from database.db import db

class Device(db.Model):
    __tablename__ = 'robot_devices'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    server_url = db.Column(db.String(500), nullable=False, default='')
    mode = db.Column(db.String(12), nullable=False, default='manual')
    command = db.Column(db.String(12), nullable=False, default='stop')
    speed = db.Column(db.Integer, nullable=False, default=150)
    line_color = db.Column(db.String(8), nullable=False, default='white')
    emergency_stop = db.Column(db.Boolean, nullable=False, default=False)
    accessories = db.Column(db.JSON, nullable=False, default=lambda: {'brush': False, 'rig_up': False, 'rig_down': False, 'led': False, 'spray': False})
    telemetry = db.Column(db.JSON, nullable=False, default=dict)
    last_seen = db.Column(db.DateTime, nullable=True)
    command_updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    command_seq = db.Column(db.Integer, nullable=False, default=0)
    command_lease_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    rearm_required = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
