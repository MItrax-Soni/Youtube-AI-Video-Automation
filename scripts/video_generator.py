"""
video_generator.py — Video Assembly

Combines audio files and images into a final MP4 video using FFmpeg.

Phase 1: Created a simple slideshow image preview.
Phase 4: Uses FFmpeg to create scene video clips and concatenate them into a final video.
"""

import glob
import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

from scripts.config import OUTPUT_DIR


def _get_ffmpeg_exe() -> str:
    """Return path to the FFmpeg executable."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def assemble_video(
    audio_files: list[str],
    image_files: list[str],
    output_path: str = None,
) -> str:
    """
    Assemble audio and image files into a final MP4 video using FFmpeg.

    Args:
        audio_files:  List of paths to audio files (one per scene).
        image_files:  List of paths to image files (one per scene).
        output_path:  Path for the output video file (.mp4).

    Returns:
        The path to the generated MP4 video file.
    """
    if output_path is None:
        output_path = str(OUTPUT_DIR / "final_video.mp4")

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if not image_files or not audio_files:
        print("  [WARN] Missing images or audio files, skipping video assembly.")
        return output_path

    ffmpeg_exe = _get_ffmpeg_exe()
    work_dir = out_file.parent / f"temp_{out_file.stem}"
    work_dir.mkdir(parents=True, exist_ok=True)

    scene_clips = []

    # 1. Build individual scene video clips
    for i, (img_path, aud_path) in enumerate(zip(image_files, audio_files)):
        clip_path = work_dir / f"clip_{i:02d}.mp4"
        
        # FFmpeg command: Loop static image, combine with audio track, sync to shortest stream (audio)
        cmd = [
            ffmpeg_exe,
            "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", str(aud_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(clip_path)
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            scene_clips.append(str(clip_path))
            print(f"  [OK] Rendered clip {i+1}/{len(image_files)}: {clip_path.name}")
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8', errors='ignore')
            print(f"  [FAIL] FFmpeg failed on clip {i+1}: {err_msg}")
            raise RuntimeError(f"FFmpeg error on scene {i+1}: {err_msg}")

    # 2. Concat demuxer list file
    concat_list_path = work_dir / "concat_list.txt"
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            # Escape single quotes and backslashes for FFmpeg demuxer
            safe_clip = clip.replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe_clip}'\n")

    # 3. Concatenate scene clips into final MP4
    concat_cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(out_file)
    ]

    try:
        subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"  [OK] Final video assembled with FFmpeg: {out_file.name}")
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore')
        print(f"  [FAIL] FFmpeg concat failed: {err_msg}")
        raise RuntimeError(f"FFmpeg concat error: {err_msg}")

    # 4. Generate visual preview grid (composite image) for quick dashboard view / history
    try:
        images = [Image.open(f) for f in image_files]
        img_width, img_height = images[0].size

        # For large scene counts, show a representative subset (max 20 thumbnails)
        MAX_PREVIEW_THUMBS = 20
        if len(images) > MAX_PREVIEW_THUMBS:
            step = len(images) / MAX_PREVIEW_THUMBS
            indices = [int(i * step) for i in range(MAX_PREVIEW_THUMBS)]
            images = [images[i] for i in indices]

        # Adaptive grid: scale columns based on image count
        count = len(images)
        if count <= 4:
            cols = 2
        elif count <= 9:
            cols = 3
        elif count <= 16:
            cols = 4
        else:
            cols = 5
        rows = (count + cols - 1) // cols
        thumb_w, thumb_h = img_width // cols, img_height // cols

        composite = Image.new("RGB", (thumb_w * cols, thumb_h * rows), (30, 30, 30))
        for idx, img in enumerate(images):
            r, c = divmod(idx, cols)
            thumb = img.resize((thumb_w, thumb_h))
            composite.paste(thumb, (c * thumb_w, r * thumb_h))

        preview_path = str(out_file).replace(".mp4", "_preview.jpg")
        composite.save(preview_path, "JPEG", quality=90)
        print(f"  [OK] Video preview saved: {Path(preview_path).name} ({count} thumbnails)")
    except Exception as e:
        print(f"  [WARN] Could not create preview thumbnail: {e}")

    return str(out_file)


# ---------------------------------------------------------------------------
# CLI entry point — allows calling from n8n via:
#   python -m scripts.video_generator --audio-dir assets/ --image-dir assets/
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Assemble video from assets")
    parser.add_argument(
        "--audio-dir", type=str, required=True, help="Directory with audio files"
    )
    parser.add_argument(
        "--image-dir", type=str, required=True, help="Directory with image files"
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Output video file path"
    )
    args = parser.parse_args()

    # Match any scene audio file (WAV or MP3) and image file
    audio = sorted(
        glob.glob(str(Path(args.audio_dir) / "scene_*_audio.mp3")) +
        glob.glob(str(Path(args.audio_dir) / "scene_*_audio.wav"))
    )
    images = sorted(glob.glob(str(Path(args.image_dir) / "scene_*_visual.jpg")))

    result = assemble_video(audio, images, args.output)
    print(json.dumps({"video_path": result}, indent=2))
