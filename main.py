"""
╔═══════════════════════════════════════════════════════════════╗
║  🎬 ShortForge AI — Automated Faceless Shorts Generator v3   ║
║  ─────────────────────────────────────────────────────────────║
║  Usage:                                                       ║
║    python main.py                           (interactive)     ║
║    python main.py --topic "Krishna story" --duration 30       ║
║    python main.py --niche shiv_parvati --count 3              ║
║    python web/app.py                        (Web UI mode)     ║
╚═══════════════════════════════════════════════════════════════╝
"""

import argparse
import sys
import uuid
import time
import shutil
from pathlib import Path
from datetime import datetime

# Ensure we can import from project root
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    GEMINI_API_KEY, NICHES,
    DEFAULT_LANGUAGE, DEFAULT_NICHE, DEFAULT_DURATION,
    TEMP_DIR, OUTPUT_DIR, FONTS_DIR, MUSIC_DIR,
    ENABLE_VEO_ANIMATION, get_scene_count,
)
from pipeline.script_writer import generate_script
from pipeline.voice_generator import generate_all_voices
from pipeline.media_fetcher import fetch_all_media
from pipeline.video_animator import animate_all_scenes
from pipeline.image_enhancer import enhance_all_images
from pipeline.caption_maker import generate_word_captions, generate_sentence_captions
from pipeline.video_assembler import assemble_final_video
from pipeline.video2video import process_v2v_pipeline as create_v2v_video


def print_banner():
    print("""
===============================================================
  ShortForge AI - Automated Faceless Shorts Generator v3
  Gemini AI + Real-ESRGAN + Edge-TTS + FFmpeg
  One command -> Ready-to-upload content
===============================================================
""")


def check_prerequisites():
    """Verify required tools and files exist."""
    issues = []
    ok = True

    # FFmpeg
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        version = result.stdout.split("\n")[0][:60] if result.stdout else "unknown"
        print(f"  ✅ FFmpeg: {version}")
    else:
        issues.append("  ❌ FFmpeg not found! Install from https://ffmpeg.org")

    # Real-ESRGAN (optional)
    from config import ESRGAN_ENGINE
    if Path(ESRGAN_ENGINE).exists():
        print(f"  ✅ Real-ESRGAN engine ready")
    else:
        issues.append(f"  ⚠️  Real-ESRGAN not found at {ESRGAN_ENGINE} (enhancement disabled)")

    # Gemini API
    if not GEMINI_API_KEY or len(GEMINI_API_KEY) < 10:
        issues.append("  ❌ GEMINI_API_KEY not set!")

    # Fonts
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if issues:
        for issue in issues:
            print(f"  {issue}")
        print()

    # Only block on critical issues (Gemini key)
    critical = [i for i in issues if i.startswith("❌") and "GEMINI" in i]
    if critical:
        print("  🛑 Fix critical issues above before continuing!")
        return False

    return True


def create_single_video(
    niche: str = DEFAULT_NICHE,
    language: str = DEFAULT_LANGUAGE,
    topic: str | None = None,
    enhance_images: bool = True,
    caption_style: str = "sentence",
    target_duration: int = DEFAULT_DURATION,
    enable_animation: bool = False,
    manual_prompt: str | None = None,
    progress_callback=None,
    voice_profile: str = "female",
    api_key_mode: str = "1",
) -> str | None:
    """
    Generate a single video from scratch.
    This is the main pipeline orchestrator.
    
    Args:
        target_duration: Video duration in seconds (15, 30, 45, 60, 90)
        enable_animation: Enable Veo animation (expensive!)
        manual_prompt: User's own script text (manual mode)
        progress_callback: Function(step, message) for UI progress updates
        voice_profile: Voice identifier from config.VOICE_PROFILES
    """
    job_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    def _progress(step: str, msg: str):
        if progress_callback:
            progress_callback(step, msg)

    print(f"\n{'='*60}")
    print(f"  🎬 NEW VIDEO — Job: {job_id}")
    print(f"  Niche: {NICHES.get(niche, {}).get('name', niche)}")
    print(f"  Language: {language}")
    print(f"  Duration: {target_duration}s | Scenes: {get_scene_count(target_duration)}")
    print(f"  Animation: {'🎥 VEO (costly!)' if enable_animation else '🖼️ Ken Burns (free)'}")
    if topic:
        print(f"  Topic: {topic}")
    print(f"{'='*60}")

    try:
        # ── Step 1: Generate Script ──────────────────────────────
        _progress("script", "Generating script with AI...")
        script = generate_script(
            niche=niche,
            language=language,
            topic=topic,
            target_duration=target_duration,
            manual_prompt=manual_prompt,
            api_key_mode=api_key_mode,
        )
        scenes = script["scenes"]

        # ── Step 2: Generate Audio (Voices) ─────────────────────────
        _progress("voice", f"Generating voices ({len(scenes)} scenes)...")
        scenes = generate_all_voices(
            scenes=scenes,
            job_id=job_id,
            language=language,
            niche=niche,
            voice_profile=voice_profile,
        )

        # ── Step 3: Generate/Fetch Images ─────────────────────────
        _progress("images", f"Creating AI cartoon images for {len(scenes)} scenes...")
        scenes = fetch_all_media(
            scenes=scenes,
            job_id=job_id,
            niche=niche,
            media_type="image",
        )

        # ── Step 3.5: Animate Images with Veo (OPTIONAL) ─────────
        if enable_animation:
            _progress("animation", f"Animating {len(scenes)} scenes with Veo (this is costly!)...")
            scenes = animate_all_scenes(
                scenes=scenes,
                job_id=job_id,
                niche=niche,
            )
        else:
            print(f"\n🖼️  Animation: SKIPPED (Ken Burns effect will be used — FREE)")
            for s in scenes:
                s["animated_path"] = None

        # ── Step 4: Enhance Images (only for Pexels, AI images already HD) ──
        has_pexels_images = any(s.get("media_type") == "pexels" for s in scenes)
        scenes = enhance_all_images(
            scenes=scenes,
            job_id=job_id,
            enable_enhancement=enhance_images and has_pexels_images,
        )

        # ── Step 5: Generate Captions ────────────────────────────
        _progress("captions", "Creating Hindi captions...")
        if caption_style == "word":
            captions_path = generate_word_captions(scenes, job_id)
        else:
            captions_path = generate_sentence_captions(scenes, job_id)

        # ── Step 6: Assemble Final Video ─────────────────────────
        _progress("assembly", "Assembling final video...")
        final_path = assemble_final_video(
            scenes=scenes,
            captions_path=captions_path,
            job_id=job_id,
            title=script.get("filename") or script.get("title", "video"),
            enable_music=True,
            enable_captions=True,
        )

        elapsed = time.time() - start_time

        if final_path:
            _progress("complete", f"Video ready! {Path(final_path).name}")
            print(f"\n  🎉 VIDEO COMPLETE!")
            print(f"  ⏱️  Total time: {elapsed:.0f} seconds")
            print(f"  📁 Saved: {final_path}")
            print(f"  📝 Title: {script.get('title', 'N/A')}")
            print(f"  📋 Description: {script.get('description', 'N/A')}")
            print(f"  #️⃣  Hashtags: {script.get('hashtags', 'N/A')}")
            print(f"\n  📤 Ready to upload to YouTube / Instagram / Facebook!")
        else:
            _progress("error", "Video generation failed")
            print(f"\n  ❌ Video generation failed after {elapsed:.0f}s")

        return final_path

    except Exception as e:
        import traceback
        _progress("error", str(e))
        print(f"\n  ❌ Error: {e}")
        traceback.print_exc()
        return None

    finally:
        # Clean up temp files for this job
        _cleanup_temp(job_id)


def _cleanup_temp(job_id: str):
    """Remove temporary files for a specific job."""
    try:
        if TEMP_DIR.exists():
            for f in TEMP_DIR.glob(f"{job_id}_*"):
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="🎬 ShortForge AI — Automated Faceless Shorts Generator v3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --topic "Krishna ki Makhan Chori" --duration 30
  python main.py --niche shiv_parvati --duration 45
  python main.py --niche radha_krishna --count 3 --duration 30
  python main.py --niche hanuman --duration 15 --animate    (Veo ON, costly!)
  python web/app.py                                          (Web UI mode)
        """,
    )
    parser.add_argument("--topic", "-t", help="Specific topic for the video")
    parser.add_argument("--niche", "-n", default=DEFAULT_NICHE,
                        choices=list(NICHES.keys()),
                        help=f"Content niche (default: {DEFAULT_NICHE})")
    parser.add_argument("--lang", "-l", default=DEFAULT_LANGUAGE,
                        choices=["english", "hindi", "hinglish"],
                        help=f"Language (default: {DEFAULT_LANGUAGE})")
    parser.add_argument("--count", "-c", type=int, default=1,
                        help="Number of videos to generate (default: 1)")
    parser.add_argument("--duration", "-d", type=int, default=DEFAULT_DURATION,
                        choices=[15, 30, 45, 60, 90],
                        help=f"Target video duration in seconds (default: {DEFAULT_DURATION})")
    parser.add_argument("--no-enhance", action="store_true",
                        help="Skip Real-ESRGAN image enhancement")
    parser.add_argument("--captions", default="sentence",
                        choices=["word", "sentence"],
                        help="Caption style (default: sentence)")
    parser.add_argument("--animate", action="store_true",
                        help="Enable Veo animation (WARNING: ~₹50/scene!)")
    parser.add_argument("--manual-prompt", "-m", type=str, default=None,
                        help="Your own script/story text (manual mode)")

    args = parser.parse_args()

    print_banner()

    if not check_prerequisites():
        sys.exit(1)

    # Batch/direct mode
    print(f"\n🚀 Generating {args.count} video(s)...")

    results = []
    for i in range(args.count):
        if args.count > 1:
            print(f"\n{'━'*60}")
            print(f"  📹 Video {i + 1} of {args.count}")
            print(f"{'━'*60}")

        path = create_single_video(
            niche=args.niche,
            language=args.lang,
            topic=args.topic,
            enhance_images=not args.no_enhance,
            caption_style=args.captions,
            target_duration=args.duration,
            enable_animation=args.animate,
            manual_prompt=args.manual_prompt,
        )
        if path:
            results.append(path)

    # Summary
    print(f"\n\n{'═'*60}")
    print(f"  🎬 BATCH COMPLETE")
    print(f"{'═'*60}")
    print(f"  ✅ Generated: {len(results)}/{args.count} videos")
    for i, p in enumerate(results, 1):
        print(f"  {i}. {p}")
    print(f"{'═'*60}")


if __name__ == "__main__":
    main()
