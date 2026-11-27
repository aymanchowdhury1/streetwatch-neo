# StreetWatch Neo — Cameras and Attachment Outputs

## Live webcam monitoring

- Plug USB webcams into the Windows/Linux computer that runs the Flask application (`python app.py`). The ESP32 DevKit V1 does not act as a USB webcam host.
- Install the project dependencies from the project root: `pip install -r requirements.txt` (includes `opencv-python`).
- Open **Live Monitoring**. The server scans camera indexes 0–7 and automatically shows all webcams it can open. One detected webcam appears as Camera 1; four detected webcams appear together in a 2×2 layout. The page refreshes the detected camera list every five seconds.
- If a camera is missing, close other apps using it, check Windows camera privacy permissions, and reconnect it. Camera numbering follows the OpenCV device index order and may differ between boots.

## Attachment controls

The **Control** page has five attachment controls:

| Button | Behavior | ESP32 pin |
|---|---|---|
| Brush | Click to toggle ON/OFF | GPIO16 |
| Rig Up | ON only while held; OFF on release/cancel | GPIO21 |
| Rig Down | ON only while held; OFF on release/cancel | GPIO22 |
| LED | Click to toggle ON/OFF | GPIO17 |
| Spray | Click to toggle ON/OFF | GPIO19 |

The web API rejects simultaneous Rig Up and Rig Down. The firmware repeats this interlock and turns all outputs off after a lost server heartbeat or emergency stop.

**Electrical safety:** ESP32 GPIO pins are logic outputs only. Drive relays/MOSFET modules, not pumps, motors, solenoids, or high-power LEDs directly. Use suitable external power, fuses, flyback protection for inductive loads, and common ground. Add physical lift limit switches and a hardwired emergency disconnect; software interlocks are not a substitute for mechanical/electrical safety devices.

The USB webcam feeds are captured and streamed by the Flask host computer. The ESP32 handles the vehicle and accessory outputs; the webcams do not connect through the ESP32.
