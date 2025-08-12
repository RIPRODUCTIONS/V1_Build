from __future__ import annotations

from typing import Any

from app.automation.registry import skill


@skill('relationship.generate_openers')
async def generate_openers(context: dict[str, Any]) -> dict[str, Any]:
    interests = context.get('interests') or []
    bio = (context.get('profile_bio') or '').strip()
    tone = (context.get('tone') or 'friendly').lower()
    count = int(context.get('count') or 5)

    base = [
        "What's a small thing that made your day better recently?",
        'If we planned a low-key weekend, what would we do?',
        "What's something you're learning or curious about right now?",
        'Best spot in town for a cozy coffee or tea?',
        'What kind of conversation do you enjoy most on first chats?',
    ]

    tailored: list[str] = []
    if interests and isinstance(interests, list):
        for interest in interests[:3]:
            i = str(interest).strip()
            if not i:
                continue
            tailored.append(f"I noticed you're into {i}. What's your favorite thing about it?")
    if bio:
        tailored.append(f"Your bio mentioned '{bio[:40]}...'. What's the story behind that?")

    openers = (tailored + base)[: max(1, min(count, 10))]
    if tone in {'playful', 'fun'}:
        openers = [o + ' 😄' for o in openers]
    elif tone in {'romantic'}:
        openers = [o + ' ✨' for o in openers]

    return {**context, 'openers': openers}
