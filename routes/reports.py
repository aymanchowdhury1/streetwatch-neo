from flask import Blueprint, render_template
from flask_login import login_required
from models.vehicle import Vehicle
from database.db import db
from datetime import datetime, timedelta
from collections import defaultdict

reports_bp = Blueprint("reports", __name__)

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

VIOLATION_TYPES = ["Overspeeding", "No Helmet", "No Parking", "Signal Jumping", "Wrong Lane"]


@reports_bp.route("/reports")
@login_required
def index():
    now = datetime.utcnow()

    total_vehicles = Vehicle.query.count()
    total_violations = Vehicle.query.filter(Vehicle.violation_type.isnot(None)).count()
    challans_issued = Vehicle.query.filter_by(challan_issued=True).count()

    violation_breakdown = {}
    for vtype in VIOLATION_TYPES:
        violation_breakdown[vtype] = Vehicle.query.filter_by(violation_type=vtype).count()

    weekly_data = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = Vehicle.query.filter(
            Vehicle.detected_at >= day_start,
            Vehicle.detected_at < day_end,
        ).count()
        weekly_data.append({"label": day_start.strftime("%a %d"), "count": count})

    location_stats = defaultdict(lambda: defaultdict(int))
    violations = Vehicle.query.filter(Vehicle.violation_type.isnot(None)).all()
    for v in violations:
        location_stats[v.location][v.violation_type] += 1

    location_stats_plain = {loc: dict(types) for loc, types in location_stats.items()}

    return render_template(
        "reports.html",
        total_vehicles=total_vehicles,
        total_violations=total_violations,
        challans_issued=challans_issued,
        violation_breakdown=violation_breakdown,
        weekly_data=weekly_data,
        location_stats=location_stats_plain,
    )
