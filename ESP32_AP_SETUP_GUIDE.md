# ESP32 phone-based AP setup guide

## What the setup portal does

The ESP32 stores its Wi-Fi and StreetWatch connection details in Preferences/NVS flash. Firmware no longer needs a per-device `config.h` edit. The portal runs only during first setup or deliberate recovery; it is not exposed during normal station-mode operation.

## Before starting

1. Flash `firmware/StreetWatchESP32/StreetWatchESP32.ino` to the ESP32 DevKit V1.
2. In the StreetWatch website, open **Devices** and register a unique Device ID.
3. Copy the newly generated token immediately. The website does not display it again.
4. Keep the Render base URL ready, e.g. `https://your-app.onrender.com`.

Firmware prerequisites: ESP32 Arduino core, ArduinoJson 7, and built-in ESP32 `Preferences`, `WebServer`, and `DNSServer` libraries. The firmware uses NTP to set time before certificate validation.

## First-time setup

1. Power the ESP32 with motors safely disconnected or lifted.
2. It starts the setup AP automatically if no saved settings exist.
3. On the phone, join Wi-Fi network `STREETWATCH-SETUP`.
4. WPA2 password format: `SWneo-` followed by the final six hexadecimal characters of the ESP32 MAC address. Use the MAC label or the MAC suffix printed by the board's USB Serial Monitor; the firmware does not print Wi-Fi passwords or device tokens.
5. Open a browser and visit `http://192.168.4.1`.
6. Enter:
   - Wi-Fi SSID
   - Wi-Fi password
   - StreetWatch server URL (must begin with `https://`)
   - registered Device ID
   - the one-time device token
7. Tap **SAVE & CONNECT**. The ESP32 stores the values and restarts.
8. It connects to the router, synchronizes time, verifies HTTPS and starts command polling and telemetry.

The portal page is mobile responsive. If the phone reports “No Internet”, stay connected to the ESP32 hotspot and open the local address manually.

## Reopen setup mode

- Connect a normally-open momentary pushbutton between GPIO4 and GND.
- Hold it for at least 4 seconds.
- The ESP32 stops motors and accessories before opening the WPA2 setup hotspot.
- If the saved Wi-Fi cannot reconnect for 120 seconds, the firmware automatically enters setup recovery.

The portal uses a deterministic WPA2 passphrase derived from the MAC suffix. Keep physical access to the ESP32 controlled. Anyone with physical access and its MAC can derive this local setup passphrase. Do not leave the rover unattended during setup. After network loss or reboot, firmware requires a new explicit control action rather than replaying the last movement command.

## Troubleshooting

- **Hotspot absent:** check power, serial boot messages, GPIO4 is not held low, and firmware flashed successfully.
- **Phone says no internet:** expected; browse directly to `http://192.168.4.1`.
- **Cannot join AP:** verify passphrase format exactly; case-sensitive.
- **Saved but device offline:** confirm Wi-Fi password, 2.4 GHz network compatibility, internet access and server URL.
- **401 response:** token was copied incorrectly, revoked or belongs to another device. Rotate token in Devices and save the new token through the portal.
- **TLS error:** confirm device time sync, use HTTPS, and ensure the server certificate chain is trusted by the firmware root CA.
- **Portal returns after 2 minutes:** ESP32 cannot connect to the saved Wi-Fi; configure it again.
- **Server asleep:** wait for Render to wake. The ESP32 remains stopped until a fresh command arrives.

Never paste the token into public chat, screenshots or a Git repository.
