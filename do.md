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
# StreetWatch Neo — ESP32 Quick Setup Guide (`do.md`)

## What Is Already Done
You do **not** need to register the ESP32 in the website or create `.env` / `config.h` from scratch:
- **`.env`** is already created with random `SECRET_KEY` and `WTF_CSRF_SECRET_KEY` values.
- **`streetwatch.db`** already has an ESP32 device pre-registered:
  - **Device ID:** `streetwatch-rover-01`
  - **Display Name:** `StreetWatch Rover 01`
  - **Token:** `F3u4EDEMdBhSEcZXqWDOcmJKioPJVoEWL9e9CN34-Fw`
- **`firmware/StreetWatchESP32/config.h`** is already created with that exact `STREETWATCH_DEVICE_ID` and `STREETWATCH_DEVICE_TOKEN`.

---

## Step 1: Start the Server on the Host PC
1. Make sure Python dependencies are installed on the PC running the server:
   ```powershell
   pip install -r requirements.txt
   ```
2. Start the server:
   ```powershell
   python app.py
   ```
   `app.py` runs on `0.0.0.0:5000`, which makes it reachable from other devices (like the ESP32) on the same local Wi-Fi/LAN.
3. If Windows Defender Firewall pops up when starting Python, allow access on **Private networks** (or allow TCP port `5000` inbound so the ESP32 can connect).

---

## Step 2: Find the Local Server URL (Host PC IP)
The ESP32 and the server PC must be connected to the **same Wi-Fi / router**.
Do **not** use `127.0.0.1` or `localhost` in the ESP32 firmware — `localhost` means the ESP32 itself. Instead, find the server PC's local IPv4 address:

* **Windows (PowerShell or Command Prompt):**
  ```powershell
  ipconfig
  ```
  Look under your active adapter (**Wireless LAN adapter Wi-Fi** or **Ethernet adapter**) for the **IPv4 Address** (for example: `192.168.1.25`).
* **Linux:**
  ```bash
  hostname -I
  ```
* **macOS:**
  ```bash
  ipconfig getifaddr en0
  ```

Your local server URL is:
```text
http://<YOUR_PC_IPV4>:5000
```
*(Example: if your IPv4 address is `192.168.1.25`, the URL is `http://192.168.1.25:5000`.)*

---

## Step 3: Update `firmware/StreetWatchESP32/config.h`
Open `firmware/StreetWatchESP32/config.h` and update **only these 3 lines**:

```cpp
#define WIFI_SSID "YOUR_WIFI_NAME"          // 1. Your Wi-Fi name (2.4 GHz)
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"  // 2. Your Wi-Fi password
...
#define STREETWATCH_SERVER "http://192.168.1.25:5000" // 3. Replace with Step 2 URL
```

> **Note:** Leave `STREETWATCH_DEVICE_ID` and `STREETWATCH_DEVICE_TOKEN` as they are — they already match `streetwatch.db`. Also leave `STREETWATCH_ROOT_CA` and `STREETWATCH_INSECURE_TLS` as they are when using `http://` on a local LAN.

---

## Step 4: Flash the ESP32
1. Open **Arduino IDE**.
2. Install the **ESP32** board package (via **Boards Manager**) and the **ArduinoJson** library (via **Library Manager**).
3. Select **Tools → Board → ESP32 Dev Module** and choose the ESP32's **COM Port**.
4. Open `firmware/StreetWatchESP32/StreetWatchESP32.ino` and click **Upload**.
5. *(Optional)* Open **Serial Monitor** at `115200` baud to verify it connects to Wi-Fi.

---

## Step 5: Wire & Test
1. Wire the ESP32, L298N motor driver, IR line sensor, and attachments according to:
   - `ESP32_FULL_CONNECTION_DIAGRAM.txt`
   - `ESP32_BUTTON_AND_PIN_MAP.txt`
   *(If you do not have the HC-SR04 ultrasonic sensor connected, set `USE_ULTRASONIC_INTERLOCK=false` in `StreetWatchESP32.ino`.)*
2. On the server PC browser, open `http://127.0.0.1:5000` and log in with:
   - **Username:** `admin`
   - **Password:** `admin`
3. Open **Control** in the sidebar, select **StreetWatch Rover 01**, lift the rover's wheels off the ground, and test at low speed.
