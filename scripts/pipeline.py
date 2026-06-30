"""
pipeline.py — End-to-End Pipeline Orchestrator

Runs all scripts in sequence to generate a complete video.
Used by Streamlit's "direct mode" (without n8n) and for testing.

Pipeline steps:
  1. Generate script  (script_generator)
  2. Generate voice    (voice_generator)
  3. Collect visuals   (visual_generator)
  4. Assemble video    (video_generator)
  5. Generate metadata (metadata_generator)

Each generation gets its own project folder under output/:
  output/video_YYYYMMDD_HHMMSS/
    final_video.mp4
    preview.jpg
    script.md
    storyboard.json
    metadata.json
    logs.txt
"""

import io
import json
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

from scripts.config import ASSETS_DIR, OUTPUT_DIR
from scripts.script_generator import generate_script
from scripts.voice_generator import generate_voice
from scripts.visual_generator import collect_visuals
from scripts.video_generator import assemble_video
from scripts.metadata_generator import generate_metadata


class _LogCapture:
    """Captures stdout to a buffer while also printing to the real stdout."""

    def __init__(self, real_stdout):
        self._real = real_stdout
        self._buffer = io.StringIO()

    def write(self, text):
        self._real.write(text)
        self._buffer.write(text)

    def flush(self):
        self._real.flush()

    def getvalue(self):
        return self._buffer.getvalue()


def _save_script_md(script: dict, path: Path):
    """Save the script as a human-readable markdown file."""
    lines = []
    lines.append(f"# {script.get('title', 'Untitled Video')}\n")
    lines.append(f"**Topic:** {script.get('topic', 'N/A')}  ")
    lines.append(f"**Tone:** {script.get('tone', 'N/A')}  ")
    lines.append(f"**Duration:** {script.get('duration', '?')}s  ")
    lines.append(f"**Source:** {script.get('source', 'N/A')}  ")
    lines.append(f"**Scenes:** {len(script.get('scenes', []))}\n")
    lines.append("---\n")

    for scene in script.get("scenes", []):
        num = scene.get("scene_number", "?")
        dur = scene.get("duration_seconds", "?")
        lines.append(f"## Scene {num} ({dur}s)\n")
        lines.append(f"{scene.get('narration', '')}\n")
        lines.append(f"*Visual: {scene.get('visual_prompt', '')}*\n")
        lines.append("---\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def run_pipeline(
    topic: str,
    tone: str = "educational",
    duration: int = 60,
    progress_callback=None,
) -> dict:
    """
    Run the full video generation pipeline.

    Each generation creates its own project folder under output/.

    Args:
        topic:             The video topic.
        tone:              Script tone ("educational", "entertaining", "motivational").
        duration:          Target video duration in seconds.
        progress_callback: Optional callable(step: int, total: int, message: str)
                           for reporting progress to the UI.

    Returns:
        A dict with:
          - status (str):      "success" or "error"
          - video_path (str):  Path to the generated video
          - metadata (dict):   YouTube metadata
          - script (dict):     Script data
          - timing (dict):     Time taken per step
          - step_status (dict): Per-step status ("success" / "error" / "skipped")
          - project_dir (str): Path to the project folder
          - error (str):       Error message if status is "error"
    """
    total_steps = 5
    timing = {}
    step_status = {}
    errors = []

    # Set up log capture
    log_capture = _LogCapture(sys.stdout)
    old_stdout = sys.stdout
    sys.stdout = log_capture

    def report(step: int, message: str):
        """Report progress if a callback is provided."""
        if progress_callback:
            progress_callback(step, total_steps, message)
        print(f"\n[{step}/{total_steps}] {message}")

    # Create project directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_dir = OUTPUT_DIR / f"video_{timestamp}"
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create working directory for intermediate files
    run_dir = ASSETS_DIR / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    script = {}
    metadata = {}
    video_path = ""

    try:
        # ---------------------------------------------------------------
        # Step 1: Generate Script
        # ---------------------------------------------------------------
        report(1, "Generating script...")
        t0 = time.time()

        try:
            script = generate_script(topic, tone, duration)
            timing["script_generation"] = round(time.time() - t0, 2)
            step_status["script_generation"] = "success"

            # Save script as JSON (storyboard)
            with open(project_dir / "storyboard.json", "w", encoding="utf-8") as f:
                json.dump(script, f, indent=2, ensure_ascii=False)

            # Save script as human-readable markdown
            _save_script_md(script, project_dir / "script.md")

            print(f"  [OK] Script generated: {script['title']}")
            print(f"  [OK] {len(script['scenes'])} scenes")
        except Exception as e:
            timing["script_generation"] = round(time.time() - t0, 2)
            step_status["script_generation"] = "error"
            errors.append(f"Script generation failed: {e}")
            print(f"  [FAIL] Script generation error: {e}")
            raise  # Script is critical — can't continue without it

        # ---------------------------------------------------------------
        # Step 2: Generate Voice
        # ---------------------------------------------------------------
        report(2, "Generating narration audio...")
        t0 = time.time()

        try:
            audio_files = generate_voice(script, str(run_dir))
            timing["voice_generation"] = round(time.time() - t0, 2)
            step_status["voice_generation"] = "success"
            print(f"  [OK] {len(audio_files)} audio files created")
        except Exception as e:
            timing["voice_generation"] = round(time.time() - t0, 2)
            step_status["voice_generation"] = "error"
            errors.append(f"Voice generation failed: {e}")
            print(f"  [FAIL] Voice generation error: {e}")
            audio_files = []

        # ---------------------------------------------------------------
        # Step 3: Collect Visuals
        # ---------------------------------------------------------------
        report(3, "Collecting visual assets...")
        t0 = time.time()

        try:
            image_files = collect_visuals(script, str(run_dir))
            timing["visual_collection"] = round(time.time() - t0, 2)
            step_status["visual_collection"] = "success"
            print(f"  [OK] {len(image_files)} images collected")
        except Exception as e:
            timing["visual_collection"] = round(time.time() - t0, 2)
            step_status["visual_collection"] = "error"
            errors.append(f"Visual collection failed: {e}")
            print(f"  [FAIL] Visual collection error: {e}")
            image_files = []

        # ---------------------------------------------------------------
        # Step 4: Assemble Video
        # ---------------------------------------------------------------
        report(4, "Assembling video...")
        t0 = time.time()

        if audio_files and image_files:
            try:
                video_path = str(project_dir / "final_video.mp4")
                result_path = assemble_video(audio_files, image_files, video_path)
                video_path = result_path
                timing["video_assembly"] = round(time.time() - t0, 2)
                step_status["video_assembly"] = "success"

                # Copy preview to project dir if it was created alongside the video
                preview_src = Path(result_path.replace(".mp4", "_preview.jpg"))
                if preview_src.exists():
                    import shutil
                    preview_dst = project_dir / "preview.jpg"
                    shutil.copy2(str(preview_src), str(preview_dst))

                print(f"  [OK] Video saved: {result_path}")
            except Exception as e:
                timing["video_assembly"] = round(time.time() - t0, 2)
                step_status["video_assembly"] = "error"
                errors.append(f"Video assembly failed: {e}")
                print(f"  [FAIL] Video assembly error: {e}")
        else:
            timing["video_assembly"] = 0.0
            step_status["video_assembly"] = "skipped"
            print("  [SKIP] No audio/images available for video assembly")

        # ---------------------------------------------------------------
        # Step 5: Generate Metadata
        # ---------------------------------------------------------------
        report(5, "Generating metadata...")
        t0 = time.time()

        try:
            metadata = generate_metadata(topic, script)
            timing["metadata_generation"] = round(time.time() - t0, 2)
            step_status["metadata_generation"] = "success"
            print(f"  [OK] Metadata generated: {metadata.get('title', 'N/A')}")
        except Exception as e:
            timing["metadata_generation"] = round(time.time() - t0, 2)
            step_status["metadata_generation"] = "error"
            errors.append(f"Metadata generation failed: {e}")
            print(f"  [FAIL] Metadata generation error: {e}")

        # ---------------------------------------------------------------
        # Done
        # ---------------------------------------------------------------
        total_time = sum(timing.values())
        overall_status = "success" if not errors else "partial"
        print(f"\n[DONE] Pipeline complete in {total_time:.1f}s")
        if errors:
            print(f"  [WARN] {len(errors)} step(s) had errors:")
            for err in errors:
                print(f"    - {err}")

    except Exception as e:
        # Critical failure (script generation)
        print(f"\n[FAIL] Pipeline failed: {e}")
        overall_status = "error"
        if not errors:
            errors.append(str(e))

    finally:
        # Restore stdout and save logs
        sys.stdout = old_stdout
        log_text = log_capture.getvalue()

        try:
            with open(project_dir / "logs.txt", "w", encoding="utf-8") as f:
                f.write(log_text)
        except Exception:
            pass

    # Save combined metadata.json (YouTube metadata + generation info)
    combined_metadata = {
        "generation": {
            "topic": topic,
            "tone": tone,
            "duration": duration,
            "timestamp": timestamp,
            "status": overall_status,
            "timing": timing,
            "step_status": step_status,
            "errors": errors,
        },
        "youtube": metadata,
        "script_title": script.get("title", ""),
        "scene_count": len(script.get("scenes", [])),
    }

    try:
        with open(project_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(combined_metadata, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    result = {
        "status": overall_status,
        "video_path": video_path,
        "metadata": metadata,
        "script": script,
        "timing": timing,
        "step_status": step_status,
        "errors": errors,
        "error": errors[-1] if overall_status == "error" and errors else "",
        "project_dir": str(project_dir),
        "run_dir": str(run_dir),
    }

    return result


# ---------------------------------------------------------------------------
# CLI entry point -- for testing and n8n integration:
#   python -m scripts.pipeline --topic "How AI Works" --tone educational
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the full video pipeline")
    parser.add_argument("--topic", type=str, required=True, help="Video topic")
    parser.add_argument(
        "--tone",
        type=str,
        default="educational",
        choices=["educational", "entertaining", "motivational"],
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Target duration in seconds"
    )
    args = parser.parse_args()

    result = run_pipeline(args.topic, args.tone, args.duration)
    print("\n" + json.dumps(result, indent=2))
