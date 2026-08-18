"""
worker.py — Background Worker for MAiX-YT Studio

Polls MongoDB for queued jobs and runs the video pipeline.
Runs as a SEPARATE PROCESS from FastAPI — NOT BackgroundTasks.

This is critical for Railway: the worker runs alongside the API
but independently so long-running pipeline execution doesn't block API responses.

Run with: python -m backend.worker
"""

import sys
import time
import threading
import traceback
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.database import get_next_queued_job, update_job, get_user_oauth_tokens
from scripts.config import OUTPUT_DIR
from scripts.google_drive import upload_to_drive


POLL_INTERVAL = 3   # seconds between job queue polls
JOB_TIMEOUT = 480   # 8 minutes max per job — kills it if it hangs


def _cleanup_zombie_jobs():
    """
    Reset any jobs stuck in 'generating_*' or 'assembling_*' status back to failed.

    This happens when the worker process is killed mid-job (e.g. Render deploy swap,
    OOM kill). Without this, those jobs stay stuck forever because nothing resets them.
    Called once on worker startup.
    """
    try:
        from scripts.database import _db, _use_mongo
        if not _use_mongo or _db is None:
            return

        stuck_statuses = [
            "generating_script",
            "generating_voice",
            "generating_visuals",
            "assembling_video",
            "uploading",
        ]
        result = _db.video_jobs.update_many(
            {"status": {"$in": stuck_statuses}},
            {"$set": {
                "status": "failed",
                "progress": 0,
                "current_step": "Failed (server restarted)",
                "error": "Job was interrupted by a server restart. Please try again.",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
        )
        if result.modified_count > 0:
            print(f"[Worker] Cleaned up {result.modified_count} zombie job(s) from previous run.")
    except Exception as e:
        print(f"[Worker] Zombie cleanup error (non-fatal): {e}")


def _progress_callback(job_id: str, step: str, progress: int, detail: str = ""):
    """Update job progress in MongoDB — called by the pipeline."""
    update_job(job_id, {
        "status": step,
        "progress": progress,
        "current_step": detail or step,
    })
    print(f"  [{job_id}] {step} — {progress}% — {detail}")


def _to_video_url(local_path: str) -> str:
    """
    Convert a local filesystem video path to a relative URL served by FastAPI's StaticFiles.

    The backend mounts StaticFiles at /api/videos pointing to OUTPUT_DIR.
    So a file at OUTPUT_DIR/video_20260818_052952/final_video.mp4
    should become /api/videos/video_20260818_052952/final_video.mp4

    Works for both:
      - Linux:   /data/videos/video_20260818_052952/final_video.mp4
      - Windows: D:\\Projects\\YT\\output\\video_20260818_052952\\final_video.mp4
    """
    p = Path(local_path)
    # The video is always at: {OUTPUT_DIR}/{project_folder}/final_video.mp4
    # We need: /api/videos/{project_folder}/final_video.mp4
    folder_name = p.parent.name   # e.g. "video_20260818_052952"
    file_name = p.name            # e.g. "final_video.mp4"
    return f"/api/videos/{folder_name}/{file_name}"


def run_pipeline_for_job(job: dict):

    """Execute the full video pipeline for a single job."""
    job_id = job["_id"]
    params = job.get("params", {})

    print(f"\n{'='*60}")
    print(f"[Worker] Starting job: {job_id}")
    print(f"  Topic: {params.get('topic', 'Unknown')}")
    print(f"  Duration: {params.get('duration', 60)}s")
    print(f"  Style: {params.get('style', 'Documentary')}")
    print(f"{'='*60}")

    # Map pipeline step numbers to status strings
    STEP_STATUS_MAP = {
        1: "generating_script",
        2: "generating_voice",
        3: "generating_visuals",
        4: "assembling_video",
        5: "uploading",
    }

    result_holder = {}
    error_holder = {}

    def _run():
        """Run the pipeline in a thread so we can enforce a timeout."""
        try:
            from scripts.pipeline import run_pipeline

            # Build the callback matching pipeline's signature: (step, total_steps, message)
            def on_progress(step: int, total_steps: int, message: str):
                status = STEP_STATUS_MAP.get(step, f"step_{step}")
                progress = int((step / total_steps) * 100)
                _progress_callback(job_id, status, progress, message)

            # Run the pipeline (it creates its own output directory)
            result = run_pipeline(
                topic=params.get("topic", ""),
                tone=params.get("tone", "educational"),
                duration=params.get("duration", 60),
                style=params.get("style", "Documentary"),
                language=params.get("language", "english"),
                aspect_ratio=params.get("aspect_ratio", "16:9"),
                voice_gender=params.get("voice_gender", "female"),
                voice_engine=params.get("voice_engine", "Edge-TTS (Neural)"),
                progress_callback=on_progress,
            )
            result_holder["result"] = result
        except Exception as e:
            error_holder["error"] = e
            traceback.print_exc()

    # Run pipeline in a thread with a hard timeout
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=JOB_TIMEOUT)

    if thread.is_alive():
        # Job exceeded the timeout — mark as failed
        print(f"[Worker] ⏰ Job {job_id} timed out after {JOB_TIMEOUT}s!")
        update_job(job_id, {
            "status": "failed",
            "progress": 0,
            "current_step": "Failed (timed out)",
            "error": f"Job exceeded the {JOB_TIMEOUT}s time limit. The server may be under heavy load.",
        })
        return

    if "error" in error_holder:
        e = error_holder["error"]
        error_msg = f"{type(e).__name__}: {str(e)}"
        update_job(job_id, {
            "status": "failed",
            "progress": 0,
            "current_step": "Failed",
            "error": error_msg,
            "failed_step": job.get("status", "unknown"),
        })
        print(f"[Worker] ❌ Job {job_id} failed: {error_msg}")
        return

    if "result" not in result_holder:
        update_job(job_id, {
            "status": "failed",
            "progress": 0,
            "current_step": "Failed",
            "error": "Pipeline returned no result",
        })
        return

    result = result_holder["result"]

    # Determine final status from result
    status = result.get("status", "unknown")
    video_path = result.get("video_path", "")

    # Convert local filesystem path to a relative URL that the frontend can fetch.
    # The backend mounts StaticFiles at /api/videos pointing to OUTPUT_DIR,
    # so /data/videos/video_20260818/final_video.mp4 becomes
    # /api/videos/video_20260818/final_video.mp4
    video_url = _to_video_url(video_path) if video_path else None

    if status == "success" and video_url:
        # Check if user has Google Drive connected
        user_id = job.get("user_id")
        drive_tokens = get_user_oauth_tokens(user_id, "google_drive") if user_id else None
        
        if drive_tokens and video_path:
            _progress_callback(job_id, "uploading", 95, "Uploading to Google Drive")
            print(f"[Worker] ☁️ Uploading video to Google Drive for user {user_id}...")
            
            # Use the job topic as the filename, sanitized
            safe_topic = "".join([c if c.isalnum() else "_" for c in params.get("topic", "Untitled")])
            filename = f"MAiX_{safe_topic}.mp4"
            
            upload_res = upload_to_drive(
                file_path=video_path,
                filename=filename,
                token_data=drive_tokens,
                description=f"Generated by MAiX-YT Studio\nTopic: {params.get('topic', '')}"
            )
            
            if upload_res.get("success"):
                # Use the Drive URL instead of the local one for playback
                video_url = upload_res.get("drive_url")
                print(f"[Worker] ☁️ Upload successful: {video_url}")
            else:
                print(f"[Worker] ⚠️ Drive upload failed, falling back to local URL. Error: {upload_res.get('error')}")

        update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "current_step": "Complete",
            "video_url": video_url,
            "video_title": result.get("title", params.get("topic", "")),
            "metadata": {
                "scene_count": result.get("scene_count", 0),
                "project_dir": result.get("project_dir", ""),
            },
            "timing": result.get("timing", {}),
        })
        print(f"[Worker] ✅ Job {job_id} completed — video_url: {video_url}")
    else:
        errors = result.get("errors", [])
        update_job(job_id, {
            "status": "failed" if not video_url else "completed",
            "progress": 100 if video_url else 0,
            "current_step": "Complete" if video_url else "Failed",
            "video_url": video_url,
            "video_title": result.get("title", ""),
            "error": "; ".join(errors) if errors else None,
            "timing": result.get("timing", {}),
        })
        if video_url:
            print(f"[Worker] ⚠️  Job {job_id} completed with warnings — video_url: {video_url}")
        else:
            print(f"[Worker] ❌ Job {job_id} failed: {errors}")



def main():
    """Main worker loop — poll for queued jobs and process them."""
    print("=" * 60)
    print("MAiX-YT Studio Worker — Starting")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print(f"Job timeout: {JOB_TIMEOUT}s")
    print("=" * 60)

    # Clean up zombie jobs from previous crashed runs
    _cleanup_zombie_jobs()

    while True:
        try:
            job = get_next_queued_job()
            if job:
                run_pipeline_for_job(job)
            else:
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\n[Worker] Shutting down...")
            break
        except Exception as e:
            print(f"[Worker] Unexpected error: {e}")
            traceback.print_exc()
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
