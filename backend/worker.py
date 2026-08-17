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
import traceback
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.database import get_next_queued_job, update_job
from scripts.config import OUTPUT_DIR


POLL_INTERVAL = 3  # seconds between job queue polls


def _progress_callback(job_id: str, step: str, progress: int, detail: str = ""):
    """Update job progress in MongoDB — called by the pipeline."""
    update_job(job_id, {
        "status": step,
        "progress": progress,
        "current_step": detail or step,
    })
    print(f"  [{job_id}] {step} — {progress}% — {detail}")


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

        # Determine final status from result
        status = result.get("status", "unknown")
        video_path = result.get("video_path", "")

        if status == "success" and video_path:
            update_job(job_id, {
                "status": "completed",
                "progress": 100,
                "current_step": "Complete",
                "video_url": video_path,
                "video_title": result.get("title", params.get("topic", "")),
                "metadata": {
                    "scene_count": result.get("scene_count", 0),
                    "project_dir": result.get("project_dir", ""),
                },
                "timing": result.get("timing", {}),
            })
            print(f"[Worker] ✅ Job {job_id} completed successfully!")
        else:
            errors = result.get("errors", [])
            update_job(job_id, {
                "status": "failed" if not video_path else "completed",
                "progress": 100 if video_path else 0,
                "current_step": "Complete" if video_path else "Failed",
                "video_url": video_path if video_path else None,
                "video_title": result.get("title", ""),
                "error": "; ".join(errors) if errors else None,
                "timing": result.get("timing", {}),
            })
            if video_path:
                print(f"[Worker] ⚠️  Job {job_id} completed with warnings")
            else:
                print(f"[Worker] ❌ Job {job_id} failed: {errors}")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        traceback.print_exc()

        update_job(job_id, {
            "status": "failed",
            "progress": 0,
            "current_step": "Failed",
            "error": error_msg,
            "failed_step": job.get("status", "unknown"),
        })

        print(f"[Worker] ❌ Job {job_id} failed: {error_msg}")


def main():
    """Main worker loop — poll for queued jobs and process them."""
    print("=" * 60)
    print("MAiX-YT Studio Worker — Starting")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print("=" * 60)

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
