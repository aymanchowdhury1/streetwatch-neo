# Render deployment guide

## 1. Prepare GitHub

Push the project to a GitHub repository and connect that repository to Render. Choose **New → Blueprint** to apply `render.yaml`, or create a Python Web Service manually. Select the `main` branch and enable automatic deploys.

## 2. Web Service settings

- Runtime: Python
- Region: Singapore if offered for your account
- Plan: Free (initial testing)
- Build command: `pip install -r requirements.txt`
- Start command:

  ```bash
  gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
  ```

- Health check path: `/healthz`

`app.py` creates the Flask object as `app`; it is not `wsgi.py` or a guessed `app:create_app()` invocation. Gunicorn imports `app:app`.

## 3. Environment variables

Set these under the service Environment page:

| Key | Value |
|---|---|
| `SECRET_KEY` | Long random secret (Render Blueprint can generate it) |
| `WTF_CSRF_SECRET_KEY` | Different long random secret |
| `INITIAL_ADMIN_USERNAME` | Your chosen administrator username |
| `INITIAL_ADMIN_PASSWORD` | Unique password, 12+ characters |
| `DATABASE_URL` | PostgreSQL connection URL |
| `COOKIE_SECURE` | `true` |

Do not paste secrets into source files, GitHub issues, screenshots or Serial Monitor. The initial admin is created only when both initial-admin variables are present and that username does not already exist. Changing the environment variable later does not automatically reset an existing password.

## 4. Database: read this before relying on Free

The application accepts Render PostgreSQL's connection URL and normalizes legacy `postgres://` URLs. Prefer the **internal** database URL when the web service and database are in the same Render region. Create the database separately and copy its internal URL into `DATABASE_URL`.

Render's current Free Postgres offer has 1 GB storage and expires 30 days after creation. Render's Free web service has an ephemeral filesystem: SQLite files and uploaded files disappear on restart, redeploy or spin-down. Thus, a $0 Render-only setup is suitable for a short-lived demo/test, not durable records. Export/backup before the database expiry. For ongoing use, select a database provider with a durable free allowance (verify its current limits) or budget for a persistent database. No database migration is automatically performed from the bundled SQLite into the hosted PostgreSQL database. To import traffic and alert rows, first deploy with `DATABASE_URL` set, then run `python scripts/import_sqlite_data.py path/to/legacy.sqlite` from an environment that can reach that database. The script deliberately skips user accounts and device tokens; create a fresh admin and re-register devices. The Render Free Web Service does not provide shell access, so run this from your local computer with the same `DATABASE_URL` environment variable.

## 5. First deployment

1. Confirm Render build succeeds.
2. Open `https://YOUR-SERVICE.onrender.com/healthz`; expect JSON with `status: ok`.
3. Open the root URL and sign in using the administrator account created from the environment variables.
4. Open Devices, register an ESP32, and securely copy its token.
5. Use the Render HTTPS URL as the ESP32 server URL.
6. After connecting the ESP32, verify the device reports Online and a recent Last contact time.

## 6. Free service behavior

- The web service spins down after 15 minutes without inbound requests and may take about a minute to wake.
- Free instances may restart and have no persistent disk.
- Functional ESP32 command polling can keep sending inbound traffic while the rover is connected, but this is not an uptime guarantee. Do not add a separate high-frequency keepalive.
- A sleeping server, lost Wi-Fi or expired command lease results in a safe stop; a control action may need to be sent again after the service wakes.

## 7. Troubleshooting

- **Build fails:** inspect Render build logs; core requirements deliberately omit YOLO/EasyOCR to reduce memory/build pressure. Those optional packages are in `requirements-video.txt`.
- **Health check 503:** verify PostgreSQL URL, database availability and logs.
- **Login unavailable:** ensure initial admin variables were set before the first startup; the username must not already exist.
- **ESP32 gets 401:** re-enter the current device token. Rotate/revoke old tokens and reconfigure affected hardware.
- **ESP32 TLS fails:** verify URL starts with `https://`, device clock has synchronized via NTP, firmware root CA is current and Render's certificate chain is trusted.
- **Free service sleeping:** first request can be delayed; wait for wake-up. Do not expect uninterrupted remote control.
- **Data missing:** local SQLite and media on Render Free are not durable. Restore from a backup or a persistent database source.

## 8. Updating

Commit and push to `main`. Render automatically builds and deploys the new commit. Check deploy logs and `/healthz` afterward.
