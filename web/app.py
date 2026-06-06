"""
ShortForge AI — Web Dashboard v3
====================================
Beautiful localhost web UI for video generation.
Run: python web/app.py → http://localhost:5000
"""

import sys
import json
import threading
import uuid
import time
import urllib.parse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, render_template, request, jsonify, send_from_directory
from config import NICHES, OUTPUT_DIR, DEFAULT_NICHE, DEFAULT_LANGUAGE, DEFAULT_DURATION

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
#  JOB TRACKING
# ═══════════════════════════════════════════════════════════════
jobs = {}  # job_id -> {status, progress, message, result, ...}


def _run_video_job(job_id: str, params: dict):
    """Background thread: runs the full video pipeline."""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["progress"] = 5
        jobs[job_id]["message"] = "Starting pipeline..."

        from main import create_single_video

        def progress_callback(step, msg):
            step_progress = {
                "script": 15,
                "voice": 30,
                "images": 50,
                "animation": 65,
                "captions": 75,
                "assembly": 85,
                "complete": 100,
                "error": -1,
            }
            jobs[job_id]["progress"] = step_progress.get(step, 50)
            jobs[job_id]["message"] = msg
            jobs[job_id]["current_step"] = step

        result = create_single_video(
            niche=params.get("niche", DEFAULT_NICHE),
            language=params.get("language", DEFAULT_LANGUAGE),
            topic=params.get("topic"),
            enhance_images=False,  # Skip for speed
            caption_style="sentence",
            target_duration=params.get("duration", DEFAULT_DURATION),
            enable_animation=params.get("animate", False),
            manual_prompt=params.get("manual_prompt"),
            progress_callback=progress_callback,
        )

        if result:
            jobs[job_id]["status"] = "complete"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Video ready!"
            jobs[job_id]["result"] = str(result)
            jobs[job_id]["filename"] = Path(result).name
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = "Video generation failed"

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)[:200]

    jobs[job_id]["completed_at"] = datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html", niches=NICHES)


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Start a new video generation job."""
    data = request.json or {}

    job_id = str(uuid.uuid4())[:8]
    
    niche = data.get("niche", DEFAULT_NICHE)
    mode = data.get("mode", "auto")  # "auto" or "manual"
    topic = data.get("topic", "").strip() or None
    manual_prompt = data.get("prompt", "").strip() if mode == "manual" else None
    duration = int(data.get("duration", DEFAULT_DURATION))
    animate = bool(data.get("animate", False))

    if duration not in [15, 30, 45, 60, 90]:
        duration = DEFAULT_DURATION

    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "message": "Queued...",
        "current_step": "",
        "niche": niche,
        "duration": duration,
        "animate": animate,
        "mode": mode,
        "topic": topic,
        "result": None,
        "filename": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }

    params = {
        "niche": niche,
        "language": "hindi",
        "topic": topic,
        "duration": duration,
        "animate": animate,
        "manual_prompt": manual_prompt,
    }

    thread = threading.Thread(target=_run_video_job, args=(job_id, params), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id, "status": "queued"})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    """Get job status/progress."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/videos")
def api_videos():
    """List all generated videos."""
    videos = []
    if OUTPUT_DIR.exists():
        for date_dir in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if date_dir.is_dir():
                # Sort by modification time (newest first) instead of alphabetically
                files = sorted(date_dir.glob("*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)
                for f in files:
                    videos.append({
                        "name": f.name,
                        "path": str(f),
                        "date": date_dir.name,
                        "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
                        "url": f"/video/{date_dir.name}/{urllib.parse.quote(f.name)}",
                    })
    return jsonify(videos[:20])  # Last 20 videos


@app.route("/video/<date>/<filename>")
def serve_video(date, filename):
    """Serve a generated video file."""
    video_dir = OUTPUT_DIR / date
    return send_from_directory(str(video_dir), filename)


@app.route("/api/jobs")
def api_jobs():
    """List recent jobs."""
    job_list = sorted(jobs.values(), key=lambda j: j.get("created_at", ""), reverse=True)
    return jsonify(job_list[:10])


# ═══════════════════════════════════════════════════════════════
#  START
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║  🎬 ShortForge AI — Web Dashboard                            ║
║  ─────────────────────────────────────────────────────────────║
║  Open in browser: http://localhost:5000                       ║
║  Stop: Press Ctrl+C                                          ║
╚═══════════════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=5000, debug=False)
