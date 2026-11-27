from flask import Blueprint, render_template
from flask_login import login_required
from models.vehicle import Vehicle
from models.alert import Alert
from datetime import datetime, timedelta
from database.db import db
from sqlalchemy import func, distinct

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_vehicles = Vehicle.query.count()
    total_violations = Vehicle.query.filter(Vehicle.violation_type.isnot(None)).count()
    challans_issued = Vehicle.query.filter_by(challan_issued=True).count()
    active_cameras = 8

    today_vehicles = Vehicle.query.filter(Vehicle.detected_at >= today_start).count()
    today_violations = Vehicle.query.filter(
        Vehicle.detected_at >= today_start,
        Vehicle.violation_type.isnot(None)
    ).count()

    yesterday_start = today_start - timedelta(days=1)
    yesterday_violations = Vehicle.query.filter(
        Vehicle.detected_at >= yesterday_start,
        Vehicle.detected_at < today_start,
        Vehicle.violation_type.isnot(None)
    ).count()

    if yesterday_violations > 0:
        violation_change = round(
            ((today_violations - yesterday_violations) / yesterday_violations) * 100, 1
        )
    else:
        violation_change = 0

    last_alerts = Alert.query.order_by(Alert.timestamp.desc()).limit(10).all()

    videos_analyzed = db.session.query(
        func.count(distinct(Vehicle.camera_id))
    ).filter(
        Vehicle.camera_id.like("VIDEO-%") | Vehicle.camera_id.like("WEBCAM-%")
    ).scalar() or 0

    violation_breakdown = {}
    types = ["Overspeeding", "No Helmet", "No Parking", "Signal Jumping", "Wrong Lane"]
    for vtype in types:
        count = Vehicle.query.filter_by(violation_type=vtype).count()
        violation_breakdown[vtype] = count

    hourly_counts = []
    for h in range(24):
        hour_start = today_start + timedelta(hours=h)
        hour_end = hour_start + timedelta(hours=1)
        count = Vehicle.query.filter(
            Vehicle.detected_at >= hour_start,
            Vehicle.detected_at < hour_end
        ).count()
        hourly_counts.append({"hour": h, "count": count})

    return render_template(
        "dashboard.html",
        total_vehicles=total_vehicles,
        total_violations=total_violations,
        challans_issued=challans_issued,
        active_cameras=active_cameras,
        today_vehicles=today_vehicles,
        today_violations=today_violations,
        violation_change=violation_change,
        last_alerts=last_alerts,
        violation_breakdown=violation_breakdown,
        hourly_counts=hourly_counts,
        videos_analyzed=videos_analyzed,
        now=now,
    )
