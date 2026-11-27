"""Import traffic and alert rows from a legacy SQLite DB into DATABASE_URL.

Users and robot_devices are intentionally not imported: the older archive
contained predictable demo accounts and exposed device tokens. Create a fresh
admin and register each ESP32 again so new credentials are issued.
"""
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

from app import app
from database.db import db
from models.alert import Alert
from models.vehicle import Vehicle

IMPORTS = {
    "vehicles": (Vehicle, {"detected_at"}),
    "alerts": (Alert, {"timestamp"}),
}


def parse_datetime(value):
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sqlite_file", nargs="?", default=str(Path(__file__).resolve().parents[1] / "streetwatch.db"))
    args = parser.parse_args()
    source = Path(args.sqlite_file).resolve()
    if not source.is_file():
        raise SystemExit(f"SQLite file not found: {source}")

    conn = sqlite3.connect(str(source))
    conn.row_factory = sqlite3.Row
    try:
        with app.app_context():
            for table, (model, datetime_fields) in IMPORTS.items():
                try:
                    rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
                except sqlite3.OperationalError:
                    print(f"Skip missing source table: {table}")
                    continue
                inserted = 0
                for row in rows:
                    data = {key: row[key] for key in row.keys() if key in model.__table__.columns}
                    for key in datetime_fields:
                        if key in data:
                            data[key] = parse_datetime(data[key])
                    record_id = data.get("id")
                    if record_id and db.session.get(model, record_id):
                        continue
                    db.session.add(model(**data))
                    inserted += 1
                db.session.commit()
                print(f"{table}: imported {inserted} new rows (source rows: {len(rows)})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
