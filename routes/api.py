from flask import Blueprint, jsonify
from flask_login import login_required
from models.vehicle import Vehicle
from models.alert import Alert
from database.db import db
from detection.mock_detector import generate_detection
from datetime import datetime, timedelta

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/stats")
@login_required
def stats():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    violations_today = Vehicle.query.filter(
        Vehicle.detected_at >= today_start,
        Vehicle.violation_type.isnot(None)
    ).count()

    challans_today = Vehicle.query.filter(
        Vehicle.detected_at >= today_start,
        Vehicle.challan_issued == True
    ).count()

    return jsonify({
        "total_devices": 12,
        "active_monitoring": 8,
        "violations_today": violations_today,
        "challans_today": challans_today,
        "roads_cleaned": "24.5 km",
    })


@api_bp.route("/api/violations/chart")
@login_required
def violations_chart():
    types = ["Overspeeding", "No Helmet", "No Parking", "Signal Jumping", "Wrong Lane"]
    data = {}
    for vtype in types:
        data[vtype] = Vehicle.query.filter_by(violation_type=vtype).count()
    return jsonify(data)


@api_bp.route("/api/traffic/hourly")
@login_required
def traffic_hourly():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    result = []
    for h in range(24):
        hour_start = today_start + timedelta(hours=h)
        hour_end = hour_start + timedelta(hours=1)
        count = Vehicle.query.filter(
            Vehicle.detected_at >= hour_start,
            Vehicle.detected_at < hour_end
        ).count()
        result.append({"hour": h, "count": count})
    return jsonify(result)


@api_bp.route("/api/alerts/recent")
@login_required
def alerts_recent():
    alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(5).all()
    return jsonify([a.to_dict() for a in alerts])


@api_bp.route("/api/simulate-detection")
@login_required
def simulate_detection():
    data = generate_detection()
    vehicle = Vehicle(
        plate_number=data["plate_number"],
        speed_kmh=data["speed_kmh"],
        location=data["location"],
        camera_id=data["camera_id"],
        violation_type=data["violation_type"],
        detected_at=datetime.utcnow(),
    )
    db.session.add(vehicle)
    db.session.commit()
    return jsonify(vehicle.to_dict())
