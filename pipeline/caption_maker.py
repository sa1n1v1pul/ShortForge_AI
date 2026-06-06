"""
ShortForge AI — Caption Maker
================================
Generates ASS (Advanced SubStation Alpha) subtitle files with
animated word-by-word highlighting for viral-style captions.
"""

from pathlib import Path
from templates.styles import STYLES, DEFAULT_STYLE
from config import TEMP_DIR, VIDEO_WIDTH, VIDEO_HEIGHT


def _format_ass_time(seconds: float) -> str:
    """Convert seconds to ASS time format: H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _build_ass_header(style_name: str = DEFAULT_STYLE) -> str:
    """Build the ASS file header with style definitions."""
    style = STYLES.get(style_name, STYLES[DEFAULT_STYLE])

    font_name = style["font_name"]
    font_size = style["font_size"]
    primary = style["primary_color"]
    secondary = style["secondary_color"]
    outline_color = style["outline_color"]
    back_color = style["back_color"]
    bold = -1 if style["bold"] else 0
    outline = style["outline"]
    shadow = style["shadow"]
    alignment = style["alignment"]
    margin_v = style["margin_v"]

    return f"""[Script Info]
Title: ReelsForge Subtitles
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary},{secondary},{outline_color},{back_color},{bold},0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},40,40,{margin_v},1
Style: Highlight,{font_name},{font_size},{secondary},{primary},{outline_color},{back_color},{bold},0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def generate_sentence_captions(
    scenes: list[dict],
    job_id: str,
    style_name: str = DEFAULT_STYLE,
) -> str:
    """
    Generate ASS subtitles with sentence-level timing.
    Each scene's text appears while the voice is speaking.

    Returns path to the generated .ass file.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(TEMP_DIR / f"{job_id}_captions.ass")

    print(f"\n📝 Generating captions...")

    ass_content = _build_ass_header(style_name)

    current_time = 0.0
    for scene in scenes:
        text = scene.get("text", "")
        duration = scene.get("duration", 5.0)

        start = _format_ass_time(current_time)
        end = _format_ass_time(current_time + duration)

        # Clean text for ASS format (replace newlines, escape braces)
        clean_text = text.replace("\n", "\\N").replace("{", "\\{").replace("}", "\\}")

        # Split into lines of max ~6 words for readability
        words = clean_text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(current_line) >= 5:
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))

        display_text = "\\N".join(lines)

        ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{display_text}\n"

        current_time += duration

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    print(f"   ✅ Captions saved: {output_path}")

    return output_path


def generate_word_captions(
    scenes: list[dict],
    job_id: str,
    style_name: str = DEFAULT_STYLE,
    words_per_group: int = 3,
) -> str:
    """
    Generate ASS subtitles with word-level timing (karaoke style).
    Words appear in groups for readability.

    This creates the viral "word pop" effect seen in top shorts.

    Returns path to the generated .ass file.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(TEMP_DIR / f"{job_id}_captions.ass")

    print(f"\n📝 Generating word-by-word captions...")

    ass_content = _build_ass_header(style_name)

    current_time = 0.0
    for scene in scenes:
        word_timings = scene.get("word_timings", [])
        duration = scene.get("duration", 5.0)

        if not word_timings:
            # Fallback: estimate word timings
            words = scene.get("text", "").split()
            if words:
                time_per_word = duration / len(words)
                word_timings = [
                    {"word": w, "start": i * time_per_word, "end": (i + 1) * time_per_word}
                    for i, w in enumerate(words)
                ]

        # Group words (3-4 words at a time)
        groups = []
        for i in range(0, len(word_timings), words_per_group):
            group = word_timings[i:i + words_per_group]
            if group:
                groups.append(group)

        for group in groups:
            group_text = " ".join(w["word"] for w in group)
            group_start = current_time + group[0]["start"]
            group_end = current_time + group[-1]["end"]

            # Ensure minimum display time of 0.3s
            if group_end - group_start < 0.3:
                group_end = group_start + 0.5

            start_str = _format_ass_time(group_start)
            end_str = _format_ass_time(group_end)

            # Clean text
            clean_text = group_text.replace("{", "\\{").replace("}", "\\}")

            # Add with a scale-in animation effect
            animated_text = (
                f"{{\\fad(100,100)\\an5}}"
                f"{clean_text}"
            )

            ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{animated_text}\n"

        current_time += duration

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    print(f"   ✅ Word captions saved: {output_path}")

    return output_path


if __name__ == "__main__":
    # Quick test
    test_scenes = [
        {
            "text": "Did you know honey never spoils?",
            "duration": 4.0,
            "word_timings": [
                {"word": "Did", "start": 0.0, "end": 0.3},
                {"word": "you", "start": 0.3, "end": 0.5},
                {"word": "know", "start": 0.5, "end": 0.8},
                {"word": "honey", "start": 0.9, "end": 1.2},
                {"word": "never", "start": 1.3, "end": 1.6},
                {"word": "spoils?", "start": 1.7, "end": 2.1},
            ],
        },
    ]
    path = generate_word_captions(test_scenes, "test001")
    print(f"Output: {path}")
