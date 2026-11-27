import random
import string

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

PLATE_PREFIXES = ["PNCG", "DHAKA", "CTG", "RAJ", "KHU", "BAR", "SYL", "RNG"]

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


def generate_detection():
    prefix = random.choice(PLATE_PREFIXES)
    series = random.randint(10, 99)
    number = random.randint(1000, 9999)
    plate = f"{prefix}-{series}-{number}"

    speed = round(random.uniform(20, 130), 1)
    violation = random.choice(VIOLATION_TYPES)

    if speed > 80 and violation is None:
        violation = "Overspeeding"

    return {
        "plate_number": plate,
        "speed_kmh": speed,
        "location": random.choice(PANCHAGARH_LOCATIONS),
        "camera_id": f"CAM-{random.randint(1, 8):02d}",
        "violation_type": violation,
    }
