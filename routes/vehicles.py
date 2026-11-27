from flask import Blueprint, render_template, request
from flask_login import login_required
from models.vehicle import Vehicle

vehicles_bp = Blueprint("vehicles", __name__)


@vehicles_bp.route("/vehicles")
@login_required
def index():
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = Vehicle.query.order_by(Vehicle.detected_at.desc())
    if search:
        query = query.filter(Vehicle.plate_number.ilike(f"%{search}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    vehicles = pagination.items

    return render_template(
        "vehicles.html",
        vehicles=vehicles,
        pagination=pagination,
        search=search,
    )


@vehicles_bp.route("/vehicles/<int:vehicle_id>")
@login_required
def detail(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return render_template("vehicle_detail.html", vehicle=vehicle)
