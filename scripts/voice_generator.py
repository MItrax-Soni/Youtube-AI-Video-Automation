"""
voice_generator.py — Text-to-Speech Narration

Converts scene narrations into audio files supporting Edge-TTS (Neural),
ElevenLabs (Premium), and gTTS (Standard) with Male and Female voice gender options.
"""

import asyncio
import json
import sys
import wave
from pathlib import Path

import requests

from scripts.config import ASSETS_DIR, get_elevenlabs_api_key


# ---------------------------------------------------------------------------
# Voice Voice-ID / Voice-Name Mappings
# ---------------------------------------------------------------------------
EDGE_TTS_VOICES = {
    "english": {
        "male": "en-US-GuyNeural",
        "female": "en-US-JennyNeural",
    },
    "hindi": {
        "male": "hi-IN-MadhurNeural",
        "female": "hi-IN-SwaraNeural",
    },
    "gujarati": {
        "male": "gu-IN-NiranjanNeural",
        "female": "gu-IN-DhwaniNeural",
    },
}

ELEVENLABS_VOICES = {
    "male": "pNInz6obpgDQGcFmaJgB",   # Adam
    "female": "21m00Tcm4TlvDq8ikWAM", # Rachel
}

GTTS_LANG_MAP = {
    "english": "en",
    "hindi": "hi",
    "gujarati": "gu",
}

GTTS_TLDS = {
    "male": "co.uk",
    "female": "com",
}


def _create_silent_wav(path: str, duration_seconds: float, sample_rate: int = 22050):
    """
    Create a silent WAV file of the given duration as fallback.
    """
    num_samples = int(sample_rate * duration_seconds)
    with wave.open(path, "w") as wav_file:
        wav_file.setnchannels(1)       # Mono
        wav_file.setsampwidth(2)       # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * num_samples)


def _generate_edge_tts(text: str, output_path: str, voice_name: str) -> bool:
    """
    Generate an MP3 audio file using Edge-TTS (Microsoft Neural Voice).
    """
    try:
        import edge_tts
        communicator = edge_tts.Communicate(text, voice_name)
        asyncio.run(communicator.save(output_path))
        return True
    except Exception as e:
        print(f"  [WARN] Edge-TTS failed ({voice_name}): {e}")
        return False


def _generate_elevenlabs(text: str, output_path: str, voice_id: str) -> bool:
    """
    Generate an MP3 audio file using ElevenLabs REST API.
    """
    try:
        api_key = get_elevenlabs_api_key()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        response = requests.post(url, json=data, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
        else:
            print(f"  [WARN] ElevenLabs HTTP {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"  [WARN] ElevenLabs API error: {e}")
        return False


def _generate_gtts(text: str, output_path: str, lang: str = "en", tld: str = "com") -> bool:
    """
    Generate an MP3 audio file using gTTS.
    """
    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"  [WARN] gTTS failed: {e}")
        return False


def generate_voice(
    script: dict,
    output_dir: str = None,
    voice_gender: str = "female",
    voice_engine: str = "Edge-TTS (Neural)",
    language: str = "english",
) -> list[str]:
    """
    Generate audio files for each scene's narration.

    Args:
        script:       The script dict from script_generator.generate_script().
        output_dir:   Directory to save audio files. Defaults to assets/.
        voice_gender: "male" or "female" (case-insensitive).
        voice_engine: Engine choice ("Edge-TTS (Neural)", "gTTS (Standard)", "ElevenLabs (Premium)").
        language:     Language for TTS ("english", "hindi", "gujarati").

    Returns:
        List of audio file paths.
    """
    if output_dir is None:
        output_dir = str(ASSETS_DIR)

    gender_key = voice_gender.lower().strip()
    if gender_key not in ["male", "female"]:
        gender_key = "female"

    lang_key = language.lower().strip()
    if lang_key not in EDGE_TTS_VOICES:
        lang_key = "english"

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    audio_files = []
    engine_name = voice_engine.lower()

    # Get language-specific voices
    lang_voices = EDGE_TTS_VOICES.get(lang_key, EDGE_TTS_VOICES["english"])
    gtts_lang_code = GTTS_LANG_MAP.get(lang_key, "en")

    for scene in script.get("scenes", []):
        scene_num = scene["scene_number"]
        duration = scene.get("duration_seconds", 5)
        narration = scene.get("narration", "").strip()

        if not narration:
            narration = f"Scene {scene_num}."

        mp3_path = str(out_path / f"scene_{scene_num:02d}_audio.mp3")
        success = False
        used_engine = "silent fallback"

        # 1. Attempt ElevenLabs
        if "elevenlabs" in engine_name:
            if lang_key in ["english", "hindi"]:
                v_id = ELEVENLABS_VOICES.get(gender_key, ELEVENLABS_VOICES["female"])
                success = _generate_elevenlabs(narration, mp3_path, v_id)
                if success:
                    used_engine = f"ElevenLabs ({gender_key.title()})"
            else:
                print(f"  [WARN] ElevenLabs optimal for English/Hindi. Falling back to Edge-TTS for {lang_key}.")

        # 2. Attempt gTTS
        if not success and "gtts" in engine_name:
            tld = GTTS_TLDS.get(gender_key, "com")
            success = _generate_gtts(narration, mp3_path, lang=gtts_lang_code, tld=tld)
            if success:
                used_engine = f"gTTS ({lang_key.title()} {gender_key.title()})"

        # 3. Attempt Edge-TTS (Primary or Fallback)
        if not success:
            v_name = lang_voices.get(gender_key, lang_voices["female"])
            success = _generate_edge_tts(narration, mp3_path, v_name)
            if success:
                used_engine = f"Edge-TTS ({lang_key.title()} {gender_key.title()})"


        if success:
            audio_files.append(mp3_path)
            print(f"  [OK] Audio scene {scene_num}: scene_{scene_num:02d}_audio.mp3 [{used_engine}]")
        else:
            # Silent fallback
            wav_path = str(out_path / f"scene_{scene_num:02d}_audio.wav")
            _create_silent_wav(wav_path, duration)
            audio_files.append(wav_path)
            print(f"  [OK] Audio scene {scene_num}: scene_{scene_num:02d}_audio.wav [silent fallback {duration}s]")

    return audio_files


# ---------------------------------------------------------------------------
# CLI entry point
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
    parser.add_argument(
        "--gender",
        type=str,
        default="female",
        choices=["male", "female"],
        help="Voice gender",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="Edge-TTS (Neural)",
        help="Voice engine",
    )
    parser.add_argument(
        "--language",
        type=str,
        default="english",
        help="Language for narration",
    )
    args = parser.parse_args()

    with open(args.script_file, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    files = generate_voice(script_data, args.output_dir, args.gender, args.engine, args.language)
    print(json.dumps({"audio_files": files}, indent=2))

