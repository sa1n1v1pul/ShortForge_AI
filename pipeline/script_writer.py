"""
ShortForge AI — Script Writer v3 (Gemini API)
================================================
Generates viral video scripts with Devanagari Hindi support.
Dynamic scene count based on target duration.
"""

import json
import re
import time
from google import genai

from config import GEMINI_API_KEY, GEMINI_API_KEY_FREE, get_scene_count, DEFAULT_DURATION
from templates.prompts import get_script_prompt


def _call_gemini(prompt: str, api_key: str) -> str:
    """Call Gemini API with given key and return response text."""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


def generate_script(
    niche: str = "radha_krishna",
    language: str = "hindi",
    topic: str | None = None,
    target_duration: int = DEFAULT_DURATION,
    manual_prompt: str | None = None,
) -> dict:
    """
    Generate a video script using Gemini API.
    
    Args:
        niche: Content niche (radha_krishna, shiv_parvati, etc.)
        language: Language (hindi, english)
        topic: Optional specific topic
        target_duration: Target video duration in seconds (15-90)
        manual_prompt: If provided, use this as the full script prompt (manual mode)
    """
    # Calculate scene count from duration
    num_scenes = get_scene_count(target_duration)

    print(f"\n🤖 Generating script...")
    print(f"   Niche: {niche} | Language: {language} | Duration: {target_duration}s | Scenes: {num_scenes}")
    if topic:
        print(f"   Topic: {topic}")

    # Build prompt
    if manual_prompt:
        # Manual mode: user provided their own prompt/script
        prompt = f"""You are a video script generator. The user has provided their own story/prompt.
Convert it into exactly {num_scenes} scenes for a {target_duration}-second video.

USER'S PROMPT:
{manual_prompt}

RULES:
- Create EXACTLY {num_scenes} scenes
- Each scene text in देवनागरी हिंदी (Devanagari script) if the prompt is in Hindi
- Each image_prompt in English for AI image generation
- Make the story flow naturally across scenes

Return ONLY valid JSON:
{{
    "title": "Catchy title with emoji",
    "filename": "short_descriptive_name_in_hinglish",
    "description": "2-3 line description",
    "hashtags": "relevant hashtags",
    "scenes": [
        {{
            "text": "Scene narration text",
            "image_prompt": "Detailed visual description in English for 3D cartoon image"
        }}
    ]
}}"""
    else:
        prompt = get_script_prompt(niche, language, num_scenes, topic, target_duration)

    # Try paid key first, fallback to free key (with retry for 503)
    raw_text = None
    for key_name, key_value in [("paid", GEMINI_API_KEY), ("free", GEMINI_API_KEY_FREE)]:
        for attempt in range(3):
            try:
                if attempt > 0:
                    print(f"   Retry {attempt}/2 for {key_name} key (waiting 30s)...")
                    time.sleep(30)
                else:
                    print(f"   Trying {key_name} key...")
                raw_text = _call_gemini(prompt, key_value)
                print(f"   ✅ {key_name} key worked!")
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "exhausted" in err_str.lower():
                    print(f"   ⚠️  {key_name} key credits exhausted, trying next...")
                    break
                elif "503" in err_str or "UNAVAILABLE" in err_str:
                    print(f"   ⚠️  Server busy (503), will retry...")
                    continue
                elif "400" in err_str and "API_KEY_INVALID" in err_str:
                    print(f"   ⚠️  {key_name} key invalid, trying next...")
                    break
                else:
                    raise
        if raw_text:
            break

    if raw_text is None:
        raise ValueError("Both Gemini API keys failed! Please check your keys or add credits.")

    # Parse JSON from response
    json_text = raw_text
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', raw_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1).strip()

    try:
        script = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON parse error, attempting repair...")
        brace_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if brace_match:
            try:
                script = json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                raise ValueError(f"Could not parse Gemini response as JSON: {e}\nRaw: {raw_text[:500]}")
        else:
            raise ValueError(f"No JSON found in Gemini response: {raw_text[:500]}")

    # Validate
    if "scenes" not in script:
        raise ValueError(f"Script missing 'scenes' key. Got: {list(script.keys())}")
    if len(script["scenes"]) == 0:
        raise ValueError("Script has 0 scenes!")

    # Ensure all scenes have required fields
    for i, scene in enumerate(script["scenes"]):
        if "text" not in scene:
            raise ValueError(f"Scene {i} missing 'text'")
        if "image_prompt" not in scene:
            scene["image_prompt"] = scene.get("image_query", "beautiful divine background, golden light")
        if "image_query" not in scene:
            scene["image_query"] = scene["image_prompt"].split(",")[0][:50]

    script.setdefault("title", "Amazing Story")
    script.setdefault("description", "Watch till the end!")
    script.setdefault("hashtags", "#shorts #viral")

    print(f"   ✅ Script generated: \"{script['title']}\"")
    print(f"   📝 {len(script['scenes'])} scenes for {target_duration}s video")
    for i, s in enumerate(script["scenes"]):
        preview = s["text"][:50] + "..." if len(s["text"]) > 50 else s["text"]
        print(f"      Scene {i+1}: {preview}")

    return script
