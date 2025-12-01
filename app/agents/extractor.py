import os

from pydantic_ai import Agent

from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import ExtractionResult
from app.prompts.extractor_prompt import PROMPT as EXTRACTOR_PROMPT

# Ensure the OpenAI API key is available to the client even if not exported in the shell
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

logger = get_logger(__name__)


class RequirementsExtractorAgent:
    def __init__(self):
        self.agent = Agent(
            settings.OPENAI_MODEL,
            output_type=ExtractionResult,
            system_prompt=EXTRACTOR_PROMPT,
        )

    async def extract(self, text: str) -> ExtractionResult:
        try:
            run = await self.agent.run(f"Extract requirements from the following text:\n\n{text}")
            return run.output
        except Exception as exc:
            logger.exception("Extraction failed", extra={"error": str(exc)})
            raise
