UPDATED DEPLOYMENT AND DEVICE SETUP NOTICE
=========================================
The phone-based ESP32 AP portal and Render/GitHub setup now supersede the
older manual config.h instructions in this legacy note. Follow these current
project guides instead:

- README.md
- RENDER_DEPLOYMENT_GUIDE.md
- GITHUB_SETUP_GUIDE.md
- ESP32_AP_SETUP_GUIDE.md
- REMOTE_CONNECTION_GUIDE.md
- HARDWARE_WIRING_GUIDE.txt

Firmware configuration is stored in ESP32 Preferences/NVS through the
STREETWATCH-SETUP WPA2 hotspot at http://192.168.4.1. Do not populate or
commit a real config.h. Device tokens must be rotated if previously exposed.

--- LEGACY REFERENCE BELOW ---
# StreetWatch Neo — Control, Devices and ESP32 setup

## Existing login

Legacy demo accounts were removed from the sanitized development database. Configure a new administrator using INITIAL_ADMIN_USERNAME and INITIAL_ADMIN_PASSWORD.

## Run locally in VS Code (website only)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000` and sign in. Localhost is suitable for developing the website on your PC. An ESP32 on a different network cannot reach localhost or a private `192.168.x.x` address.

## Add ESP32 devices

1. Sign in as an administrator and click **Devices** in the sidebar.
2. Enter a unique device ID, a display name and the base URL of the website.
3. The page generates a unique device token. Copy the configuration snippet immediately; the token is shown only once.
4. For each board, copy `firmware/StreetWatchESP32/config.h.example` to `config.h`, set its Wi-Fi credentials, device ID and unique token, and set its server URL.
5. Upload `StreetWatchESP32.ino` to that ESP32. Repeat with a different ID and token for every additional board.
6. Open **Control** and select the device you want to operate from the Selected device dropdown.

The exact firmware URL setting is this line in `firmware/StreetWatchESP32/config.h`:

```cpp
#define STREETWATCH_SERVER "https://your-public-domain.example"
```

Change this line when that ESP32 must use a different website URL. The Devices page stores the URL for reference and lets you edit it, but changing the URL in the web page does not remotely rewrite firmware already flashed onto the ESP32; copy the new URL into `config.h` and upload again.

## Different networks / internet access

The ESP32 initiates outbound HTTPS requests to the web server. The web server does not connect to the ESP32's local IP, so the rover and website may use different Wi-Fi networks/mobile networks. For this to work, deploy Flask behind a public HTTPS domain with a valid TLS certificate. A PC running `python app.py` at `127.0.0.1` is not remotely reachable. Do not expose Flask's development server directly to the public internet; use a production WSGI server and HTTPS reverse proxy/host.

For HTTPS, paste the correct root CA PEM certificate into `STREETWATCH_ROOT_CA` and keep `STREETWATCH_INSECURE_TLS` set to `0`. Setting it to `1` disables certificate verification and is unsafe for production. Use unique device tokens and keep them private.

## Controls and safety

- Manual: Forward both motors forward; Reverse both reverse; Left Motor A forward / Motor B reverse; Right Motor A reverse / Motor B forward.
- Auto: OpenJumper 4-channel digital IR line following. White target is default; Black is selectable. The module reads IR reflectivity/contrast, not arbitrary RGB colours.
- Brush, LED and Spray are latched toggles. Rig Up and Rig Down are momentary hold controls.
- Firmware stops motors and switches accessories off when server contact is lost. The server also clears latched accessory states when a device becomes stale.
- The sidebar tabs scroll independently. Control is landscape-first on desktop and responsive on smaller screens.
- Full wiring: `ESP32_FULL_CONNECTION_DIAGRAM.txt`.
- Button actions and GPIO HIGH/LOW states: `ESP32_BUTTON_AND_PIN_MAP.txt`.

## USB cameras

USB webcams connect to the computer running Flask, not to the ESP32. Live Monitoring scans available host webcams; they are separate from the ESP32 network connection.

## Hardware caution

Test with wheels lifted and low speed. Use separate, correctly rated motor and attachment power, common logic ground, fused supplies, flyback protection, relay/MOSFET drivers, physical lift limit switches, hardwired up/down interlock and an accessible physical motor disconnect. GPIO pins are not load power outputs. Autonomous line following is a prototype, not a road-safe autonomous driving system.
