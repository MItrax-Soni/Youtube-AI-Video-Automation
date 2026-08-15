"""
metadata_generator.py — YouTube Metadata Generation

Generates title, description, tags, and thumbnail text for a video using Google Gemini.

Phase 1: Returned templated metadata based on the topic and script.
Phase 5: Uses Gemini for SEO-optimized metadata with automatic fallback.
"""

import json
import re
import sys

from google import genai
from google.genai import types

from scripts.config import get_gemini_api_keys

# ---------------------------------------------------------------------------
# Gemini Prompt Template
# ---------------------------------------------------------------------------
METADATA_PROMPT = """You are a YouTube SEO expert and digital strategist. Generate optimized metadata for a YouTube video based on the script below.

Topic: {topic}
Tone: {tone}

Script Overview:
{script_summary}

IMPORTANT RULES:
1. Write a catchy, high-CTR YouTube title (max 70 chars).
2. Write a comprehensive, SEO-friendly video description. Include a call to action to subscribe, and relevant hashtags.
3. Generate a list of 10-15 relevant, high-ranking tags (single keywords or short phrases).
4. Create punchy thumbnail text (2-4 words) ideal for text overlays.
5. Return ONLY a valid JSON object with the exact keys: "title", "description", "tags", "thumbnail_text".

JSON Structure:
{{
  "title": "Optimized Video Title",
  "description": "Engaging description with key highlights...",
  "tags": ["tag1", "tag2", "tag3"],
  "thumbnail_text": "PUNCHY THUMBNAIL TEXT"
}}
"""


def _parse_gemini_response(response_text: str) -> dict:
    """Extract and parse JSON from Gemini's response."""
    text = response_text.strip()
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def _generate_with_gemini(topic: str, script: dict) -> dict:
    """Call Gemini API to generate SEO-optimized YouTube metadata.

    Rotates through all configured API keys and model fallbacks on 429 errors.
    """
    import time

    api_keys = get_gemini_api_keys()
    tone = script.get("tone", "educational")
    scenes = script.get("scenes", [])
    script_summary = "\n".join(
        [f"- Scene {s.get('scene_number', i+1)}: {s.get('narration', '')[:100]}..."
         for i, s in enumerate(scenes)]
    )

    prompt = METADATA_PROMPT.format(
        topic=topic,
        tone=tone,
        script_summary=script_summary
    )

    MODEL_CHAIN = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.6-flash",
    ]

    last_error = None

    for key_index, api_key in enumerate(api_keys):
        client = genai.Client(api_key=api_key)
        key_label = f"key {key_index + 1}/{len(api_keys)}"

        for model_name in MODEL_CHAIN:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.7,
                            max_output_tokens=1024,
                        ),
                    )
                    result = _parse_gemini_response(response.text)

                    # Validate required keys
                    for k in ["title", "description", "tags", "thumbnail_text"]:
                        if k not in result:
                            raise ValueError(f"Gemini metadata missing '{k}' key")

                    print(
                        f"  [OK] Metadata generated via {model_name} ({key_label})",
                        file=sys.stderr,
                    )
                    return result

                except Exception as e:
                    err_str = str(e)
                    last_error = e

                    is_quota_error = (
                        "429" in err_str
                        or "RESOURCE_EXHAUSTED" in err_str
                        or "quota" in err_str.lower()
                    )

                    if is_quota_error:
                        retry_delay = 30
                        m = re.search(r"retryDelay['\"]:\s*['\"](\d+)s", err_str)
                        if m:
                            retry_delay = int(m.group(1)) + 2

                        if attempt == 0:
                            print(
                                f"  [WARN] Metadata: {model_name} ({key_label}) quota exceeded. "
                                f"Waiting {retry_delay}s...",
                                file=sys.stderr,
                            )
                            time.sleep(retry_delay)
                        else:
                            break  # try next model
                    else:
                        raise  # non-quota error — surface immediately

    # All keys/models exhausted — raise so caller falls back to template
    raise RuntimeError(
        f"All Gemini API keys hit quota for metadata generation. "
        f"Last error: {last_error}"
    )


def _generate_templated(topic: str, script: dict) -> dict:
    """Generate templated metadata (fallback when Gemini is unavailable)."""
    tone = script.get("tone", "educational")
    scenes = script.get("scenes", [])
    num_scenes = len(scenes)

    title = script.get("title", f"{topic} -- Complete Guide")

    description = (
        f"In this {tone} video, we explore {topic}.\n\n"
        f"This video covers {num_scenes} key points to help you understand "
        f"everything you need to know about {topic}.\n\n"
        f"Key Topics Covered:\n"
    )

    for scene in scenes:
        narration = scene.get("narration", "")
        first_sentence = narration.split(".")[0].strip()
        if first_sentence:
            description += f"* {first_sentence}\n"

    description += (
        f"\nSubscribe for more {tone} content!\n"
        f"Like this video if you found it helpful.\n\n"
        f"#shorts #youtube #{topic.replace(' ', '').lower()}"
    )

    words = topic.lower().split()
    tags = [
        topic.lower(),
        f"{topic.lower()} explained",
        f"{topic.lower()} 2026",
        tone,
        "explained",
        "guide",
        "tutorial",
    ] + words

    seen = set()
    unique_tags = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    return {
        "title": title,
        "description": description,
        "tags": unique_tags,
        "thumbnail_text": topic.upper(),
    }


def generate_metadata(topic: str, script: dict) -> dict:
    """
    Generate YouTube metadata for the video.

    Attempts to use Gemini API for real AI optimization.
    Falls back to templated metadata if Gemini is unavailable.

    Args:
        topic:  The video topic.
        script: The script dict from script_generator.generate_script().

    Returns:
        A dict with title, description, tags, and thumbnail_text.
    """
    import sys
    try:
        metadata = _generate_with_gemini(topic, script)
        metadata["source"] = "gemini"
        print("  [OK] Metadata generated using Gemini API", file=sys.stderr)
        return metadata
    except Exception as e:
        print(f"  [WARN] Gemini metadata generation failed, using templated metadata: {e}", file=sys.stderr)
        metadata = _generate_templated(topic, script)
        metadata["source"] = "template"
        return metadata


# ---------------------------------------------------------------------------
# CLI entry point — allows calling from n8n via:
#   python -m scripts.metadata_generator --topic "AI" --script-file assets/script.json
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate YouTube metadata")
    parser.add_argument("--topic", type=str, required=True, help="Video topic")
    parser.add_argument(
        "--script-file",
        type=str,
        required=True,
        help="Path to script JSON file",
    )
    args = parser.parse_args()

    with open(args.script_file, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    metadata = generate_metadata(args.topic, script_data)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
