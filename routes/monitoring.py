"""Live USB webcam discovery and MJPEG streaming for the StreetWatch host PC.

USB webcams must be connected to the computer running this Flask application.
The ESP32 DevKit V1 is not a USB webcam host.
"""
import threading
import time
from flask import Blueprint, Response, jsonify, render_template, abort
from flask_login import login_required

monitoring_bp = Blueprint("monitoring", __name__)

try:
    import cv2
except ImportError:  # Camera support remains optional; dashboard still loads.
    cv2 = None

CAMERA_SCAN_LIMIT = 8
_scan_lock = threading.Lock()
_cameras = {}
_last_scan = 0.0


def _scan_cameras(force=False):
    """Discover attached host-computer webcams, keeping successful captures open."""
    global _last_scan, _cameras
    if cv2 is None:
        return
    now = time.time()
    if not force and now - _last_scan < 5:
        return
    if not _scan_lock.acquire(blocking=False):
        return
    try:
        # Recheck after acquiring the lock.
        if not force and time.time() - _last_scan < 5:
            return
        found = {}
        for index in range(CAMERA_SCAN_LIMIT):
            cap = _cameras.get(index)
            if cap is not None and cap.isOpened():
                found[index] = cap
                continue
            # CAP_DSHOW is more reliable for USB cameras on Windows.
            backend = getattr(cv2, "CAP_DSHOW", 0) if __import__('platform').system() == 'Windows' else cv2.CAP_ANY
            candidate = cv2.VideoCapture(index, backend)
            if candidate.isOpened():
                candidate.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                candidate.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                found[index] = candidate
            else:
                candidate.release()
        for index, cap in _cameras.items():
            if index not in found:
                try:
                    cap.release()
                except Exception:
                    pass
        _cameras = found
        _last_scan = time.time()
    finally:
        _scan_lock.release()


def _camera_snapshot():
    _scan_cameras()
    return [
        {"id": index, "name": f"Camera {position + 1}", "status": "online",
         "stream_url": f"/monitoring/camera/{index}/stream"}
        for position, index in enumerate(sorted(_cameras))
    ]


@monitoring_bp.route("/monitoring")
@login_required
def index():
    return render_template("monitoring.html", cameras=[])


@monitoring_bp.get("/api/cameras")
@login_required
def camera_status():
    return jsonify({"cameras": _camera_snapshot(), "count": len(_cameras), "supported": cv2 is not None})


@monitoring_bp.get("/monitoring/camera/<int:camera_id>/stream")
@login_required
def camera_stream(camera_id):
    _scan_cameras()
    if camera_id not in _cameras:
        abort(404)

    def generate():
        while True:
            cap = _cameras.get(camera_id)
            if cap is None or not cap.isOpened():
                break
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.1)
                continue
            ok, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
            if ok:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + encoded.tobytes() + b'\r\n')
            time.sleep(0.025)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={"Cache-Control": "no-store, no-cache, must-revalidate"})
