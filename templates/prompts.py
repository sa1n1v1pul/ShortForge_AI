"""
ShortForge AI — Gemini Prompt Templates v2
=============================================
Story-driven prompts for dharmic cartoon shorts + general niches.
"""


def get_script_prompt(niche: str, language: str, num_scenes: int, topic: str | None = None) -> str:
    """Build the Gemini prompt for generating a video script."""

    # Language instruction
    if language == "hindi":
        lang_instruction = """Language: Pure Hindi (Devanagari transliteration in Roman script).
Use simple, emotional Hindi that connects with Indian audience.
Example tone: "Kya aapko pata hai ki Bhagwan Krishna ne ye kyu kiya tha? Suniye ye adbhut katha..."
Do NOT use English words. Keep it desi and emotional."""
    elif language == "hinglish":
        lang_instruction = """Language: Hinglish (mix of Hindi and English in Roman script).
Example: "Guys, kya aapko pata hai ki Krishna ji ne ek baar aise kiya tha..."
Keep it casual and engaging."""
    else:
        lang_instruction = """Language: English. Keep it simple and engaging.
Use hooks like "Did you know..." or "Here's something incredible..."."""

    # Topic instruction
    topic_line = f'\nSPECIFIC TOPIC: "{topic}"\n' if topic else ""

    # Get niche-specific prompt
    niche_prompts = {
        "radha_krishna": _get_dharmic_prompt("radha_krishna", lang_instruction, topic_line, num_scenes),
        "shiv_parvati": _get_dharmic_prompt("shiv_parvati", lang_instruction, topic_line, num_scenes),
        "hanuman": _get_dharmic_prompt("hanuman", lang_instruction, topic_line, num_scenes),
        "mythology": _get_dharmic_prompt("mythology", lang_instruction, topic_line, num_scenes),
        "moral_stories": _get_dharmic_prompt("moral_stories", lang_instruction, topic_line, num_scenes),
    }

    if niche in niche_prompts:
        return niche_prompts[niche]
    else:
        return _get_general_prompt(niche, lang_instruction, topic_line, num_scenes)


def _get_dharmic_prompt(niche: str, lang_instruction: str, topic_line: str, num_scenes: int) -> str:
    """Generate prompt for dharmic/religious content."""

    niche_contexts = {
        "radha_krishna": """Niche: RADHA KRISHNA STORIES
You are a divine storyteller narrating beautiful leelas of Shri Krishna and Radha Rani.
Focus on: Krishna's childhood leelas (Makhan Chori, Kaliya Naag), Radha-Krishna divine love, 
Gopis ki kahaniyan, Krishna's wisdom from Bhagavad Gita, miraculous stories.
Tone: Devotional, magical, full of bhakti and wonder.""",

        "shiv_parvati": """Niche: SHIV PARVATI STORIES
You are narrating divine stories of Mahadev Shiva and Mata Parvati.
Focus on: Shiv-Parvati's divine love, Shiva's tandav, Ganesh ji birth, Kartikeya stories,
Shiva's wisdom, Samudra Manthan, Shiva saving the universe.
Tone: Powerful, devotional, awe-inspiring.""",

        "hanuman": """Niche: HANUMAN JI STORIES
You are narrating stories of the mighty Bajrangbali Hanuman ji.
Focus on: Hanuman's devotion to Lord Ram, Lanka Dahan, Sanjeevani Booti, 
Hanuman's childhood (eating the sun), Hanuman Chalisa stories.
Tone: Powerful, heroic, full of devotion and strength.""",

        "mythology": """Niche: SANATAN MYTHOLOGY
You are narrating epic stories from Indian mythology.
Focus on: Mahabharat episodes, Ramayan stories, Vishnu avatars, 
Devi Durga stories, lesser-known divine tales, cosmic battles.
Tone: Epic, grand, full of wisdom and divine power.""",

        "moral_stories": """Niche: DHARMIC MORAL STORIES
You are telling short moral stories inspired by Indian dharmic traditions.
Focus on: Panchatantra-style stories, stories with dharmic lessons,
tales of karma, dharma, truth, and devotion. 
Tone: Warm, wise, teaching values through engaging stories.""",
    }

    context = niche_contexts.get(niche, niche_contexts["mythology"])

    return f"""You are ShortForge AI — a viral short-form video script generator.

{context}
{topic_line}
{lang_instruction}

Generate a COMPLETE video script with EXACTLY {num_scenes} scenes for a 45-60 second vertical video (YouTube Shorts / Instagram Reels).

SCRIPT RULES:
1. Start with a POWERFUL HOOK in Scene 1 (question or shocking statement)
2. Tell a COMPLETE STORY with beginning, middle, and climax
3. End with a moral/wisdom or devotional call-to-action
4. Each scene should be 8-12 seconds of narration
5. Each scene MUST have a detailed image_prompt for AI cartoon image generation

IMAGE PROMPT RULES (VERY IMPORTANT):
- Each image_prompt must describe a specific cartoon scene
- Include character descriptions (what they look like, what they're wearing)
- Include setting/background details  
- Include mood/lighting (golden divine glow, mystical atmosphere, etc.)
- Style: "3D Indian cartoon animation style"
- Make each scene visually DIFFERENT from others

Return ONLY valid JSON (no markdown, no explanation):
{{
    "title": "Catchy title with emoji",
    "description": "2-3 line engaging description for YouTube/Instagram",
    "hashtags": "relevant hashtags space-separated",
    "scenes": [
        {{
            "text": "Narration text for this scene (8-12 seconds worth)",
            "image_prompt": "Detailed visual description for AI cartoon image generation: specific characters, poses, setting, colors, mood, 3D Indian cartoon animation style"
        }}
    ]
}}"""


def _get_general_prompt(niche: str, lang_instruction: str, topic_line: str, num_scenes: int) -> str:
    """Generate prompt for general content niches."""

    return f"""You are ShortForge AI — a viral short-form video script generator.

Niche: {niche.upper().replace('_', ' ')}
{topic_line}
{lang_instruction}

Generate a COMPLETE video script with EXACTLY {num_scenes} scenes for a 45-60 second vertical video (YouTube Shorts / Instagram Reels).

SCRIPT RULES:
1. Start with a POWERFUL HOOK (question or shocking fact)
2. Each scene reveals one mind-blowing point  
3. Build curiosity through all scenes
4. End with the most shocking revelation + call to action
5. Each scene = 8-12 seconds of narration

IMAGE PROMPT RULES:
- Each image_prompt must describe a specific illustration for that scene
- Include specific visual elements, colors, composition
- Style: "3D cartoon illustration, cinematic, vibrant colors"
- Make each scene visually DIFFERENT

Return ONLY valid JSON:
{{
    "title": "Catchy viral title with emoji",
    "description": "2-3 line description",
    "hashtags": "relevant hashtags",
    "scenes": [
        {{
            "text": "Narration for this scene",
            "image_prompt": "Detailed visual description for AI image: subject, setting, colors, mood, 3D cartoon style"
        }}
    ]
}}"""
