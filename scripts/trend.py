"""
trend.py — Trending Topic Discovery

Suggests video topics based on a niche/category using Google Gemini.

Falls back to hardcoded sample topics if the Gemini API key is not configured.
"""

import json
import re
import sys

from google import genai
from google.genai import types

from scripts.config import get_gemini_api_key

# ---------------------------------------------------------------------------
# Gemini Prompt Template
# ---------------------------------------------------------------------------
TREND_PROMPT = """You are a YouTube content strategist. Suggest 5 trending and engaging video topic ideas for the following niche.

Niche: {niche}

IMPORTANT RULES:
1. Each topic should be specific, clickable, and suitable for a YouTube video title.
2. Topics should feel current and timely for 2026.
3. Mix evergreen topics with trending subjects.
4. Each topic should be a single, concise sentence or phrase.
5. Return ONLY a JSON array of strings, no other text.

Example format:
["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"]
"""

# ---------------------------------------------------------------------------
# Fallback sample topics (used when Gemini API key is not configured)
# ---------------------------------------------------------------------------
SAMPLE_TOPICS = {
    "technology": [
        "How AI is Changing Software Development in 2026",
        "Top 5 Programming Languages to Learn This Year",
        "What is Quantum Computing? Explained Simply",
        "The Future of Wearable Technology",
        "How Blockchain Works Beyond Cryptocurrency",
    ],
    "science": [
        "Why Black Holes Are the Strangest Objects in the Universe",
        "How CRISPR is Editing the Future of Medicine",
        "The Science Behind Climate Change",
        "5 Unsolved Mysteries in Physics",
        "How Your Brain Makes Decisions",
    ],
    "education": [
        "How to Study Effectively Using the Feynman Technique",
        "Top 10 Free Online Learning Platforms",
        "Why Most Students Fail at Time Management",
        "The History of the Internet in 10 Minutes",
        "How Memory Works and How to Improve It",
    ],
    "general": [
        "10 Habits of Highly Productive People",
        "How to Start a YouTube Channel in 2026",
        "The Psychology of Procrastination",
        "Minimalism: Living More with Less",
        "How to Build a Morning Routine That Works",
    ],
}


def _parse_gemini_response(response_text: str) -> list[str]:
    """
    Extract and parse a JSON array from Gemini's response.

    Handles cases where the model wraps JSON in markdown code fences.
    """
    text = response_text.strip()

    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    result = json.loads(text)

    # Ensure we got a list of strings
    if not isinstance(result, list):
        raise ValueError("Expected a JSON array of strings")

    return [str(item) for item in result]


def _discover_with_gemini(niche: str) -> list[str]:
    """
    Call Gemini API to generate trending topic suggestions.

    Uses the new google.genai SDK (google-genai package).
    Returns a list of topic strings, or raises an exception on failure.
    """
    api_key = get_gemini_api_key()
    client = genai.Client(api_key=api_key)

    prompt = TREND_PROMPT.format(niche=niche)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.9,  # Higher temperature for creative suggestions
            max_output_tokens=512,
        ),
    )

    return _parse_gemini_response(response.text)


def discover_trends(niche: str = "general") -> list[str]:
    """
    Return a list of trending topic suggestions for the given niche.

    Attempts to use Gemini API for real AI-generated suggestions.
    Falls back to hardcoded topics if the API key is missing or the call fails.

    Args:
        niche: Category of topics (e.g., "technology", "science").
               Falls back to "general" if the niche is not recognized.

    Returns:
        A list of topic strings.
    """
    niche_lower = niche.lower().strip()

    try:
        topics = _discover_with_gemini(niche_lower)
        print(f"  [OK] Trends generated using Gemini API for niche: {niche_lower}")
        return topics
    except ValueError:
        # API key not configured -- fall back silently
        pass
    except Exception as e:
        print(f"  [WARN] Gemini trend discovery failed, using fallback: {e}")

    # Fallback to hardcoded topics
    return SAMPLE_TOPICS.get(niche_lower, SAMPLE_TOPICS["general"])


# ---------------------------------------------------------------------------
# CLI entry point -- allows calling from n8n via:
#   python -m scripts.trend --niche technology
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Discover trending topics")
    parser.add_argument(
        "--niche",
        type=str,
        default="general",
        help="Topic niche (technology, science, education, general)",
    )
    args = parser.parse_args()

    topics = discover_trends(args.niche)
    print(json.dumps({"niche": args.niche, "topics": topics}, indent=2, ensure_ascii=False))
