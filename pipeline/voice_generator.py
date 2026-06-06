"""
ShortForge AI — Voice Generator v2 (Edge-TTS)
================================================
Generates natural Hindi/English voices using Microsoft Edge TTS (FREE).
Supports male/female voices per niche, with word-level timing.
"""

import asyncio
import edge_tts
from pathlib import Path

from config import (
    VOICE_RATE_HINDI, VOICE_RATE_ENGLISH,
    VOICE_VOLUME, TEMP_DIR, NICHES, VOICE_PROFILES
)


def _get_voice_id(language: str, niche: str = "") -> str:
    """Get the appropriate voice ID based on language and niche preference."""
    # Check niche-specific voice preference
    niche_voice_pref = NICHES.get(niche, {}).get("voice", "female")

    if language in ("hindi", "hinglish"):
        if niche_voice_pref == "male":
            return VOICE_ID_HINDI_MALE
        return VOICE_ID_HINDI_FEMALE
    else:
        if niche_voice_pref == "male":
            return VOICE_ID_ENGLISH_MALE
        return VOICE_ID_ENGLISH_FEMALE


def _get_voice_rate(language: str) -> str:
    """Get speech rate based on language."""
    if language in ("hindi", "hinglish"):
        return VOICE_RATE_HINDI
    return VOICE_RATE_ENGLISH


async def _generate_voice_async(
    text: str,
    output_path: str,
    voice_id: str,
    rate: str,
    volume: str,
    pitch: str,
) -> tuple[float, list[dict]]:
    """
    Generate voice audio file and extract word timings.
    Returns (duration_seconds, word_timings).
    """
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice_id,
        rate=rate,
        volume=volume,
        pitch=pitch,
    )

    # Collect word timings from SSML events
    word_timings = []

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_timings.append({
                    "text": chunk["text"],
                    "offset": chunk["offset"] / 10_000_000,  # Convert to seconds
                    "duration": chunk["duration"] / 10_000_000,
                })

    # Calculate total duration from file
    duration = 0.0
    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", output_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
    except Exception:
        # Estimate from word timings
        if word_timings:
            last = word_timings[-1]
            duration = last["offset"] + last["duration"] + 0.5
        else:
            # Rough estimate: ~3 words per second for Hindi
            word_count = len(text.split())
            duration = max(5.0, word_count / 2.5)

    return duration, word_timings


def generate_all_voices(
    scenes: list[dict],
    job_id: str,
    language: str = "hindi",
    niche: str = "",
    voice_profile: str = "female",
) -> list[dict]:
    """Generate voice audio for all scenes."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Get voice ID and pitch from config
    profile = VOICE_PROFILES.get(language, VOICE_PROFILES["hindi"]).get(voice_profile, VOICE_PROFILES["hindi"]["female"])
    voice_id = profile["voice_id"]
    pitch = profile["pitch"]
    
    rate = _get_voice_rate(language)

    print(f"\n🗣️  Generating voices for {len(scenes)} scenes...")
    print(f"   Voice: {voice_id} | Pitch: {pitch} | Rate: {rate}")

    async def _gen_all():
        for i, scene in enumerate(scenes):
            text = scene.get("text", "")
            if not text:
                continue

            output_path = str(TEMP_DIR / f"{job_id}_voice_{i:03d}.mp3")

            print(f"   🗣️  Scene {i + 1}: Generating voice...")
            preview = text[:50] + "..." if len(text) > 50 else text
            print(f"         \"{preview}\"")

            try:
                duration, word_timings = await _generate_voice_async(
                    text=text,
                    output_path=output_path,
                    voice_id=voice_id,
                    rate=rate,
                    volume=VOICE_VOLUME,
                    pitch=pitch,
                )

                scene["audio_path"] = output_path
                scene["duration"] = duration
                scene["word_timings"] = word_timings
                print(f"         Duration: {duration:.1f}s | Words: {len(word_timings)}")

            except Exception as e:
                print(f"         ❌ Voice error: {e}")
                scene["audio_path"] = None
                scene["duration"] = 5.0
                scene["word_timings"] = []

    # Run async voice generation
    asyncio.run(_gen_all())

    total_duration = sum(s.get("duration", 0) for s in scenes)
    print(f"   ✅ All voices generated! Total duration: {total_duration:.1f}s")

    return scenes


if __name__ == "__main__":
    # Quick test
    test_scenes = [
        {"text": "Kya aapko pata hai ki Bhagwan Krishna ne Govardhan Parvat ko apni ek ungli par utha liya tha?"},
    ]
    result = generate_all_voices(test_scenes, "test", "hindi", "radha_krishna")
    print(f"Duration: {result[0].get('duration', 0):.1f}s")
