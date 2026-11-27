from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import random
import string

db = SQLAlchemy()

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

VIOLATION_TYPES = [
    "Overspeeding",
    "No Helmet",
    "No Parking",
    "Signal Jumping",
    "Wrong Lane",
    None,
    None,
    None,
]

PLATE_PREFIXES = [
    "PNCG", "DHAKA", "CTG", "RAJ", "KHU", "BAR", "SYL", "RNG",
]

ALERT_TYPES = [
    "Overspeeding Detected",
    "Signal Violation",
    "Road Obstruction",
    "Camera Offline",
    "High Traffic Density",
    "Unauthorized Parking",
    "Wrong Way Driver",
    "Pedestrian Hazard",
]


def generate_plate():
    prefix = random.choice(PLATE_PREFIXES)
    series = random.randint(10, 99)
    number = random.randint(1000, 9999)
    return f"{prefix}-{series}-{number}"


def generate_challan_number():
    today = datetime.utcnow().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"CHN-{today}-{suffix}"


def seed_database():
    """Create an administrator only when explicit credentials are supplied.

    Demo traffic is intentionally not generated on production startup.
    Existing rows are never deleted or overwritten.
    """
    import os
    from models.user import User

    username = os.environ.get("INITIAL_ADMIN_USERNAME", "").strip()
    password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
    if username and password and not User.query.filter_by(username=username).first():
        if len(password) < 12:
            raise RuntimeError("INITIAL_ADMIN_PASSWORD must be at least 12 characters.")
        admin = User(username=username, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
