from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.parser import DocumentParserAgent
from app.agents.extractor import RequirementsExtractorAgent
from app.agents.evaluator import ConfidenceEvaluatorAgent
from app.core.logging import get_logger
from app.entities.entities import Project, Space, Item

logger = get_logger(__name__)

class OrchestratorAgent:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.parser = DocumentParserAgent()
        self.extractor = RequirementsExtractorAgent()
        self.evaluator = ConfidenceEvaluatorAgent()

    async def create_or_update_project_from_document(self, document) -> int:
        """Analyze document, then create or update linked project with spaces/items."""
        from app.entities.entities import Project, Space, Item

        # 1) Parse document (async wrapper to avoid blocking)
        try:
            content = await self.parser.parse_file_async(document.file_path)
            logger.info(
                "Document parsed",
                extra={"document_id": getattr(document, "id", None)},
            )
        except Exception as exc:
            logger.exception(
                "Failed to parse document",
                extra={"document_id": getattr(document, "id", None), "error": str(exc)},
            )
            raise

        # 2) Extract structured requirements
        try:
            extraction_result = await self.extractor.extract(content.text)
            extraction_result = await self.evaluator.evaluate(content.text, extraction_result)
            logger.info(
                "Extraction and evaluation completed",
                extra={"document_id": getattr(document, "id", None)},
            )
        except Exception as exc:
            logger.exception(
                "Failed to extract or evaluate requirements",
                extra={"document_id": getattr(document, "id", None), "error": str(exc)},
            )
            raise

        # 3) Upsert project (reuse existing if document already linked)
        metadata = extraction_result.project_metadata
        project = None
        if document.project_id:
            project = await self.session.get(Project, document.project_id)
        if project is None:
            project = Project(
                name=metadata.name or document.filename,
                client_type=metadata.client_type,
                location=metadata.location,
                timeline=metadata.timeline,
                budget_range=metadata.budget_range,
            )
            self.session.add(project)
            await self.session.commit()
            await self.session.refresh(project)
        else:
            project.name = metadata.name or document.filename
            project.client_type = metadata.client_type
            project.location = metadata.location
            project.timeline = metadata.timeline
            project.budget_range = metadata.budget_range
            await self.session.commit()

        # 4) Replace spaces/items for this project
        existing_spaces = await self.session.execute(select(Space).where(Space.project_id == project.id))
        for space in existing_spaces.scalars().all():
            await self.session.delete(space)
        await self.session.commit()

        for space_data in extraction_result.spaces:
            space = Space(
                project_id=project.id,
                room_type=space_data.room_type,
                dimension=space_data.dimension,
                area=space_data.area,
            )
            self.session.add(space)
            await self.session.commit()
            await self.session.refresh(space)

            for item_data in space_data.items:
                confidence = self._clamp_confidence(item_data.confidence)
                item = Item(
                    space_id=space.id,
                    name=item_data.name or item_data.category.value,
                    category=item_data.category.value,
                    technical_specs=item_data.technical_specs,
                    material_preference=item_data.material_preference,
                    color_preference=item_data.color_preference,
                    brand_preference=item_data.brand_preference,
                    special_instruction=item_data.special_instruction,
                    quantity=item_data.quantity,
                    confidence=confidence,
                    is_accepted=None,
                )
                self.session.add(item)

        # 5) Link document to project
        document.project_id = project.id
        await self.session.commit()
        return project.id

    def _clamp_confidence(self, value):
        if value is None:
            return None
        try:
            return max(0.0, min(1.0, float(value)))
        except Exception:
            return None
