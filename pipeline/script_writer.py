"""
ShortForge AI — Script Writer (Gemini API)
============================================
Generates viral short-form video scripts using Google Gemini.
"""

import json
import re
from google import genai

from config import GEMINI_API_KEY, SCENES_PER_VIDEO
from templates.prompts import get_script_prompt


def generate_script(
    niche: str = "amazing_facts",
    language: str = "english",
    topic: str | None = None,
    num_scenes: int = SCENES_PER_VIDEO,
) -> dict:
    """
    Generate a video script using Gemini API.

    Returns dict with keys: title, scenes, description, hashtags
    Each scene has: text, image_query
    """
    print(f"\n🤖 Generating script...")
    print(f"   Niche: {niche} | Language: {language}")
    if topic:
        print(f"   Topic: {topic}")

    # Build prompt
    prompt = get_script_prompt(niche, language, num_scenes, topic)

    # Call Gemini
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    raw_text = response.text.strip()

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
