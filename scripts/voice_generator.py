"""
voice_generator.py — Text-to-Speech Narration

Converts scene narrations into audio files using gTTS (Google Text-to-Speech).

Phase 1: Generated silent WAV placeholders.
Phase 3: Uses gTTS for real narration. Falls back to silent WAV if gTTS fails.

gTTS produces MP3 files. The filename extension is .mp3.
FFmpeg (Phase 4) accepts MP3 directly, so no conversion is needed here.
"""

import json
import sys
import wave
from pathlib import Path

from scripts.config import ASSETS_DIR


def _create_silent_wav(path: str, duration_seconds: float, sample_rate: int = 22050):
    """
    Create a silent WAV file of the given duration.

    Used as a fallback when gTTS is unavailable or fails.
    """
    num_samples = int(sample_rate * duration_seconds)
    with wave.open(path, "w") as wav_file:
        wav_file.setnchannels(1)       # Mono
        wav_file.setsampwidth(2)       # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * num_samples)


def _generate_gtts(text: str, output_path: str) -> bool:
    """
    Generate an MP3 audio file from text using gTTS.

    Args:
        text:        The narration text to convert to speech.
        output_path: File path to save the MP3 (should end in .mp3).

    Returns:
        True on success, False on failure.
    """
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"  [WARN] gTTS failed: {e}")
        return False


def generate_voice(script: dict, output_dir: str = None) -> list[str]:
    """
    Generate audio files for each scene's narration using gTTS.

    Attempts to use gTTS for real speech synthesis. Falls back to a silent
    WAV placeholder if gTTS fails for any scene.

    Args:
        script:     The script dict from script_generator.generate_script().
        output_dir: Directory to save audio files. Defaults to assets/.

    Returns:
        A list of file paths to the generated audio files, one per scene.
        Files are MP3 (gTTS) or WAV (fallback silent).
    """
    if output_dir is None:
        output_dir = str(ASSETS_DIR)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    audio_files = []

    for scene in script.get("scenes", []):
        scene_num = scene["scene_number"]
        duration = scene.get("duration_seconds", 5)
        narration = scene.get("narration", "").strip()

        if not narration:
            narration = f"Scene {scene_num}."

        # Try gTTS first — saves as MP3
        mp3_path = str(out_path / f"scene_{scene_num:02d}_audio.mp3")
        success = _generate_gtts(narration, mp3_path)

        if success:
            audio_files.append(mp3_path)
            print(f"  [OK] Audio for scene {scene_num}: scene_{scene_num:02d}_audio.mp3 (gTTS)")
        else:
            # Fallback: silent WAV with correct duration
            wav_path = str(out_path / f"scene_{scene_num:02d}_audio.wav")
            _create_silent_wav(wav_path, duration)
            audio_files.append(wav_path)
            print(f"  [OK] Audio for scene {scene_num}: scene_{scene_num:02d}_audio.wav (silent fallback, {duration}s)")

    return audio_files


# ---------------------------------------------------------------------------
# CLI entry point — allows calling from n8n via:
#   python -m scripts.voice_generator --script-file assets/script.json
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate voice narration")
    parser.add_argument(
        "--script-file",
        type=str,
        required=True,
        help="Path to script JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save audio files",
    )
    args = parser.parse_args()

    with open(args.script_file, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    files = generate_voice(script_data, args.output_dir)
    print(json.dumps({"audio_files": files}, indent=2))
