from flask import Blueprint, render_template, request
from flask_login import login_required
from models.vehicle import Vehicle

violations_bp = Blueprint("violations", __name__)

VIOLATION_TYPES = ["Overspeeding", "No Helmet", "No Parking", "Signal Jumping", "Wrong Lane"]


@violations_bp.route("/violations")
@login_required
def index():
    filter_type = request.args.get("type", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = Vehicle.query.filter(Vehicle.violation_type.isnot(None)).order_by(
        Vehicle.detected_at.desc()
    )

    if filter_type and filter_type in VIOLATION_TYPES:
        query = query.filter(Vehicle.violation_type == filter_type)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    vehicles = pagination.items

    return render_template(
        "violations.html",
        vehicles=vehicles,
        pagination=pagination,
        filter_type=filter_type,
        violation_types=VIOLATION_TYPES,
    )
