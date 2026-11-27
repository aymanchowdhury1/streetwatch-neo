# StreetWatch Neo

Flask traffic-monitoring dashboard and multi-device ESP32 rover control platform. This repository is prepared for GitHub and Render deployment, with phone-based ESP32 setup.

## Features

- Dashboard, monitoring, video analysis, vehicles, violations, e-challan and reports.
- Multi-device ESP32 registration and authenticated command/telemetry endpoints.
- ESP32 outbound HTTPS polling; no router port forwarding or PC-hosted server required.
- ESP32 WPA2 setup hotspot, mobile web portal, Preferences/NVS configuration and recovery button.
- PostgreSQL URL support and additive migration for the device command timestamp.
- Health endpoint at `/healthz`.

## Repository layout

- `app.py` — Flask application factory and WSGI entry point (`app:app`).
- `config.py` — environment-driven settings.
- `database/`, `models/` — SQLAlchemy models and startup setup.
- `routes/control.py` — web control, device management and ESP32 APIs.
- `templates/`, `static/` — dashboard and frontend.
- `firmware/StreetWatchESP32/StreetWatchESP32.ino` — ESP32 firmware and AP setup portal.
- `render.yaml`, `Procfile` — Render deployment configuration.
- `requirements-video.txt` — optional, resource-heavy local video analysis dependencies.

## Local installation

1. Use Python 3.12 (the included `.python-version` pins 3.12.10).
2. Create and activate a virtual environment.
3. Install core dependencies:

   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\\Scripts\\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`. Replace the secret placeholders and choose a unique initial admin password of at least 12 characters.
5. Run:

   ```bash
   python app.py
   ```

6. Open `http://127.0.0.1:5000`. The sanitized bundled development database keeps the existing traffic and alert sample records; demo users and exposed device credentials were removed. The configured `INITIAL_ADMIN_USERNAME` / `INITIAL_ADMIN_PASSWORD` creates the first admin on startup.

Optional local video analysis:

```bash
pip install -r requirements-video.txt
```

YOLO/EasyOCR are intentionally not installed in the small Render Free web build; their model downloads and memory requirements are unsuitable for a small free web instance. Webcam access is local-host hardware and is not available on Render.

## GitHub and automatic deployment

Follow `GITHUB_SETUP_GUIDE.md`. `.gitignore` excludes `.env`, the real firmware `config.h`, local databases, uploads, Python caches and private key files. Keep `.env.example` and `config.h.example` as safe templates. Connect the repository's `main` branch to Render; `render.yaml` enables automatic deployment.

## Render deployment

Follow `RENDER_DEPLOYMENT_GUIDE.md`. Correct start command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
```

Set `SECRET_KEY`, `WTF_CSRF_SECRET_KEY`, `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD`, and `DATABASE_URL`. Use a PostgreSQL connection URL for hosted structured data. `postgres://` URLs are normalized to `postgresql://`.

**Free-tier warning:** Render Free web services sleep after 15 minutes without inbound requests, wake-up can take about a minute, and their filesystem is ephemeral. Render Free Postgres is limited to 1 GB and expires 30 days after creation. It is not a permanent $0 database. Export/backup data before expiry or use a different durable database provider. No free plan guarantees 24/7 uptime.

The ESP32 polls the command API every 2 seconds after success, backs off from 2 to 30 seconds on server errors, and sends telemetry every 30 seconds while connected. That is functional command/telemetry traffic, not a promise that Render will remain awake or that the service is always available. If Render is asleep, the rover stops on stale-command timeout and resumes only after a fresh valid command.

## ESP32 setup

1. Register a device in the website Devices page. Copy the token immediately; it is shown only once.
2. Flash `firmware/StreetWatchESP32/StreetWatchESP32.ino` using Arduino IDE with ESP32 board support and ArduinoJson 7.
3. On first boot, or after holding GPIO4 SETUP button for 4 seconds, the ESP32 starts `STREETWATCH-SETUP`.
4. Connect phone to that WPA2 hotspot. Password is `SWneo-` plus the final six hexadecimal characters of the ESP32 MAC address.
5. Browse to `http://192.168.4.1`, enter Wi-Fi SSID/password, Render HTTPS URL, Device ID and token, then Save.
6. The ESP32 restarts, joins the configured Wi-Fi and begins authenticated HTTPS requests.

See `ESP32_AP_SETUP_GUIDE.md`, `REMOTE_CONNECTION_GUIDE.md`, and `HARDWARE_WIRING_GUIDE.txt`.

## Security and safety

- Rotate any credential that was present in an older archive or firmware.
- Never commit `.env`, real `config.h`, local database files, tokens or Wi-Fi passwords.
- Browser state-changing routes use CSRF protection; the ESP32 command/telemetry routes are exempt from browser CSRF and require the per-device `X-Device-Token` header. Device registration, deletion and token rotation are administrator-only.
- Device tokens are sent in `X-Device-Token`, never in URLs.
- Production device URLs must use HTTPS; firmware validates the ISRG Root X1 certificate and does not use insecure TLS.
- Commands expire server-side. A monotonically increasing command sequence prevents a previously held command from restarting after ESP32 Wi-Fi reconnect/reboot; server restarts require a fresh operator action. The ESP32 stops motors and turns accessories off when the command lease expires, Wi-Fi is lost, or the server returns an error.
- Keep a physical emergency stop and motor power disconnect. Internet stop is not a substitute for a hardware stop.
- Test with wheels raised and loads disconnected before floor operation.

## Storage and known limits

- SQLAlchemy structured records support PostgreSQL. Startup uses `create_all` plus one additive `robot_devices.command_updated_at` migration; it does not run a full Alembic migration history.
- Existing local SQLite traffic/alert sample data is retained in the supplied development DB, but old demo users and the previously exposed ESP32 registration were removed. Configure a new admin and register devices again.
- `scripts/import_sqlite_data.py` imports vehicle and alert records from a legacy SQLite file into the PostgreSQL URL in `DATABASE_URL`; users and device tokens are intentionally not migrated.
- Render filesystem uploads and SQLite changes are ephemeral. Video upload processing currently uses temporary files and removes them after processing; the app does not yet provide durable object-storage integration. Do not treat uploaded media as an archive.
- Render Free Postgres is temporary (30 days). For long-term data, use a database with a durable backup/retention policy. Object storage for large video/image archives requires a separate provider account and integration.

## Verification

Run:

```bash
python -m compileall -q .
```

For firmware compile, install Arduino CLI/IDE, ESP32 Arduino core and ArduinoJson 7, then compile for the correct ESP32 DevKit board. Physical network, TLS, motor and safety tests must be performed on actual hardware.
