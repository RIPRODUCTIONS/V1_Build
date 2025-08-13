from __future__ import annotations

from typing import Any, Dict


class VoiceInterface:
    async def setup_voice_commands(self) -> Dict[str, Any]:
        return {"status": "configured", "commands": ["check emails", "spending this month", "schedule posts"]}

    async def mobile_quick_actions(self) -> Dict[str, Any]:
        return {"quick_actions": ["Run Research", "Buy Credits", "View Receipts"]}


