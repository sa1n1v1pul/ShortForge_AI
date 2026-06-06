"""
ShortForge AI — Video Assembler (FFmpeg)
==========================================
Combines images, audio, and captions into final 9:16 vertical videos.
Features: Ken Burns effect, smooth transitions, background music.
"""

import os
import subprocess
import time
from pathlib import Path

from config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    TEMP_DIR, OUTPUT_DIR, BG_MUSIC_VOLUME,
    MUSIC_DIR, FONTS_DIR,
)


def _find_ffmpeg() -> str:
    """Find FFmpeg executable — check PATH first, then common locations."""
    # Check PATH
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return "ffmpeg"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Check common Windows locations
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\ffmpeg.exe",
        r"D:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Tools\ffmpeg\bin\ffmpeg.exe",
    ]
    for p in common_paths:
        if Path(p).exists():
            return p

    # Check if there's one in our project
    local = Path(__file__).parent.parent / "ffmpeg" / "bin" / "ffmpeg.exe"
    if local.exists():
        return str(local)

    return "ffmpeg"  # Hope it's in PATH


def _get_bg_music() -> str | None:
    """Get a background music file if available."""
    if not MUSIC_DIR.exists():
        return None
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    if music_files:
        return str(music_files[0])
    return None


def _get_font_path() -> str | None:
    """Get the caption font file path."""
    if not FONTS_DIR.exists():
        return None
    font_files = list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.otf"))
    if font_files:
        return str(font_files[0])
    return None


def _combine_video_audio(
    video_path: str,
    audio_path: str,
    duration: float,
    scene_index: int,
    job_id: str,
    ffmpeg: str = "ffmpeg",
) -> str | None:
    """
    Combine a Veo-animated video clip with narration audio.
    Loops/trims the video to match audio duration.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(TEMP_DIR / f"{job_id}_scene_clip_{scene_index:03d}.mp4")

    cmd = [
        ffmpeg, "-y",
        "-stream_loop", "-1",  # Loop video if shorter than audio
        "-i", video_path,
        "-i", audio_path,
        "-filter_complex",
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={VIDEO_FPS}[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if Path(output_path).exists():
            return output_path
        else:
            return None
    except Exception:
        return None


def create_scene_video(
    image_path: str,
    audio_path: str,
    duration: float,
    scene_index: int,
    job_id: str,
    ffmpeg: str = "ffmpeg",
) -> str | None:
    """
    Create a video segment for a single scene.
    - Image with Ken Burns (slow zoom) effect
    - Audio narration overlaid
    - Returns path to the scene video clip
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(TEMP_DIR / f"{job_id}_scene_clip_{scene_index:03d}.mp4")

    if not Path(image_path).exists():
        print(f"   ⚠️  Scene {scene_index + 1}: Image missing, creating color background")
        # Create a solid color background
        colors = ["0x1a1a2e", "0x16213e", "0x0f3460", "0x533483", "0x2c3333", "0x1b2430"]
        color = colors[scene_index % len(colors)]
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={duration:.2f}:r={VIDEO_FPS}",
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path
        ]
    else:
        # Ken Burns effect: slow zoom from 100% to 115% over duration
        # zoompan filter: zoom from 1.0 to 1.15, pan to keep centered
        total_frames = int(duration * VIDEO_FPS)
        zoom_speed = 0.15 / total_frames  # 15% zoom over duration

        cmd = [
            ffmpeg, "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-filter_complex",
            (
                f"[0:v]scale={VIDEO_WIDTH * 2}:{VIDEO_HEIGHT * 2},"
                f"zoompan=z='min(zoom+{zoom_speed:.6f},1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
            ),
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            output_path
        ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if Path(output_path).exists():
            return output_path
        else:
            print(f"   ❌ Scene {scene_index + 1} video creation failed")
            if result.stderr:
                # Print last 3 lines of error
                lines = result.stderr.strip().split("\n")
                for line in lines[-3:]:
                    print(f"      {line}")
            return None
    except subprocess.TimeoutExpired:
        print(f"   ❌ Scene {scene_index + 1} timed out")
        return None
    except FileNotFoundError:
        print(f"   ❌ FFmpeg not found! Please install FFmpeg.")
        return None


def concat_scenes(
    scene_clips: list[str],
    job_id: str,
    ffmpeg: str = "ffmpeg",
) -> str | None:
    """Concatenate all scene clips into one video."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(TEMP_DIR / f"{job_id}_concat.mp4")
    list_file = str(TEMP_DIR / f"{job_id}_concat_list.txt")

    # Create concat list file
    with open(list_file, "w") as f:
        for clip in scene_clips:
            # Escape backslashes for FFmpeg
            escaped = clip.replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    cmd = [
        ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if Path(output_path).exists():
            return output_path
        else:
            print(f"   ❌ Concat failed")
            if result.stderr:
                lines = result.stderr.strip().split("\n")
                for line in lines[-3:]:
                    print(f"      {line}")
            return None
    except Exception as e:
        print(f"   ❌ Concat error: {e}")
        return None


def burn_captions(
    video_path: str,
    captions_path: str,
    job_id: str,
    ffmpeg: str = "ffmpeg",
) -> str | None:
    """Burn ASS subtitles into the video."""
    output_path = str(TEMP_DIR / f"{job_id}_captioned.mp4")

    # Windows path escaping for FFmpeg filter:
    # 1. Use forward slashes
    # 2. Escape colons with \\:
    # 3. Use the subtitles filter (more compatible than ass filter)
    captions_escaped = captions_path.replace("\\", "/")
    # Escape the drive letter colon (e.g., D: -> D\\:)
    if len(captions_escaped) >= 2 and captions_escaped[1] == ":":
        captions_escaped = captions_escaped[0] + "\\:" + captions_escaped[2:]

    # Method 1: subtitles filter (most compatible)
    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-vf", f"subtitles='{captions_escaped}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
            return output_path
    except Exception:
        pass

    # Method 2: copy ASS to temp with simple name, use that
    try:
        import shutil
        simple_ass = str(TEMP_DIR / f"subs.ass")
        shutil.copy2(captions_path, simple_ass)
        simple_escaped = simple_ass.replace("\\", "/")
        if len(simple_escaped) >= 2 and simple_escaped[1] == ":":
            simple_escaped = simple_escaped[0] + "\\:" + simple_escaped[2:]

        cmd2 = [
            ffmpeg, "-y",
            "-i", video_path,
            "-vf", f"ass='{simple_escaped}'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "copy",
            "-pix_fmt", "yuv420p",
            output_path,
        ]
        result = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
        if Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
            return output_path
    except Exception:
        pass

    print(f"   ⚠️  Caption burn failed, using video without captions")
    if result and result.stderr:
        lines = result.stderr.strip().split("\n")
        for line in lines[-3:]:
            print(f"      {line}")
    return video_path


def add_background_music(
    video_path: str,
    job_id: str,
    ffmpeg: str = "ffmpeg",
) -> str | None:
    """Add background music at low volume."""
    music_path = _get_bg_music()
    if not music_path:
        return video_path  # No music available, return as-is

    output_path = str(TEMP_DIR / f"{job_id}_with_music.mp4")

    cmd = [
        ffmpeg, "-y",
        "-i", video_path,
        "-i", music_path,
        "-filter_complex",
        (
            f"[1:a]volume={BG_MUSIC_VOLUME}[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        ),
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if Path(output_path).exists():
            return output_path
        else:
            return video_path
    except Exception:
        return video_path


def assemble_final_video(
    scenes: list[dict],
    captions_path: str,
    job_id: str,
    title: str = "video",
    enable_music: bool = True,
    enable_captions: bool = True,
) -> str | None:
    """
    Main assembly function: combines all scenes into final video.

    Steps:
    1. Create individual scene clips (image + audio + Ken Burns)
    2. Concatenate all scenes
    3. Burn captions
    4. Add background music
    5. Export to output folder
    """
    ffmpeg = _find_ffmpeg()
    print(f"\n🎬 Assembling video...")
    print(f"   FFmpeg: {ffmpeg}")

    # Step 1: Create scene clips
    print(f"\n   📽️  Creating {len(scenes)} scene clips...")
    scene_clips = []
    animated_count = 0
    for i, scene in enumerate(scenes):
        audio_path = scene.get("audio_path")

        if not audio_path:
            print(f"   ⚠️  Scene {i + 1}: No audio, skipping")
            continue

        # Priority: Veo animated clip > enhanced image > raw image
        animated_path = scene.get("animated_path")
        image_path = scene.get("enhanced_path") or scene.get("media_path")

        if animated_path and Path(animated_path).exists():
            # Use Veo animated clip — just combine with audio
            clip_path = _combine_video_audio(
                video_path=animated_path,
                audio_path=audio_path,
                duration=scene.get("duration", 5.0),
                scene_index=i,
                job_id=job_id,
                ffmpeg=ffmpeg,
            )
            animated_count += 1
        else:
            # Fallback: static image + Ken Burns effect
            clip_path = create_scene_video(
                image_path=image_path or "",
                audio_path=audio_path,
                duration=scene.get("duration", 5.0),
                scene_index=i,
                job_id=job_id,
                ffmpeg=ffmpeg,
            )

        if clip_path:
            scene_clips.append(clip_path)
            tag = "🎥" if animated_path and Path(animated_path).exists() else "✅"
            print(f"   {tag} Scene {i + 1} clip ready")
        else:
            print(f"   ❌ Scene {i + 1} clip failed")

    if not scene_clips:
        print("   ❌ No scene clips created! Cannot assemble video.")
        return None

    # Step 2: Concatenate
    print(f"\n   🔗 Concatenating {len(scene_clips)} clips...")
    concat_path = concat_scenes(scene_clips, job_id, ffmpeg)
    if not concat_path:
        print("   ❌ Concatenation failed!")
        return None
    print(f"   ✅ Concatenated")

    # Step 3: Burn captions
    final_path = concat_path
    if enable_captions and captions_path and Path(captions_path).exists():
        print(f"\n   📝 Burning captions...")
        captioned = burn_captions(concat_path, captions_path, job_id, ffmpeg)
        if captioned:
            final_path = captioned
            print(f"   ✅ Captions burned")

    # Step 4: Background music
    if enable_music:
        print(f"\n   🎵 Adding background music...")
        with_music = add_background_music(final_path, job_id, ffmpeg)
        if with_music:
            final_path = with_music

    # Step 5: Copy to output folder
    from datetime import date
    today_dir = OUTPUT_DIR / date.today().isoformat()
    today_dir.mkdir(parents=True, exist_ok=True)

    # Clean title for filename
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    safe_title = safe_title.strip().replace(" ", "_")[:50] or "video"

    # Find next available number
    existing = list(today_dir.glob(f"{safe_title}*.mp4"))
    num = len(existing) + 1
    output_name = f"{safe_title}_{num:03d}.mp4"
    final_output = str(today_dir / output_name)

    # Copy (or move) final video to output
    import shutil
    shutil.copy2(final_path, final_output)

    # Get file size
    size_mb = Path(final_output).stat().st_size / (1024 * 1024)

    print(f"\n   {'='*50}")
    print(f"   ✅ VIDEO READY!")
    print(f"   📁 {final_output}")
    print(f"   📏 {size_mb:.1f} MB")
    print(f"   {'='*50}")

    return final_output


if __name__ == "__main__":
    ffmpeg = _find_ffmpeg()
    try:
        result = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, timeout=5)
        print(f"FFmpeg found: {ffmpeg}")
        print(result.stdout.split("\n")[0])
    except FileNotFoundError:
        print("FFmpeg NOT found! Please install it.")
