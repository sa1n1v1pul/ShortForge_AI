"""
ShortForge AI — Caption Styles
=================================
ASS subtitle styling presets for different visual styles.
"""

# Caption style presets
STYLES = {
    "bold_white": {
        "font_name": "Montserrat",
        "font_size": 22,
        "primary_color": "&H00FFFFFF",      # White
        "secondary_color": "&H0000FFFF",    # Yellow (for highlights)
        "outline_color": "&H00000000",      # Black outline
        "back_color": "&H80000000",         # Semi-transparent black shadow
        "bold": True,
        "outline": 3,
        "shadow": 2,
        "alignment": 2,                     # Bottom center
        "margin_v": 180,
    },
    "neon_yellow": {
        "font_name": "Montserrat",
        "font_size": 24,
        "primary_color": "&H0000FFFF",      # Yellow
        "secondary_color": "&H00FFFFFF",    # White
        "outline_color": "&H00000000",      # Black outline
        "back_color": "&H80000000",
        "bold": True,
        "outline": 4,
        "shadow": 3,
        "alignment": 2,
        "margin_v": 200,
    },
    "modern_gradient": {
        "font_name": "Montserrat",
        "font_size": 22,
        "primary_color": "&H00FFFFFF",      # White
        "secondary_color": "&H005EFFFB",    # Cyan
        "outline_color": "&H00200000",      # Dark blue outline
        "back_color": "&HA0000000",
        "bold": True,
        "outline": 3,
        "shadow": 2,
        "alignment": 2,
        "margin_v": 180,
    },
}

DEFAULT_STYLE = "bold_white"
