"""
ShortForge AI — Gemini Prompt Templates v3
=============================================
Story-driven prompts with Devanagari Hindi output for proper TTS pronunciation.
Dynamic scene count based on target video duration.
"""


def get_script_prompt(niche: str, language: str, num_scenes: int, topic: str | None = None, target_duration: int = 45) -> str:
    """Build the Gemini prompt for generating a video script."""

    seconds_per_scene = max(5, target_duration // num_scenes)

    # Language instruction
    if language == "hindi":
        lang_instruction = f"""भाषा: शुद्ध हिंदी (देवनागरी लिपि में)।
हर scene का text देवनागरी में लिखो: "कृष्ण ने बांसुरी बजाई", NOT "Krishna ne bansuri bajaai"।
सरल, भावनात्मक हिंदी जो भारतीय दर्शकों से जुड़े।
अंग्रेज़ी शब्दों का बिल्कुल इस्तेमाल मत करो — शुद्ध हिंदी लिखो।
image_prompt हमेशा English में लिखो (AI image generation के लिए)।
हर scene का narration {seconds_per_scene} सेकंड का हो।"""
    else:
        lang_instruction = f"""Language: English. Keep it simple and engaging.
Use hooks like "Did you know..." or "Here's something incredible..."
Each scene narration should be about {seconds_per_scene} seconds long."""

    topic_line = f'\nSPECIFIC TOPIC: "{topic}"\n' if topic else ""

    # Get niche-specific prompt
    niche_prompts = {
        "radha_krishna": _get_dharmic_prompt("radha_krishna", lang_instruction, topic_line, num_scenes, target_duration),
        "shiv_parvati": _get_dharmic_prompt("shiv_parvati", lang_instruction, topic_line, num_scenes, target_duration),
        "hanuman": _get_dharmic_prompt("hanuman", lang_instruction, topic_line, num_scenes, target_duration),
        "mythology": _get_dharmic_prompt("mythology", lang_instruction, topic_line, num_scenes, target_duration),
        "moral_stories": _get_dharmic_prompt("moral_stories", lang_instruction, topic_line, num_scenes, target_duration),
    }

    if niche in niche_prompts:
        return niche_prompts[niche]
    else:
        return _get_general_prompt(niche, lang_instruction, topic_line, num_scenes, target_duration)


def _get_dharmic_prompt(niche: str, lang_instruction: str, topic_line: str, num_scenes: int, target_duration: int) -> str:
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

Generate a COMPLETE video script with EXACTLY {num_scenes} scenes for a {target_duration}-second vertical video (YouTube Shorts / Instagram Reels).

CRITICAL RULES:
1. Start with a POWERFUL HOOK in Scene 1 (question or shocking statement)
2. Tell a COMPLETE STORY with beginning, middle, and climax
3. End with a moral/wisdom or devotional call-to-action
4. EXACTLY {num_scenes} scenes — no more, no less!
5. Each scene = {max(5, target_duration // num_scenes)} seconds of narration (2-3 sentences)
6. Total narration should be approximately {target_duration} seconds

TEXT RULES (VERY IMPORTANT):
- "text" field MUST be in देवनागरी हिंदी (Devanagari script)
- Example: "क्या आपको पता है कि भगवान कृष्ण ने..." NOT "Kya aapko pata hai..."
- No English words at all in "text" field

IMAGE PROMPT RULES:
- "image_prompt" MUST be in English (for AI image generation)
- Include character descriptions, setting, mood, lighting
- Style: "3D Indian cartoon animation style"
- Make each scene visually DIFFERENT from others

Return ONLY valid JSON (no markdown, no explanation):
{{
    "title": "Catchy title with emoji (in Devanagari Hindi)",
    "description": "2-3 line engaging description (in Devanagari Hindi)",
    "hashtags": "relevant hashtags space-separated",
    "scenes": [
        {{
            "text": "देवनागरी हिंदी में narration text",
            "image_prompt": "Detailed visual description in ENGLISH for AI cartoon image: specific characters, poses, setting, colors, mood, 3D Indian cartoon animation style"
        }}
    ]
}}"""


def _get_general_prompt(niche: str, lang_instruction: str, topic_line: str, num_scenes: int, target_duration: int) -> str:
    """Generate prompt for general content niches."""

    return f"""You are ShortForge AI — a viral short-form video script generator.

Niche: {niche.upper().replace('_', ' ')}
{topic_line}
{lang_instruction}

Generate a COMPLETE video script with EXACTLY {num_scenes} scenes for a {target_duration}-second vertical video (YouTube Shorts / Instagram Reels).

SCRIPT RULES:
1. Start with a POWERFUL HOOK (question or shocking fact)
2. Each scene reveals one mind-blowing point
3. Build curiosity through all scenes
4. End with the most shocking revelation + call to action
5. EXACTLY {num_scenes} scenes — no more, no less!
6. Each scene = {max(5, target_duration // num_scenes)} seconds of narration

IMAGE PROMPT RULES:
- Each "image_prompt" must be in English
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
            "image_prompt": "Detailed visual description in English for AI image: subject, setting, colors, mood, 3D cartoon style"
        }}
    ]
}}"""
