import json
import os
from typing import List
from pathlib import Path

from pydantic_ai import Agent

from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import SpaceRequirements
from app.prompts.prompt_add_agent import PROMPT as PROMPT_ADD_PROMPT

# Ensure the OpenAI API key is available to the client even if not exported in the shell
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

logger = get_logger(__name__)


class PromptAddAgent:

    def __init__(self):
        self.agent = Agent(
            settings.OPENAI_MODEL,
            output_type=List[SpaceRequirements],
            system_prompt=PROMPT_ADD_PROMPT,
        )

    async def generate_additions(self, context_summary: str, user_prompt: str) -> List[SpaceRequirements]:
        payload = {
            "current_spaces": context_summary,
            "user_prompt": user_prompt,
        }
        try:
            run = await self.agent.run(
                "Current project summary:\n"
                f"{context_summary}\n\n"
                "User prompt (additions only):\n"
                f"{user_prompt}\n\n"
                "Return ONLY the spaces/items to add as JSON.",
            )
            return run.output
        except Exception as exc:
            logger.exception("Prompt-based additions failed", extra={"error": str(exc), "payload": json.dumps(payload)})
            raise
