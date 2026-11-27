import json
import os
import tempfile
import threading
import time
from uuid import uuid4

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
    stream_with_context,
)
from flask_login import login_required

from models.vehicle import Vehicle

video_bp = Blueprint("video", __name__, url_prefix="/video")

processing_sessions = {}


def _check_libs():
    try:
        import cv2
        import ultralytics
        import easyocr
        return True, None
    except ImportError as exc:
        return False, str(exc)


@video_bp.route("")
@video_bp.route("/")
@login_required
def index():
    recent = (
        Vehicle.query.filter(
            Vehicle.camera_id.like("VIDEO-%") | Vehicle.camera_id.like("WEBCAM-%")
        )
        .order_by(Vehicle.detected_at.desc())
        .limit(20)
        .all()
    )
    return render_template("video_analysis.html", recent_detections=recent)


@video_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    libs_ok, lib_err = _check_libs()
    if not libs_ok:
        return (
            jsonify(
                {
                    "error": (
                        "Detection libraries not installed. "
                        "Run: pip install ultralytics easyocr opencv-python"
                    )
                }
            ),
            400,
        )

    if "video" not in request.files:
        return jsonify({"error": "No video file provided."}), 400

    f = request.files["video"]
    if f.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    allowed = {".mp4", ".avi", ".mov", ".mkv"}
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in allowed:
        return jsonify({"error": f"Unsupported format: {ext}. Use {', '.join(allowed)}"}), 400

    session_id = str(uuid4())
    tmp_path = os.path.join(tempfile.gettempdir(), f"streetwatch_{session_id}{ext}")
    f.save(tmp_path)

    _start_processing(session_id, tmp_path)
    return jsonify({"session_id": session_id, "status": "processing"})


@video_bp.route("/webcam/start")
@login_required
def webcam_start():
    libs_ok, lib_err = _check_libs()
    if not libs_ok:
        return (
            jsonify(
                {
                    "error": (
                        "Detection libraries not installed. "
                        "Run: pip install ultralytics easyocr opencv-python"
                    )
                }
            ),
            400,
        )

    session_id = str(uuid4())
    _start_processing(session_id, 0, camera_prefix="WEBCAM")
    return jsonify({"session_id": session_id, "status": "started"})


def _start_processing(session_id, source, camera_prefix="VIDEO"):
    from detection.video_processor import VideoProcessor

    flask_app = current_app._get_current_object()

    processor = VideoProcessor(source, session_id, flask_app)
    if camera_prefix == "WEBCAM":
        processor._camera_prefix = "WEBCAM"

    t = threading.Thread(target=processor.process, daemon=True)
    processing_sessions[session_id] = {"processor": processor, "thread": t}
    t.start()


@video_bp.route("/stream/<session_id>")
@login_required
def stream(session_id):
    @stream_with_context
    def generate():
        last_sent_idx = 0

        while True:
            session = processing_sessions.get(session_id)
            if not session:
                yield _sse({"type": "error", "message": "Session not found."})
                break

            processor = session["processor"]

            if processor.error:
                yield _sse({"type": "error", "message": processor.error})
                break

            new_results = processor.results[last_sent_idx:]
            for result in new_results:
                yield _sse(
                    {
                        "type": "detection",
                        "data": result,
                        "frame_count": processor.frame_count,
                        "detections_so_far": len(processor.results),
                    }
                )
                last_sent_idx += 1

            if not new_results:
                yield _sse(
                    {
                        "type": "progress",
                        "frame_count": processor.frame_count,
                        "detections_so_far": len(processor.results),
                    }
                )

            if processor.done:
                yield _sse(
                    {
                        "type": "done",
                        "status": "done",
                        "frame_count": processor.frame_count,
                        "results": processor.results,
                    }
                )
                break

            time.sleep(0.5)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@video_bp.route("/stop/<session_id>", methods=["POST"])
@login_required
def stop(session_id):
    session = processing_sessions.get(session_id)
    if session:
        session["processor"].stop()
        return jsonify({"status": "stopped"})
    return jsonify({"status": "not_found"}), 404


@video_bp.route("/results/<session_id>")
@login_required
def results(session_id):
    session = processing_sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    processor = session["processor"]
    return jsonify(
        {
            "session_id": session_id,
            "frame_count": processor.frame_count,
            "done": processor.done,
            "results": processor.results,
        }
    )


def _sse(data):
    return f"data: {json.dumps(data)}\n\n"
