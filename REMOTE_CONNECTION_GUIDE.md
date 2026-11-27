# Remote connection and multi-device guide

## Network topology

Each ESP32 initiates outbound HTTPS requests to the same public StreetWatch URL:

```text
Phone / PC on Wi-Fi A
        |
      Internet
        |
  Render HTTPS service
        |
      Internet
      /      \\
 ESP32 #1   ESP32 #2
 Wi-Fi B    Wi-Fi C
```

The ESP32 does not accept inbound internet connections. No router port forwarding, public home IP, local PC IP or always-on PC is required.

## Register multiple devices

1. Sign in as administrator.
2. Open Devices and add each device with a unique Device ID and display name.
3. Copy each token once and keep it securely.
4. Enter the same public HTTPS base URL, the matching Device ID and its own token into each ESP32 AP portal.
5. Repeat for every rover. Device ID and token are unique per ESP32; the server base URL can be identical.

The API resolves the device by `X-Device-Token`. Telemetry is associated with that authenticated record and a mismatched claimed Device ID is rejected. A device cannot fetch another device's command by changing a URL parameter.

## Request flow

- `GET /api/device/command` — ESP32 polls its own command.
- `POST /api/device/telemetry` — ESP32 reports firmware, RSSI, sensors, battery and obstacle data.
- Browser `/api/robot/command` — authenticated administrator issues a command for one selected device.
- Browser `/api/robot/devices` — lists registered devices without exposing tokens.

The token is sent in the `X-Device-Token` header, never in the URL. Firmware validates HTTPS certificates; insecure TLS mode is not used.

## Timing and free hosting

The firmware polls commands every 2 seconds after success (server errors trigger exponential backoff up to 30 seconds) and sends telemetry every 30 seconds. The browser renews the command lease while its authenticated control page is active. Commands have a short server-side lease; the ESP32 also stops if it does not receive a fresh valid command. Wi-Fi loss, HTTP errors, server sleep or stale commands stop motors and disable accessories.

Render Free services sleep after 15 minutes without inbound traffic and may take about a minute to wake. ESP32 command polling is functional traffic, but it may keep the web service active while the rover is connected. The service may still restart or be unavailable. Free Render Postgres expires after 30 days; a persistent database is needed for ongoing records. See the Render guide.

## Revoke a token

In Devices, choose **REVOKE & ROTATE TOKEN**. The previous token becomes invalid immediately. Copy the new token and re-enter it using the ESP32 AP setup portal. Removing a device also revokes its token by deleting its registration.

## Safety

Internet control is best-effort, not safety-rated. The ESP32 remembers the last accepted command sequence and requires a newer explicit operator action after Wi-Fi loss/reboot; server restarts also require a new operator action. Keep a hardware emergency stop in series with motor power. The ESP32's local stale-command timeout is a second layer, not a replacement for a physical disconnect.
