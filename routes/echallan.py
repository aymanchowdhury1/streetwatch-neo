from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from models.vehicle import Vehicle
from database.db import db
from datetime import datetime, timedelta
import random
import string

echallan_bp = Blueprint("echallan", __name__)


def _gen_challan_number():
    today = datetime.utcnow().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"CHN-{today}-{suffix}"


@echallan_bp.route("/echallan")
@login_required
def index():
    challans = (
        Vehicle.query.filter_by(challan_issued=True)
        .order_by(Vehicle.detected_at.desc())
        .all()
    )
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    challans_today = Vehicle.query.filter(
        Vehicle.challan_issued == True,
        Vehicle.detected_at >= today_start,
    ).count()
    return render_template("echallan.html", challans=challans, challans_today=challans_today)


@echallan_bp.route("/echallan/issue/<int:vehicle_id>", methods=["POST"])
@login_required
def issue(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    if not vehicle.challan_issued:
        vehicle.challan_issued = True
        vehicle.challan_number = _gen_challan_number()
        db.session.commit()
        flash(f"Challan {vehicle.challan_number} issued successfully.", "success")
    else:
        flash("Challan already issued for this vehicle.", "error")
    return redirect(url_for("vehicles.index"))


@echallan_bp.route("/echallan/<challan_number>")
@login_required
def challan_detail(challan_number):
    vehicle = Vehicle.query.filter_by(challan_number=challan_number).first_or_404()
    return render_template("challan_print.html", vehicle=vehicle)
