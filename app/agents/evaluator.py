import json
import os

from pydantic_ai import Agent

from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import ExtractionResult
from app.prompts.evaluator_prompt import PROMPT as EVALUATOR_PROMPT

# Ensure the OpenAI API key is available to the client even if not exported in the shell
if settings.OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

logger = get_logger(__name__)


class ConfidenceEvaluatorAgent:
    """LLM agent that re-scores extraction items for confidence."""

    def __init__(self):
        self.agent = Agent(
            settings.OPENAI_MODEL,
            output_type=ExtractionResult,
            system_prompt=EVALUATOR_PROMPT,
        )

    async def evaluate(self, document_text: str, extraction: ExtractionResult) -> ExtractionResult:
        # Provide the existing extraction as JSON to reduce hallucinations.
        extraction_json = json.dumps(extraction.model_dump(), ensure_ascii=True)
        try:
            run = await self.agent.run(
                (
                    "Document text:\n"
                    f"{document_text}\n\n"
                    "Existing extraction (JSON):\n"
                    f"{extraction_json}\n\n"
                    "Return the same structure with confidence values populated. "
                    "Do not invent new items or spaces."
                )
            )
            return run.output
        except Exception as exc:
            logger.exception("Confidence evaluation failed", extra={"error": str(exc)})
            raise
