# StreetWatch Neo ESP32 firmware (AP configuration)

## Hardware

ESP32 DevKit V1 with the existing pinout preserved. See `../../HARDWARE_WIRING_GUIDE.txt`.

## Arduino IDE prerequisites

- ESP32 board support package (Espressif Systems)
- ArduinoJson 7.x
- Built-in ESP32 `Preferences`, `WebServer`, `DNSServer`, `WiFiClientSecure`

Select the correct ESP32 Dev Module board and port, then compile/upload `StreetWatchESP32.ino`.

## No per-device config.h required

On first boot, the device creates a WPA2 access point:

- SSID: `STREETWATCH-SETUP`
- Password: `SWneo-` + last six hexadecimal characters of the ESP32 MAC address
- Setup URL: `http://192.168.4.1`

Enter Wi-Fi SSID/password, public HTTPS StreetWatch URL, registered Device ID and one-time token. Values are stored in ESP32 Preferences/NVS. The portal closes after restart and is not exposed during normal station operation.

Hold a momentary GPIO4-to-GND setup button for 4 seconds to reopen the portal. If Wi-Fi cannot reconnect for 120 seconds, the firmware enters recovery mode.

## TLS

The firmware embeds ISRG Root X1 and uses certificate validation. It does not call `setInsecure()`. It synchronizes the ESP32 clock with NTP before making HTTPS requests. If Render's active certificate chain changes to a different root, update the trusted CA bundle after checking the live certificate chain.

## Safety behavior

- Command polling: every 2 seconds after success; network/server errors back off exponentially up to 30 seconds.
- Telemetry: every 30 seconds.
- Server command lease: 5 seconds; firmware local stale-command stop: 8 seconds.
- Wi-Fi loss, non-200 HTTP response, stale command or server stop disables motors and accessories. A persistent command sequence prevents an old held command from restarting after reconnect/reboot; a new operator action is required.
- Automatic line following stops when the line is lost or an obstacle is detected.
- Physical emergency stop and motor disconnect are still mandatory.

Never print Wi-Fi passwords or device tokens to Serial Monitor. The MAC suffix is printed to help identify the setup AP password.
