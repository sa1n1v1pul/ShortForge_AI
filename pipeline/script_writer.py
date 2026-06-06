"""
ShortForge AI — Script Writer (Gemini API)
============================================
Generates viral short-form video scripts using Google Gemini.
"""

import json
import re
from google import genai

from config import GEMINI_API_KEY, GEMINI_API_KEY_FREE, SCENES_PER_VIDEO
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
    niche: str = "amazing_facts",
    language: str = "english",
    topic: str | None = None,
    num_scenes: int = SCENES_PER_VIDEO,
) -> dict:
    """
    Generate a video script using Gemini API.
    Tries paid key first, falls back to free key if credits exhausted.

    Returns dict with keys: title, scenes, description, hashtags
    Each scene has: text, image_query
    """
    print(f"\n🤖 Generating script...")
    print(f"   Niche: {niche} | Language: {language}")
    if topic:
        print(f"   Topic: {topic}")

    # Build prompt
    prompt = get_script_prompt(niche, language, num_scenes, topic)

    # Try paid key first, fallback to free key
    raw_text = None
    for key_name, key_value in [("paid", GEMINI_API_KEY), ("free", GEMINI_API_KEY_FREE)]:
        try:
            print(f"   Trying {key_name} key...")
            raw_text = _call_gemini(prompt, key_value)
            print(f"   ✅ {key_name} key worked!")
            break
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "exhausted" in err_str.lower():
                print(f"   ⚠️  {key_name} key credits exhausted, trying next...")
                continue
            elif "400" in err_str and "API_KEY_INVALID" in err_str:
                print(f"   ⚠️  {key_name} key invalid, trying next...")
                continue
            else:
                raise

    if raw_text is None:
        raise ValueError("Both Gemini API keys failed! Please check your keys or add credits.")


    # Parse JSON from response (handle markdown code blocks)
    json_text = raw_text
    # Remove ```json ... ``` wrapper if present
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', raw_text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1).strip()

    try:
        script = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"   ⚠️  JSON parse error, attempting repair...")
        # Try to find JSON object in the text
        brace_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if brace_match:
            try:
                script = json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                raise ValueError(f"Could not parse Gemini response as JSON: {e}\nRaw: {raw_text[:500]}")
        else:
            raise ValueError(f"No JSON found in Gemini response: {raw_text[:500]}")

    # Validate structure
    if "scenes" not in script:
        raise ValueError(f"Script missing 'scenes' key. Got: {list(script.keys())}")

    if len(script["scenes"]) == 0:
        raise ValueError("Script has 0 scenes!")

    # Ensure all scenes have required fields
    for i, scene in enumerate(script["scenes"]):
        if "text" not in scene:
            raise ValueError(f"Scene {i} missing 'text'")
        if "image_query" not in scene:
            scene["image_query"] = "abstract background"

    # Add defaults for missing top-level fields
    script.setdefault("title", "Amazing Facts You Need to Know")
    script.setdefault("description", "Watch till the end! 🤯")
    script.setdefault("hashtags", "#facts #shorts #viral")

    print(f"   ✅ Script generated: \"{script['title']}\"")
    print(f"   📝 {len(script['scenes'])} scenes")
    for i, s in enumerate(script["scenes"]):
        preview = s["text"][:60] + "..." if len(s["text"]) > 60 else s["text"]
        print(f"      Scene {i+1}: {preview}")

    return script


if __name__ == "__main__":
    # Quick test
    script = generate_script(niche="amazing_facts", language="english")
    print("\n" + json.dumps(script, indent=2, ensure_ascii=False))
