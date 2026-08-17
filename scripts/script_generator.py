"""
script_generator.py — AI-Powered Dynamic Script Generation

Generates a fully dynamic YouTube script using Google Gemini.

The AI decides:
  - Storytelling structure (documentary, chronological, mystery, tutorial, etc.)
  - Number of scenes (based on content richness and duration)
  - Pacing and scene order
  - Transitions and narrative flow

No fixed Hook → Introduction → Main → Conclusion template is enforced.
Each topic produces a unique, human-sounding script.

Each scene contains:
  - narration:      conversational, human-like script text
  - visual_prompt:  highly specific, cinematic B-roll / image prompt
  - objective:      what this scene achieves for the viewer
  - transition:     how the scene flows into the next
  - duration_seconds: per-scene timing
"""

import json
import re
import sys

from google import genai
from google.genai import types

from scripts.config import get_gemini_api_keys, get_scene_count, get_duration_word_bounds

# ---------------------------------------------------------------------------
# Gemini Prompt Template — Structured YouTube Script
# ---------------------------------------------------------------------------
SCRIPT_PROMPT = """You are an elite YouTube scriptwriter, researcher, storyteller, and content strategist with over 20 years of experience creating viral videos across every niche — technology, AI, finance, business, history, science, medicine, education, documentaries, biographies, psychology, geopolitics, self-improvement, entertainment, and storytelling.

Your job is NOT to fill a template. Your job is to THINK like an experienced human creator.

Every topic deserves its own storytelling style. Never force a fixed structure. Never reuse the same flow simply because two topics belong to the same category.

Your writing should feel like it came from an expert YouTube creator, not an AI.

==================================================
INPUTS
==================================================

Topic: {topic}
Tone: {tone}
Target Duration: {duration} seconds
Target Word Count: {min_words} to {max_words} total narration words

==================================================
CRITICAL TONE ACCURACY RULE
==================================================

The requested Tone is: "{tone}". 
You MUST radically alter your vocabulary, pacing, sentence structure, and emotional delivery to match this Tone EXACTLY. 
If the tone is "Dramatic", the script must be filled with tension, heavy pauses, and serious implications. 
If the tone is "Energetic", it must be fast-paced, punchy, and highly enthusiastic. 
If the tone is "Friendly", it must feel like a warm, casual conversation with a close friend.
Do NOT default to a generic "YouTube voice". Your entire script's personality must be dictated by the requested Tone.

==================================================
CRITICAL DURATION ACCURACY RULE
==================================================

Standard narration speaking pace is ~2.3 words per second.
To ensure the generated video duration is accurate to {duration} seconds:
• The total combined word count of all scene narrations MUST be between {min_words} and {max_words} words.
• Do NOT exceed {max_words} words or drop below {min_words} words.
• Each scene's duration_seconds must accurately reflect the speaking time of its narration.

==================================================
THINK BEFORE WRITING
==================================================

Before writing a single word of narration, analyze internally:

• What is this topic really about — and what does the audience NOT expect to hear?
• Who is watching? Curious beginners? Experts? Casual viewers?
• What emotion does this topic trigger — awe, urgency, curiosity, fear, inspiration?
• What storytelling structure fits BEST? Chronological journey? Mystery reveal? Problem → discovery? Case study? Documentary? Debate? Experiment?
• What is the single most surprising or counterintuitive insight this topic offers?
• Where should tension be built? Where should it be released?
• Which pieces of information should be withheld to build suspense?
• What pacing keeps viewers from clicking away?

Decide the structure yourself. Do not expose this reasoning in output.

==================================================
DYNAMIC STRUCTURE — NO FIXED FORMAT
==================================================

Do NOT default to: Hook → Introduction → Main Content → Conclusion → CTA

That structure is allowed only when it genuinely fits. Instead, determine the best format for THIS specific topic:

- History / Biography → chronological journey with emotional beats
- Science / Medicine → concept-first, then implications, then surprising edge cases
- Finance / Economics → problem → analysis → solution → warning
- Technology / AI → evolution → current state → what comes next
- Psychology / Behavior → relatable scenario → mechanism → real-world consequence
- Mystery / Conspiracy → clues revealed gradually, never predictably
- Documentary style → cinematic narrative with immersive descriptions
- Tutorial / How-to → progressive steps with embedded "why it works" explanations
- Comparison → contrasting naturally, not in a list-reading style
- Motivation / Self-help → emotional arc from struggle to clarity to action

The AI decides the best structure for each topic.

==================================================
SCENE COUNT
==================================================

Generate ONLY the number of scenes that serve the content naturally.

Approximate guidance (adjust based on content richness):
• 15–30 seconds → 2 to 4 scenes
• 30–60 seconds → 4 to 7 scenes
• 60–120 seconds → 6 to 10 scenes
• 2–5 minutes → 10 to 18 scenes
• 5–10 minutes → 18 to 28 scenes
• 10–20 minutes → 28 to 45 scenes
• 20+ minutes → 45+ scenes

Every scene must exist for a reason. Every scene must introduce NEW value. Never add filler to reach a count.

==================================================
STORYTELLING RULES
==================================================

• Write as if speaking to ONE viewer — never a crowd.
• Avoid textbook language, robotic phrasing, or filler words.
• Build curiosity. Delay answers strategically. Reward patience.
• Create open loops that pull the viewer forward.
• Vary sentence length naturally — short punches, longer explanations, occasional questions.
• Every sentence should make the viewer want to hear the next one.
• Introduce surprising information when least expected.

==================================================
FORBIDDEN PHRASES
==================================================

Never use these phrases or close variants:

"Welcome back" / "Welcome to" / "In today's video" / "Today we're going to" /
"Let's talk about" / "Moving on" / "Another important thing" / "As we can see" /
"It's worth noting" / "In conclusion" / "Finally" / "The future is bright" /
"One interesting fact" / "Let's dive in" / "Without further ado"

Create every transition fresh and specific to the content.

==================================================
TOPIC-ADAPTIVE WRITING STYLE
==================================================

AI / Technology → visionary, forward-looking, slightly urgent
History → cinematic, with human detail and consequence
Medicine / Health → clear, careful, empathetic
Finance → precise, analytical, with a strategic edge
Psychology → relatable, pattern-revealing, slightly provocative
Documentary → immersive, present-tense narration, cinematic texture
Biography → personal, emotional, showing private moments
Science → curiosity-driven, layered reveals, wonder-inducing
Mystery → suspenseful, gradual disclosure, controlled tension
Tutorial → instructional but energetic, never dry
Motivation → emotional arc, honest, direct, no clichés

==================================================
VISUAL PROMPT RULES
==================================================

Every scene must include ONE highly specific, cinematically useful visual prompt.

Bad: "Technology" / "AI concept" / "People working"
Good: "Close-up of a neurosurgeon's gloved hands guiding a robotic surgical arm in a sterile operating room, blue surgical lighting, slow zoom out"

Visuals must be:
• Unique per scene (never repeat)
• Usable for stock footage, AI image generation, or B-roll
• Highly specific — not generic
• Directly tied to the narration content

==================================================
STOCK FOOTAGE SEARCH QUERIES (CRITICAL)
==================================================

For every scene, you MUST also generate 2–3 stock-footage search queries in the "visual_queries" field.

These are NOT the same as visual_prompt. These are SHORT, LITERAL search queries designed to find relevant stock photos/videos on a stock footage platform like Pexels.

RULES:
• Queries must describe the REAL-WORLD SUBJECT of the narration — what a viewer should SEE while listening.
• Do NOT use cinematic terms (close-up, zoom, pan, lighting, shot, camera, b-roll).
• Do NOT use abstract concepts (AI concept, technology, innovation, future).
• DO describe concrete, searchable subjects (people, objects, actions, places).
• Each query should be 3–6 words, specific and literal.
• Order queries from most specific to broadest fallback.
• Each scene's queries must be DIFFERENT from every other scene's queries.

EXAMPLE — Good vs Bad:

Narration: "AI agents can automatically analyze thousands of financial documents."

BAD queries: ["AI", "AI technology", "futuristic robot"]
GOOD queries: ["financial analyst reviewing documents", "business financial reports computer", "document analysis office"]

Narration: "Electric vehicles are becoming cheaper because battery manufacturing is scaling rapidly."

BAD queries: ["electric car", "person driving", "technology"]
GOOD queries: ["electric vehicle battery factory", "lithium battery manufacturing", "EV assembly line production"]

Narration: "Doctors are using AI to analyze medical scans."

BAD queries: ["AI technology medical", "robot doctor"]
GOOD queries: ["doctor examining medical scan", "radiology MRI analysis", "medical imaging hospital"]

The search queries must represent the VISUAL MEANING of what the narrator is describing — what should appear on screen.

==================================================
FACTUAL ACCURACY
==================================================

• Never invent facts, quotes, or statistics.
• If uncertain, use broadly accepted knowledge.
• Never fabricate specific numbers — use approximate ranges if needed.

==================================================
OUTPUT FORMAT — STRICT JSON ONLY
==================================================

Return ONLY valid JSON. No markdown. No code fences. No explanations. No extra text before or after.

{{
  "title": "compelling YouTube video title",
  "summary": "one sentence describing the video's core value to the viewer",
  "storytelling_style": "describe the chosen narrative structure and why it fits this topic",
  "estimated_duration_seconds": {duration},
  "scenes": [
    {{
      "scene_number": 1,
      "objective": "what this scene achieves for the viewer",
      "narration": "full narration text for this scene",
      "visual_prompt": "highly specific, cinematically descriptive visual prompt",
      "visual_queries": ["specific stock footage search query 1", "broader stock footage search query 2", "broadest fallback query 3"],
      "transition": "how this scene flows into the next",
      "duration_seconds": 12
    }}
  ]
}}

The sum of all scene duration_seconds must equal approximately {duration}.

The script must be indistinguishable from one written by a world-class human YouTube creator.
"""



# ---------------------------------------------------------------------------
# Mock scene templates — structured YouTube format
# ---------------------------------------------------------------------------
MOCK_TEMPLATES = {
    "hook": {
        "narration": (
            "Did you know that {topic} is one of the fastest-growing fields "
            "in the world right now? In the next few minutes, you'll discover "
            "exactly why."
        ),
        "visual_prompt": "Dramatic wide shot of {topic_keyword} technology in action with cinematic lighting",
        "visual_queries": ["{topic_keyword} in action", "{topic_keyword} demonstration", "{topic_keyword} overview"],
    },
    "introduction": {
        "narration": (
            "Welcome to this video. Today we're diving deep into {topic}. "
            "Whether you're a complete beginner or already familiar with the "
            "basics, there's something here for everyone. Let's get started."
        ),
        "visual_prompt": "Modern workspace with {topic_keyword} related content displayed on multiple screens",
        "visual_queries": ["{topic_keyword} workspace computer", "modern office multiple screens", "professional working desk setup"],
    },
    "main_content": [
        {
            "narration": (
                "Let's start with the fundamentals. Understanding the core "
                "concepts behind {topic} is essential before we can appreciate "
                "its real impact."
            ),
            "visual_prompt": "Detailed diagram explaining {topic_keyword} fundamentals on a whiteboard",
            "visual_queries": ["{topic_keyword} explanation whiteboard", "{topic_keyword} fundamentals diagram", "educational presentation concept"],
        },
        {
            "narration": (
                "One of the most exciting aspects of {topic} is how it's being "
                "applied in real-world scenarios right now. Companies and "
                "researchers are making breakthroughs every day."
            ),
            "visual_prompt": "Team of researchers working with {topic_keyword} equipment in a modern lab",
            "visual_queries": ["researchers working laboratory", "{topic_keyword} research team", "scientists modern lab equipment"],
        },
        {
            "narration": (
                "Let's look at the numbers. The data behind {topic} tells a "
                "compelling story about where things are headed."
            ),
            "visual_prompt": "Data visualization dashboard showing {topic_keyword} growth statistics",
            "visual_queries": ["data analytics dashboard screen", "growth statistics chart", "business data visualization"],
        },
        {
            "narration": (
                "Here's where things get really interesting. Recent innovations "
                "in {topic} have opened up possibilities that were unimaginable "
                "just a few years ago."
            ),
            "visual_prompt": "Futuristic technology demonstration related to {topic_keyword}",
            "visual_queries": ["{topic_keyword} innovation technology", "modern technology breakthrough", "cutting edge {topic_keyword}"],
        },
        {
            "narration": (
                "There are some common misconceptions about {topic} that we "
                "need to address. Understanding what it really is helps separate "
                "the hype from reality."
            ),
            "visual_prompt": "Side-by-side comparison showing common myths versus facts about {topic_keyword}",
            "visual_queries": ["fact check comparison", "myth versus reality", "truth about {topic_keyword}"],
        },
        {
            "narration": (
                "Looking at how {topic} compares to traditional approaches, "
                "the advantages become clear. The evolution has been remarkable."
            ),
            "visual_prompt": "Timeline infographic showing the evolution of {topic_keyword} over the years",
            "visual_queries": ["{topic_keyword} evolution timeline", "progress comparison old new", "technology advancement history"],
        },
        {
            "narration": (
                "Experts in the field have identified several key challenges "
                "that {topic} still faces. Understanding these challenges helps "
                "us see the complete picture."
            ),
            "visual_prompt": "Professional conference panel discussing {topic_keyword} challenges",
            "visual_queries": ["professional conference panel discussion", "experts meeting boardroom", "industry leaders debate"],
        },
        {
            "narration": (
                "Here's a practical example of {topic} in action. Seeing it "
                "work in a real scenario makes everything click into place."
            ),
            "visual_prompt": "Step-by-step demonstration of {topic_keyword} being used in practice",
            "visual_queries": ["{topic_keyword} practical demonstration", "hands on {topic_keyword} work", "step by step process"],
        },
        {
            "narration": (
                "The impact of {topic} extends beyond just technology. It's "
                "changing how people think about everyday problems and solutions."
            ),
            "visual_prompt": "Diverse group of people benefiting from {topic_keyword} in daily life",
            "visual_queries": ["people using {topic_keyword} daily life", "diverse group technology users", "everyday life improvement"],
        },
        {
            "narration": (
                "As we look ahead, the future of {topic} is incredibly "
                "promising. New developments are being announced almost weekly."
            ),
            "visual_prompt": "Futuristic cityscape with {topic_keyword} technology integrated into infrastructure",
            "visual_queries": ["futuristic city technology", "modern smart city", "future urban infrastructure"],
        },
        {
            "narration": (
                "Here are some practical tips you can use right away to get "
                "started with {topic}, even if you're a complete beginner."
            ),
            "visual_prompt": "Clean checklist or step-by-step guide for getting started with {topic_keyword}",
            "visual_queries": ["checklist getting started", "beginner guide tutorial", "step by step instructions notebook"],
        },
        {
            "narration": (
                "Many industry leaders are already investing heavily in {topic}. "
                "The trend shows no signs of slowing down."
            ),
            "visual_prompt": "Business leaders and investors discussing {topic_keyword} strategy in a boardroom",
            "visual_queries": ["business leaders boardroom meeting", "investors strategy discussion", "corporate meeting presentation"],
        },
        {
            "narration": (
                "The community around {topic} is growing rapidly. Collaboration "
                "and open sharing of ideas are driving innovation forward."
            ),
            "visual_prompt": "Online community or meetup event focused on {topic_keyword}",
            "visual_queries": ["community meetup event", "people collaborating together", "team brainstorming ideas"],
        },
        {
            "narration": (
                "Let's talk about the tools and resources available for {topic}. "
                "Having the right tools makes all the difference."
            ),
            "visual_prompt": "Collection of software tools and resources for working with {topic_keyword}",
            "visual_queries": ["software tools computer screen", "digital tools resources", "professional toolkit workspace"],
        },
        {
            "narration": (
                "What makes {topic} unique compared to similar fields is its "
                "ability to adapt and evolve rapidly. This flexibility is key."
            ),
            "visual_prompt": "Abstract visualization showing {topic_keyword} adaptability and flexibility",
            "visual_queries": ["{topic_keyword} flexibility adaptation", "evolving technology process", "agile transformation"],
        },
        {
            "narration": (
                "Education in {topic} is becoming more accessible than ever. "
                "There are courses, tutorials, and communities for every level."
            ),
            "visual_prompt": "Students learning about {topic_keyword} in a modern classroom or online setting",
            "visual_queries": ["students learning classroom", "online education computer", "person studying tutorial"],
        },
        {
            "narration": (
                "The ethical considerations around {topic} are important to "
                "discuss. Responsible development benefits everyone."
            ),
            "visual_prompt": "Thoughtful discussion panel about ethics and responsibility in {topic_keyword}",
            "visual_queries": ["ethics discussion panel", "responsible development team", "thoughtful professional conversation"],
        },
        {
            "narration": (
                "Success stories in {topic} are inspiring more people to get "
                "involved. Each breakthrough creates new opportunities."
            ),
            "visual_prompt": "Celebration of a successful {topic_keyword} project with a diverse team",
            "visual_queries": ["team celebrating success", "project achievement celebration", "diverse team accomplishment"],
        },
    ],
    "conclusion": {
        "narration": (
            "So there you have it. {topic} is not just a buzzword. It's a "
            "transformative force that's reshaping how we think about the "
            "world. The key takeaways are clear: understanding the fundamentals, "
            "staying current with developments, and getting hands-on experience "
            "are the best ways to stay ahead."
        ),
        "visual_prompt": "Elegant summary graphic with key points about {topic_keyword} highlighted",
        "visual_queries": ["summary key points presentation", "conclusion recap highlights", "key takeaways screen"],
    },
    "cta": {
        "narration": (
            "Thanks for watching! If you found this video helpful, hit the "
            "like button and subscribe to the channel for more content on "
            "{topic} and related topics. Drop a comment below with your "
            "thoughts and I'll see you in the next one."
        ),
        "visual_prompt": "Animated end screen with subscribe button and related video suggestions",
        "visual_queries": ["subscribe button end screen", "social media engagement", "video outro end card"],
    },
}



def _parse_gemini_response(response_text: str) -> dict:
    """
    Extract and parse JSON from Gemini's response.

    Handles cases where the model wraps JSON in markdown code fences.
    """
    text = response_text.strip()

    # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    return json.loads(text)


def _generate_with_gemini(topic: str, tone: str, duration: int, language: str = "english") -> dict:
    """
    Call Gemini API to generate a dynamic video script.

    Uses the new google.genai SDK (google-genai package).
    The model decides the storytelling structure, scene count, and pacing
    based on the topic — no hardcoded format is imposed.

    Handles 429 RESOURCE_EXHAUSTED automatically:
      - Waits the retry delay advertised in the error
      - Rotates through all configured API keys
      - Falls back through a model chain per key if quota is still exceeded

    Returns the parsed script dict, or raises an exception on failure.
    """
    import time

    api_keys = get_gemini_api_keys()
    min_w, max_w = get_duration_word_bounds(duration)

    prompt = SCRIPT_PROMPT.format(
        topic=topic,
        tone=tone,
        duration=duration,
        min_words=min_w,
        max_words=max_w,
    )

    # Add language instruction if not English
    lang_key = language.lower().strip()
    if lang_key != "english":
        lang_map = {"hindi": "Hindi (हिन्दी)", "gujarati": "Gujarati (ગુજરાતી)"}
        lang_name = lang_map.get(lang_key, language)
        prompt = (
            f"IMPORTANT LANGUAGE INSTRUCTION: Write ALL narration text in {lang_name}. "
            f"The visual_prompt fields should still be in English for Pexels search compatibility. "
            f"The title and summary should be in {lang_name}. "
            f"The objective and transition fields can be in English.\n\n"
            + prompt
        )


    # Model fallback chain — newest/most capable first, lighter fallbacks
    # NOTE: gemini-1.5-flash and gemini-1.5-flash-8b are removed from v1beta API
    MODEL_CHAIN = [
        "gemini-2.5-flash",       # primary flash model
        "gemini-2.5-flash-lite",  # light fallback
        "gemini-3.6-flash",       # fallback
    ]

    last_error = None

    # Timeout wrapper — prevents Gemini API calls from hanging forever
    # on slow cloud networks (Render free tier).
    import concurrent.futures
    API_TIMEOUT = 90  # seconds max per API call

    def _call_gemini(client, model_name, prompt_text):
        """Call Gemini API — runs inside a thread so we can enforce a timeout."""
        return client.models.generate_content(
            model=model_name,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                temperature=0.85,
                max_output_tokens=8192,
            ),
        )

    for key_index, api_key in enumerate(api_keys):
        client = genai.Client(api_key=api_key)
        key_label = f"key {key_index + 1}/{len(api_keys)}"

        for model_name in MODEL_CHAIN:
            try:
                print(
                    f"  [INFO] Trying model: {model_name} ({key_label})",
                    file=sys.stderr,
                )

                # Run the API call with a hard timeout
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(_call_gemini, client, model_name, prompt)
                    response = future.result(timeout=API_TIMEOUT)

                # Success — parse and validate
                result = _parse_gemini_response(response.text)

                # Validate required top-level structure
                if "scenes" not in result:
                    raise ValueError("Gemini response missing 'scenes' key")
                if not isinstance(result["scenes"], list) or len(result["scenes"]) == 0:
                    raise ValueError("Gemini returned an empty scenes list")

                # Normalize each scene — ensure all expected fields exist
                total_duration = 0
                for i, scene in enumerate(result["scenes"]):
                    scene.setdefault("scene_number", i + 1)
                    scene.setdefault("duration_seconds", max(2, duration // len(result["scenes"])))
                    scene.setdefault("objective", "")
                    scene.setdefault("transition", "")
                    scene.setdefault("scene_type", "main_content")
                    total_duration += scene["duration_seconds"]

                # Normalize scene durations to match requested total (±10s tolerance)
                if total_duration > 0 and abs(total_duration - duration) > 10:
                    scale = duration / total_duration
                    for scene in result["scenes"]:
                        scene["duration_seconds"] = max(2, round(scene["duration_seconds"] * scale))

                # Normalize top-level metadata fields
                result.setdefault("title", topic)
                result.setdefault("summary", "")
                result.setdefault("storytelling_style", "")
                result.setdefault("estimated_duration_seconds", duration)

                print(
                    f"  [OK] Script generated via {model_name} ({key_label}, {len(result['scenes'])} scenes)",
                    file=sys.stderr,
                )
                return result

            except concurrent.futures.TimeoutError:
                last_error = TimeoutError(f"{model_name} timed out after {API_TIMEOUT}s")
                print(
                    f"  [WARN] {model_name} ({key_label}) timed out after {API_TIMEOUT}s. "
                    "Trying next model...",
                    file=sys.stderr,
                )
                continue  # try next model

            except Exception as e:
                err_str = str(e)
                last_error = e

                # Check for quota-exhausted (429) error
                is_quota_error = (
                    "429" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                    or "quota" in err_str.lower()
                )
                is_model_not_found = (
                    "404" in err_str
                    or "NOT_FOUND" in err_str
                    or "not found" in err_str.lower()
                )

                if is_quota_error:
                    print(
                        f"  [WARN] {model_name} ({key_label}) quota exceeded. "
                        "Trying next available model/key...",
                        file=sys.stderr,
                    )
                    continue  # try next model
                elif is_model_not_found:
                    print(
                        f"  [WARN] {model_name} ({key_label}) is unavailable. "
                        "Trying next model...",
                        file=sys.stderr,
                    )
                    continue  # try next model
                else:
                    print(
                        f"  [WARN] {model_name} ({key_label}) error: {err_str[:100]}. "
                        "Trying next model...",
                        file=sys.stderr,
                    )
                    continue  # try next model instead of crashing

        # All models for this key exhausted — try next key
        if key_index < len(api_keys) - 1:
            print(
                f"  [WARN] All models exhausted for {key_label}. Switching to next API key...",
                file=sys.stderr,
            )

    # All keys and models exhausted
    raise RuntimeError(
        f"All Gemini API keys and models hit quota limits. "
        f"Please wait a few minutes and try again, or add a paid API key. "
        f"Last error: {last_error}"
    )


def _generate_mock(topic: str, tone: str, duration: int) -> dict:
    """
    Return a mock script with proper YouTube structure (fallback).
    """
    scene_count = get_scene_count(duration)
    per_scene = max(2, round(duration / scene_count))
    topic_keyword = topic.lower().replace(" ", " ")

    def _format_queries(queries: list[str]) -> list[str]:
        return [q.format(topic_keyword=topic_keyword) for q in queries]

    scenes = []

    # Scene 1: Hook
    hook = MOCK_TEMPLATES["hook"].copy()
    scenes.append({
        "scene_number": 1,
        "scene_type": "hook",
        "narration": hook["narration"].format(topic=topic),
        "visual_prompt": hook["visual_prompt"].format(topic_keyword=topic_keyword),
        "visual_queries": _format_queries(hook.get("visual_queries", [])),
        "duration_seconds": min(per_scene, 8),
    })

    # Scene 2: Introduction
    intro = MOCK_TEMPLATES["introduction"].copy()
    scenes.append({
        "scene_number": 2,
        "scene_type": "introduction",
        "narration": intro["narration"].format(topic=topic),
        "visual_prompt": intro["visual_prompt"].format(topic_keyword=topic_keyword),
        "visual_queries": _format_queries(intro.get("visual_queries", [])),
        "duration_seconds": per_scene,
    })

    # Scenes 3 to N-2: Main Content
    main_templates = MOCK_TEMPLATES["main_content"]
    main_count = scene_count - 4  # Subtract hook, intro, conclusion, CTA
    if main_count < 1:
        main_count = 1

    for i in range(main_count):
        template = main_templates[i % len(main_templates)]
        cycle = i // len(main_templates)
        visual = template["visual_prompt"].format(topic_keyword=topic_keyword)
        if cycle > 0:
            visual = f"{visual} (perspective {cycle + 1})"

        scenes.append({
            "scene_number": i + 3,
            "scene_type": "main_content",
            "narration": template["narration"].format(topic=topic),
            "visual_prompt": visual,
            "visual_queries": _format_queries(template.get("visual_queries", [])),
            "duration_seconds": per_scene,
        })

    # Conclusion
    conclusion = MOCK_TEMPLATES["conclusion"].copy()
    scenes.append({
        "scene_number": scene_count - 1,
        "scene_type": "conclusion",
        "narration": conclusion["narration"].format(topic=topic),
        "visual_prompt": conclusion["visual_prompt"].format(topic_keyword=topic_keyword),
        "visual_queries": _format_queries(conclusion.get("visual_queries", [])),
        "duration_seconds": per_scene,
    })

    # Call-to-Action
    cta = MOCK_TEMPLATES["cta"].copy()
    scenes.append({
        "scene_number": scene_count,
        "scene_type": "cta",
        "narration": cta["narration"].format(topic=topic),
        "visual_prompt": cta["visual_prompt"].format(topic_keyword=topic_keyword),
        "visual_queries": _format_queries(cta.get("visual_queries", [])),
        "duration_seconds": min(per_scene, 6),
    })

    title = f"{topic} -- Everything You Need to Know"
    return {"title": title, "scenes": scenes}



def generate_script(
    topic: str,
    tone: str = "educational",
    duration: int = 60,
    language: str = "english",
) -> dict:
    """
    Generate a dynamic video script for the given topic using AI.

    The model autonomously selects the best storytelling structure,
    scene count, and narrative flow based on the topic and duration.
    No fixed template is applied — every script is unique.

    Args:
        topic:    The video topic (e.g., "The Fall of the Roman Empire").
        tone:     Tone of the script (educational, entertaining, motivational).
        duration: Target video duration in seconds.
        language: Language for narration ("english", "hindi", "gujarati").

    Returns:
        A dict with keys:
          - title (str):               Video title
          - summary (str):             One-sentence value proposition
          - storytelling_style (str):  Narrative structure chosen by the AI
          - estimated_duration_seconds (int): Target duration
          - topic (str):               Original topic
          - tone (str):                Tone used
          - duration (int):            Target duration
          - language (str):            Language used
          - scenes (list[dict]):       List of scene dicts, each containing:
              - scene_number, narration, visual_prompt, objective,
                transition, duration_seconds, scene_type
          - source (str):              "gemini" or "mock"
    """
    import sys
    try:
        result = _generate_with_gemini(topic, tone, duration, language=language)
        source = "gemini"
        print(f"  [OK] Script generated using Gemini API ({len(result['scenes'])} scenes, lang={language})", file=sys.stderr)
    except Exception as e:
        print(f"  [WARN] Gemini API call failed, using mock script: {e}", file=sys.stderr)
        result = _generate_mock(topic, tone, duration)
        source = "mock"

    # Attach metadata
    result["topic"] = topic
    result["tone"] = tone
    result["duration"] = duration
    result["language"] = language
    result["source"] = source

    return result


# ---------------------------------------------------------------------------
# CLI entry point -- allows calling from n8n via:
#   python -m scripts.script_generator --topic "How AI Works" --tone educational
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a video script")
    parser.add_argument("--topic", type=str, required=True, help="Video topic")
    parser.add_argument(
        "--tone",
        type=str,
        default="educational",
        choices=["educational", "entertaining", "motivational"],
        help="Script tone",
    )
    parser.add_argument(
        "--duration", type=int, default=60, help="Target duration in seconds"
    )
    args = parser.parse_args()

    script = generate_script(args.topic, args.tone, args.duration)
    print(json.dumps(script, indent=2, ensure_ascii=False))
