"""
video_generator.py — Dynamic FFmpeg Video Assembly Engine

Combines audio files and images into a professional MP4 video using FFmpeg.

Added Features:
  - Smooth Crossfade Transitions (xfade: fade, dissolve, fadeblack)
  - Image Motion Effects (Ken Burns slow zoom-in, zoom-out, pan-left, pan-right)
  - Visual Fade-In at start (1.0s) & Fade-Out at end (1.0s)
  - Key Phrase Text Highlights (animated keyword box overlays)
  - Synchronized Subtitles (clean readable text overlay per scene)
  - Low-volume Background Music Mixing (voice narration stays loud & prominent)
  - Style-based effect preset customization (Documentary, Educational, Entertainment, Motivational)
  - Per-clip fallback error handling to guarantee non-breaking video renders.
"""

import glob
import json
import os
import random
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from PIL import Image

from scripts.config import (
    ASSETS_DIR,
    OUTPUT_DIR,
    SettingsManager,
    get_style_profile,
)


def _get_ffmpeg_exe() -> str:
    """Return path to the FFmpeg executable."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _get_audio_duration(aud_path: str, ffmpeg_exe: str) -> float:
    """Return exact duration in seconds of an audio file."""
    try:
        if str(aud_path).lower().endswith(".wav"):
            with wave.open(str(aud_path), "r") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 2)
    except Exception:
        pass

    try:
        cmd = [ffmpeg_exe, "-hide_banner", "-i", str(aud_path)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = res.stderr.decode("utf-8", errors="ignore")
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
        if match:
            hours, mins, secs = match.groups()
            return round(float(hours) * 3600 + float(mins) * 60 + float(secs), 2)
    except Exception:
        pass

    return 5.0


def _extract_text_highlight(narration: str, objective: str = "") -> str:
    """Extract a short, punchy keyword phrase (2–4 words) for on-screen highlight."""
    text_source = narration if narration else objective
    if not text_source:
        return ""

    clean = re.sub(r"[^\w\s]", "", text_source).strip()
    words = clean.split()
    if not words:
        return ""

    if len(words) <= 4:
        return " ".join(words).upper()

    stop_words = {
        "in", "this", "video", "the", "a", "an", "and", "or", "to", "of", "for",
        "with", "on", "at", "by", "from", "up", "about", "into", "over", "after",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "but", "not", "you", "your", "they", "we", "can"
    }

    meaningful = [w for w in words if w.lower() not in stop_words and len(w) >= 3]
    if len(meaningful) >= 2:
        return f"{meaningful[0].upper()} {meaningful[1].upper()}"
    elif len(meaningful) == 1:
        return meaningful[0].upper()

    return " ".join(words[:3]).upper()


def _build_drawtext_filter(
    text_highlight: str,
    subtitle_text: str,
    duration: float,
    enable_highlight: bool,
    enable_subtitles: bool,
    work_dir: Path,
    scene_idx: int,
) -> str:
    """Build FFmpeg drawtext filter string using textfile inputs to avoid escaping errors."""
    filters = []

    if enable_highlight and text_highlight:
        hl_file = work_dir / f"hl_{scene_idx:02d}.txt"
        with open(hl_file, "w", encoding="utf-8") as f:
            f.write(text_highlight.strip())
        safe_hl_path = str(hl_file).replace("\\", "/").replace(":", "\\:")
        alpha_expr = f"if(lt(t,0.4),t/0.4,if(gt(t,{max(0.5, duration-0.4):.2f}),({duration:.2f}-t)/0.4,1))"
        hl_filter = (
            f"drawtext=textfile='{safe_hl_path}':fontcolor=yellow:fontsize=36:"
            f"box=1:boxcolor=black@0.65:boxborderw=8:"
            f"x=(w-text_w)/2:y=h*0.16:alpha='{alpha_expr}'"
        )
        filters.append(hl_filter)

    if enable_subtitles and subtitle_text:
        sub_file = work_dir / f"sub_{scene_idx:02d}.txt"
        safe_sub = subtitle_text.strip()
        if len(safe_sub) > 42:
            mid = len(safe_sub) // 2
            space_idx = safe_sub.find(" ", mid)
            if space_idx != -1:
                safe_sub = safe_sub[:space_idx] + "\n" + safe_sub[space_idx + 1:]

        with open(sub_file, "w", encoding="utf-8") as f:
            f.write(safe_sub)
        safe_sub_path = str(sub_file).replace("\\", "/").replace(":", "\\:")

        sub_filter = (
            f"drawtext=textfile='{safe_sub_path}':fontcolor=white:fontsize=22:"
            f"box=1:boxcolor=black@0.70:boxborderw=6:"
            f"x=(w-text_w)/2:y=h*0.80:line_spacing=4"
        )
        filters.append(sub_filter)

    return ",".join(filters)


def _get_motion_vf(
    motion_type: str,
    duration: float,
    fps: int = 25,
    width: int = 1280,
    height: int = 720,
    zoom_speed: float = 0.0015,
    max_zoom: float = 1.15,
) -> str:
    """Build FFmpeg zoompan filter string for static images.

    Uses an adaptive zoom speed so the effect is always visibly continuous
    for the entire clip duration, regardless of how long the clip is.
    Pan effects use the output frame counter (on) so the pan is smooth and
    never resets mid-clip (a common bug when using the x/y state variable).
    """
    total_frames = max(25, int(duration * fps))

    # Adaptive speed: travel the full zoom range [1.0 → max_zoom] over the
    # full clip, so the movement is always visible even for short clips.
    adaptive_speed = (max_zoom - 1.0) / max(total_frames, 1)
    # Clamp: don't go slower than a very subtle drift or faster than a jump cut
    adaptive_speed = max(0.0005, min(adaptive_speed, 0.005))

    # Pixels to pan per frame so the pan covers 12% of frame width total
    pan_px_per_frame = (width * 0.12) / max(total_frames, 1)

    if motion_type == "zoom_in":
        vf = (
            f"zoompan=z='min(1+on*{adaptive_speed:.6f},{max_zoom:.4f})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps},"
            f"scale={width}:{height},setsar=1,format=yuv420p"
        )
    elif motion_type == "zoom_out":
        vf = (
            f"zoompan=z='max(1.0,{max_zoom:.4f}-on*{adaptive_speed:.6f})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps},"
            f"scale={width}:{height},setsar=1,format=yuv420p"
        )
    elif motion_type == "pan_right":
        # x starts at 0, moves right by pan_px_per_frame each frame
        # clamped to never exceed the right boundary
        vf = (
            f"zoompan=z='1.12':"
            f"x='min(on*{pan_px_per_frame:.4f},iw-iw/zoom)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps},"
            f"scale={width}:{height},setsar=1,format=yuv420p"
        )
    elif motion_type == "pan_left":
        # x starts at the right edge, moves left by pan_px_per_frame each frame
        start_x = width * 0.12
        vf = (
            f"zoompan=z='1.12':"
            f"x='max(0,{start_x:.4f}-on*{pan_px_per_frame:.4f})':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={width}x{height}:fps={fps},"
            f"scale={width}:{height},setsar=1,format=yuv420p"
        )
    else:
        # Static: just scale/pad/sar with no motion
        vf = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p"
        )

    return vf


def _find_bg_music_file() -> str:
    """Check project directory for available background music tracks."""
    candidates = [
        ASSETS_DIR / "music" / "ambient_pad.wav",
        ASSETS_DIR / "music" / "bg_music.mp3",
        ASSETS_DIR / "bg_music.mp3",
        ASSETS_DIR / "bg_music.wav",
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    music_dir = ASSETS_DIR / "music"
    if music_dir.exists():
        files = sorted(glob.glob(str(music_dir / "*.mp3")) + glob.glob(str(music_dir / "*.wav")))
        if files:
            return files[0]

    return ""


def _mix_background_music(
    video_path: str,
    bg_music_path: str,
    bg_volume: float,
    ffmpeg_exe: str,
    out_path: str,
) -> bool:
    """Mix background music at low volume with voice narration track."""
    try:
        if not bg_music_path or not Path(bg_music_path).exists():
            return False

        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(video_path),
            "-stream_loop", "-1",
            "-i", str(bg_music_path),
            "-filter_complex",
            f"[1:a]volume={bg_volume:.2f}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            str(out_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0 and Path(out_path).exists()
    except Exception as e:
        print(f"  [WARN] Background music mixing error: {e}")
        return False


def _xfade_pass(
    clip_paths: list,
    clip_durations: list,
    xfade_name: str,
    td: float,
    ffmpeg_exe: str,
    out_path,
) -> bool:
    """Single filter_complex xfade pass for N clips (max ~10 for reliability)."""
    try:
        n = len(clip_paths)
        inputs = []
        for cp in clip_paths:
            inputs += ["-i", str(cp)]

        v_in = [f"[{i}:v]" for i in range(n)]
        a_in = [f"[{i}:a]" for i in range(n)]

        filter_parts = []
        cur_v = v_in[0]
        cur_a = a_in[0]

        # Cumulative offset: where each clip starts on the merged timeline.
        # offset_i = sum(durations[0..i-1]) - i * td  (each transition overlaps by td)
        cumulative_dur = 0.0
        for i in range(n - 1):
            cumulative_dur += clip_durations[i]
            # xfade starts at the end of clip i minus the transition overlap
            offset = cumulative_dur - (i + 1) * td
            offset = max(0.05, offset)

            out_v = f"[xv{i}]"
            out_a = f"[xa{i}]"

            filter_parts.append(
                f"{cur_v}{v_in[i+1]}xfade=transition={xfade_name}:"
                f"duration={td:.3f}:offset={offset:.3f}{out_v}"
            )
            filter_parts.append(
                f"{cur_a}{a_in[i+1]}acrossfade=d={td:.3f}:c1=tri:c2=tri{out_a}"
            )
            cur_v = out_v
            cur_a = out_a

        filter_complex = "; ".join(filter_parts)

        cmd = (
            [ffmpeg_exe, "-y"]
            + inputs
            + [
                "-filter_complex", filter_complex,
                "-map", cur_v,
                "-map", cur_a,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                str(out_path),
            ]
        )

        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and Path(out_path).exists():
            return True
        err = res.stderr.decode("utf-8", errors="ignore")
        print(f"  [WARN] xfade pass error: {err[-400:]}")
        return False

    except Exception as e:
        print(f"  [WARN] _xfade_pass exception: {e}")
        return False


def _concat_with_xfade(
    clip_paths: list,
    clip_durations: list,
    transition_type: str,
    transition_duration: float,
    ffmpeg_exe: str,
    out_path,
) -> bool:
    """
    Join scene clips with FFmpeg xfade (video) + acrossfade (audio) transitions.

    For N <= 8 clips: one filter_complex pass.
    For N > 8 clips: batch into groups of 8, merge each batch, then merge batches.
    This avoids filter_complex string length limits in FFmpeg for long videos.

    Returns True on success, False on any error (caller falls back to plain concat).
    """
    try:
        n = len(clip_paths)
        if n < 2:
            return False

        td = max(0.1, min(transition_duration, 0.8))

        xfade_map = {
            "fade":       "fade",
            "dissolve":   "dissolve",
            "fadeblack":  "fadeblack",
            "fadewhite":  "fadewhite",
            "wipeleft":   "wipeleft",
            "wiperight":  "wiperight",
            "slideleft":  "slideleft",
            "slideright": "slideright",
        }
        xfade_name = xfade_map.get(transition_type, "fade")

        BATCH = 8
        if n > BATCH:
            batch_outputs = []
            batch_durations_out = []
            tmp_dir = Path(out_path).parent
            bi = 0
            batch_index = 0
            while bi < n:
                batch_clips = clip_paths[bi: bi + BATCH]
                batch_durs  = clip_durations[bi: bi + BATCH]
                batch_out   = tmp_dir / f"xbatch_{batch_index:02d}.mp4"
                ok = _xfade_pass(batch_clips, batch_durs, xfade_name, td, ffmpeg_exe, batch_out)
                if not ok:
                    return False
                batch_outputs.append(str(batch_out))
                # Duration of merged batch = sum(durs) - (len-1)*td
                merged_dur = sum(batch_durs) - (len(batch_durs) - 1) * td
                batch_durations_out.append(max(0.5, merged_dur))
                bi += BATCH
                batch_index += 1

            if len(batch_outputs) == 1:
                shutil.copy2(batch_outputs[0], str(out_path))
                return True
            return _xfade_pass(batch_outputs, batch_durations_out, xfade_name, td, ffmpeg_exe, out_path)

        return _xfade_pass(clip_paths, clip_durations, xfade_name, td, ffmpeg_exe, out_path)

    except Exception as e:
        print(f"  [WARN] _concat_with_xfade exception: {e}")
        return False



def assemble_video(
    audio_files: list[str],
    image_files: list[str],
    output_path: str = None,
    script_data: dict = None,
    style: str = "Documentary",
    aspect_ratio: str = "16:9",
) -> str:
    """
    Assemble audio and image files into a professional MP4 video using FFmpeg.

    Args:
        audio_files:  List of paths to audio files (one per scene).
        image_files:  List of paths to image files (one per scene).
        output_path:  Path for the output video file (.mp4).
        script_data:  Optional script dict containing scenes narration & objectives.
        style:        Selected video style ("Documentary", "Educational", "Entertainment", "Motivational").

    Returns:
        The path to the generated MP4 video file.
    """
    if output_path is None:
        output_path = str(OUTPUT_DIR / "final_video.mp4")

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)


    if not image_files or not audio_files:
        print("  [WARN] Missing images or audio files, skipping video assembly.")
        return output_path

    # Load configuration settings
    settings = SettingsManager.load()
    style_profile = get_style_profile(style)

    enable_motion = settings.get("enable_motion_effects", True)
    enable_highlights = False  # Disabled: keyword highlight overlays removed
    enable_subtitles = settings.get("enable_subtitles", False)
    enable_transitions = settings.get("enable_transition_effects", True)
    enable_bg_music = settings.get("enable_bg_music", True)
    bg_music_vol = float(settings.get("bg_music_volume", 0.10))

    ffmpeg_exe = _get_ffmpeg_exe()
    work_dir = out_file.parent / f"temp_{out_file.stem}"
    work_dir.mkdir(parents=True, exist_ok=True)

    scenes = (script_data or {}).get("scenes", [])
    motion_types = style_profile.get("motion_types", ["zoom_in", "zoom_out", "pan_right", "pan_left"])
    zoom_speed = style_profile.get("zoom_speed", 0.0015)
    max_zoom = style_profile.get("max_zoom", 1.15)
    trans_type = style_profile.get("transition_type", "fade")
    trans_dur = style_profile.get("transition_duration", 0.5)

    scene_clips = []
    clip_durations = []

    # Determine resolution based on aspect ratio
    if aspect_ratio == "9:16":
        vid_w, vid_h = 1080, 1920
    else:
        vid_w, vid_h = 1920, 1080

    # 1. Build individual scene video clips with Motion + Text Highlights + Subtitles + Audio Sync
    for i, (img_path, aud_path) in enumerate(zip(image_files, audio_files)):
        clip_path = work_dir / f"clip_{i:02d}.mp4"
        aud_duration = _get_audio_duration(aud_path, ffmpeg_exe)
        clip_durations.append(aud_duration)

        # Get scene details if available
        scene = scenes[i] if i < len(scenes) else {}
        narration = scene.get("narration", "")
        objective = scene.get("objective", "")

        text_hl = _extract_text_highlight(narration, objective) if (enable_highlights and (i % 2 == 0 or i == 0)) else ""

        # Select motion type for scene
        motion_type = motion_types[i % len(motion_types)] if enable_motion else "static"

        # Build FFmpeg video filters
        vf_motion = _get_motion_vf(
            motion_type, aud_duration, fps=25, width=vid_w, height=vid_h,
            zoom_speed=zoom_speed, max_zoom=max_zoom
        )
        vf_text = _build_drawtext_filter(
            text_hl, narration, aud_duration,
            enable_highlight=enable_highlights,
            enable_subtitles=enable_subtitles,
            work_dir=work_dir,
            scene_idx=i
        )

        full_vf = f"{vf_motion},{vf_text}" if vf_text else vf_motion

        cmd = [
            ffmpeg_exe,
            "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", str(aud_path),
            "-vf", full_vf,
            "-r", "25",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{aud_duration:.2f}",
            str(clip_path),
        ]

        rendered_success = False
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            scene_clips.append(str(clip_path))
            rendered_success = True
            print(f"  [OK] Rendered dynamic scene clip {i+1}/{len(image_files)}: {clip_path.name} ({motion_type}, {aud_duration}s)")
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode("utf-8", errors="ignore")
            print(f"  [WARN] Dynamic filter failed on scene {i+1}, using fallback rendering: {err_msg[:80]}")

        # Fallback for scene clip if dynamic filters failed
        if not rendered_success:
            fallback_cmd = [
                ffmpeg_exe,
                "-y",
                "-loop", "1",
                "-i", str(img_path),
                "-i", str(aud_path),
                "-vf", f"scale={vid_w}:{vid_h}:force_original_aspect_ratio=decrease,pad={vid_w}:{vid_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p",
                "-r", "25",
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-t", f"{aud_duration:.2f}",
                str(clip_path),
            ]
            try:
                subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                scene_clips.append(str(clip_path))
                print(f"  [OK] Rendered fallback clip {i+1}/{len(image_files)}: {clip_path.name}")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"FFmpeg error on scene {i+1}: {err_msg[:120]}")

    # 2. Concat scene clips with optional xfade crossfade transitions
    raw_video_path = work_dir / "assembled_raw.mp4"

    xfade_success = False
    if enable_transitions and len(scene_clips) > 1:
        xfade_success = _concat_with_xfade(
            scene_clips, clip_durations, trans_type, trans_dur,
            ffmpeg_exe, raw_video_path
        )
        if xfade_success:
            print(f"  [OK] Clips joined with '{trans_type}' xfade transitions ({trans_dur}s each)")
        else:
            print(f"  [WARN] xfade transitions failed, falling back to plain concat")

    if not xfade_success:
        # Plain concat fallback
        concat_list_path = work_dir / "concat_list.txt"
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for clip in scene_clips:
                abs_p = Path(clip).resolve().as_posix().replace("'", "\'")
                f.write(f"file '{abs_p}'\n")

        concat_cmd = [
            ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list_path),
            "-c:v", "libx264", "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            str(raw_video_path),
        ]
        try:
            subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"  [OK] Scene clips concatenated (plain cut): {raw_video_path.name}")
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode("utf-8", errors="ignore")
            print(f"  [FAIL] Concat failed: {err_msg[:120]}")
            copy_concat_cmd = [
                ffmpeg_exe, "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list_path), "-c", "copy", str(raw_video_path)
            ]
            subprocess.run(copy_concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"  [OK] Scene clips concatenated via stream copy: {raw_video_path.name}")

    # Apply overall Video Fade In at beginning (1.0s) & Fade Out at end (1.0s)
    total_vid_duration = sum(clip_durations)
    fade_out_start = max(1.0, total_vid_duration - 1.0)
    faded_video_path = work_dir / "assembled_faded.mp4"
    fade_vf = f"fade=t=in:st=0:d=1.0,fade=t=out:st={fade_out_start:.2f}:d=1.0"

    fade_cmd = [
        ffmpeg_exe,
        "-y",
        "-i", str(raw_video_path),
        "-vf", fade_vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "copy",
        str(faded_video_path),
    ]
    
    video_to_mix = raw_video_path
    try:
        res = subprocess.run(fade_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and faded_video_path.exists():
            video_to_mix = faded_video_path
            print(f"  [OK] Applied fade-in (1s) and fade-out (1s) at {fade_out_start:.2f}s")
    except Exception as e:
        print(f"  [WARN] Video fade filter skipped: {e}")

    # 3. Optional Background Music Mixing
    mixed_video_path = str(out_file)
    bg_music_file = _find_bg_music_file() if enable_bg_music else ""

    if enable_bg_music and bg_music_file:
        mixed_success = _mix_background_music(
            str(video_to_mix), bg_music_file, bg_music_vol, ffmpeg_exe, mixed_video_path
        )
        if mixed_success:
            print(f"  [OK] Background music mixed at {int(bg_music_vol*100)}% volume: {Path(bg_music_file).name}")
        else:
            shutil.copy2(str(video_to_mix), mixed_video_path)
    else:
        shutil.copy2(str(video_to_mix), mixed_video_path)

    print(f"  [OK] Final video assembled with FFmpeg: {out_file.name}")


    # 4. Generate visual preview grid thumbnail
    try:
        images = [Image.open(f) for f in image_files]
        img_width, img_height = images[0].size

        MAX_PREVIEW_THUMBS = 20
        if len(images) > MAX_PREVIEW_THUMBS:
            step = len(images) / MAX_PREVIEW_THUMBS
            indices = [int(i * step) for i in range(MAX_PREVIEW_THUMBS)]
            images = [images[i] for i in indices]

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

        preview_path = str(out_file.with_name(f"{out_file.stem}_preview.jpg"))
        composite.save(preview_path, "JPEG", quality=90)
        print(f"  [OK] Video preview saved: {Path(preview_path).name} ({count} thumbnails)")
    except Exception as e:
        print(f"  [WARN] Could not create preview thumbnail: {e}")


    return str(out_file)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Assemble video from assets")
    parser.add_argument("--audio-dir", type=str, required=True, help="Directory with audio files")
    parser.add_argument("--image-dir", type=str, required=True, help="Directory with image files")
    parser.add_argument("--output", type=str, default=None, help="Output video file path")
    parser.add_argument("--style", type=str, default="Documentary", help="Video style")
    args = parser.parse_args()

    audio = sorted(
        glob.glob(str(Path(args.audio_dir) / "scene_*_audio.mp3")) +
        glob.glob(str(Path(args.audio_dir) / "scene_*_audio.wav"))
    )
    images = sorted(glob.glob(str(Path(args.image_dir) / "scene_*_visual.jpg")))

    result = assemble_video(audio, images, args.output, style=args.style)
    print(json.dumps({"video_path": result}, indent=2))

