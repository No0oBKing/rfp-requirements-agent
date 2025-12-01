from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from typing import Optional, Dict, Any, List

from app.repositories.project_repository import (
    project_repository,
    space_repository,
    item_repository,
    document_repository
)
from app.agents.orchestrator import OrchestratorAgent
from app.agents.prompt_add import PromptAddAgent
from app.entities.entities import Project, Space, Item, Document
from app.core.logging import get_logger

logger = get_logger(__name__)

class ProjectService:
    """Stateless service for project operations"""
    
    def __init__(self):
        self.project_repository = project_repository
        self.space_repository = space_repository
        self.item_repository = item_repository
        self.document_repository = document_repository
        self.prompt_add_agent = PromptAddAgent()
    
    async def upload_document(self, session: AsyncSession, filename: str, file_path: str) -> int:
        """Upload document without creating project"""
        document = Document(
            filename=filename,
            file_path=file_path,
            project_id=None  # No project yet
        )
        document = await self.document_repository.create(session, document)
        logger.info("Document upload recorded", extra={"document_id": document.id, "filename": filename})
        return document.id

    async def add_space_with_items(self, session: AsyncSession, project_id: int, space_data: Dict[str, Any]) -> Optional[Space]:
        """Add a new space (optionally with items) to a project."""
        project = await self.project_repository.get_by_id(session, project_id)
        if not project:
            return None

        space = Space(
            project_id=project_id,
            room_type=space_data["room_type"],
            dimension=space_data.get("dimension"),
            area=space_data.get("area"),
        )
        space = await self.space_repository.create(session, space)

        items_data = space_data.get("items") or []
        created_items = []
        for item in items_data:
            new_item = Item(
                space_id=space.id,
                name=item.get("name") or item.get("category") or "Item",
                category=item.get("category") or "Others",
                technical_specs=item.get("technical_specs"),
                material_preference=item.get("material_preference"),
                color_preference=item.get("color_preference"),
                brand_preference=item.get("brand_preference"),
                special_instruction=item.get("special_instruction"),
                quantity=item.get("quantity"),
                confidence=item.get("confidence"),
            )
            created_items.append(await self.item_repository.create(session, new_item))

        logger.info(
            "Space added with items",
            extra={"project_id": project_id, "space_id": space.id, "item_count": len(created_items)},
        )
        return space

    async def add_item_to_space(self, session: AsyncSession, space_id: int, item_data: Dict[str, Any]) -> Optional[Item]:
        """Add a new item to an existing space."""
        space = await self.space_repository.get_by_id(session, space_id)
        if not space:
            return None

        item = Item(
            space_id=space_id,
            name=item_data.get("name") or item_data.get("category") or "Item",
            category=item_data.get("category") or "Others",
            technical_specs=item_data.get("technical_specs"),
            material_preference=item_data.get("material_preference"),
            color_preference=item_data.get("color_preference"),
            brand_preference=item_data.get("brand_preference"),
            special_instruction=item_data.get("special_instruction"),
            quantity=item_data.get("quantity"),
            confidence=item_data.get("confidence"),
            is_accepted=item_data.get("is_accepted"),
        )
        created = await self.item_repository.create(session, item)
        logger.info("Item added to space", extra={"space_id": space_id, "item_id": created.id})
        return created

    async def analyze_document(self, session: AsyncSession, document_id: int) -> Dict[str, Any]:
        """Analyze document and create project"""
        # Get the document
        documents = await self.document_repository.get_by_id(session, document_id)
        if not documents:
            raise ValueError(f"Document {document_id} not found")
        document = documents[0] if isinstance(documents, list) else documents

        logger.info("Starting document analysis", extra={"document_id": document_id})

        try:
            orchestrator = OrchestratorAgent(session)
            project_id = await orchestrator.create_or_update_project_from_document(document)
            logger.info(
                "Document analysis complete",
                extra={"document_id": document_id, "project_id": project_id},
            )
            return await self.get_project_analysis(session, project_id)
        except Exception as exc:
            logger.exception(
                "Document analysis failed",
                extra={"document_id": document_id, "error": str(exc)},
            )
            raise

    async def get_all_documents(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get all uploaded documents"""
        documents = await self.document_repository.get_all(session)
        logger.info("Documents fetched", extra={"count": len(documents)})
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "upload_date": doc.upload_date,
                "project_id": doc.project_id,
                "has_analysis": doc.project_id is not None
            }
            for doc in documents
        ]


    async def get_project(self, session: AsyncSession, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        project = await self.project_repository.get_by_id(session, project_id)
        if project:
            logger.info("Project fetched", extra={"project_id": project_id})
        else:
            logger.info("Project not found", extra={"project_id": project_id})
        return project

    async def get_project_analysis(self, session: AsyncSession, project_id: int) -> Optional[Dict[str, Any]]:
        """Get extraction results for a project"""
        # Use selectinload to eagerly load relationships
        result = await session.execute(
            select(Project)
            .options(selectinload(Project.spaces).selectinload(Space.items))
            .filter(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None

        result_dict = {
            "id": project.id,
            "name": project.name,
            "client_type": project.client_type,
            "location": project.location,
            "timeline": project.timeline,
            "budget_range": project.budget_range,
            "created_at": project.created_at,
            "spaces": []
        }

        for space in project.spaces:
            space_dict = {
                "id": space.id,
                "room_type": space.room_type,
                "dimension": space.dimension,
                "area": space.area,
                "items": []
            }
            for item in space.items:
                item_dict = {
                    "id": item.id,
                    "name": item.name,
                    "category": item.category,
                    "technical_specs": item.technical_specs,
                    "material_preference": item.material_preference,
                    "color_preference": item.color_preference,
                    "brand_preference": item.brand_preference,
                    "special_instruction": item.special_instruction,
                    "quantity": item.quantity,
                    "confidence": item.confidence,
                    "is_accepted": item.is_accepted,
                }
                space_dict["items"].append(item_dict)
            result_dict["spaces"].append(space_dict)

        logger.info("Project analysis fetched", extra={"project_id": project_id})
        return result_dict

    async def update_requirement(self, session: AsyncSession, item_id: int, updates: Dict[str, Any]) -> Optional[Item]:
        """Update a requirement (item)"""
        item = await self.item_repository.get_by_id(session, item_id)
        if not item:
            return None

        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)

        updated = await self.item_repository.update(session, item)
        logger.info("Requirement updated", extra={"item_id": item_id, "project_id": id})
        return updated

    async def prompt_add(self, session: AsyncSession, project_id: int, prompt: str) -> Dict[str, Any]:
        """Use a prompt to add spaces/items to an existing project."""
        project = await session.execute(
            select(Project)
            .options(selectinload(Project.spaces).selectinload(Space.items))
            .filter(Project.id == project_id)
        )
        project_entity = project.scalar_one_or_none()
        if not project_entity:
            return {"error": "Project not found"}

        # Build context summary
        summaries = []
        for space in project_entity.spaces:
            item_summaries = ", ".join([f"{i.name} (qty {i.quantity or 1})" for i in space.items]) if space.items else "no items"
            summaries.append(f"{space.room_type}: {item_summaries}")
        context_summary = "; ".join(summaries) if summaries else "No spaces yet."

        additions = await self.prompt_add_agent.generate_additions(context_summary, prompt)

        # Apply additions
        created_spaces = []
        created_items = []
        for space_add in additions:
            # match by room_type (case-insensitive)
            existing_space = next(
                (s for s in project_entity.spaces if s.room_type.lower() == (space_add.room_type or "").lower()),
                None,
            )
            if existing_space is None:
                new_space = Space(
                    project_id=project_id,
                    room_type=space_add.room_type,
                    dimension=space_add.dimension,
                    area=space_add.area,
                )
                existing_space = await self.space_repository.create(session, new_space)
                project_entity.spaces.append(existing_space)
                created_spaces.append(existing_space.id)

            for item_add in space_add.items:
                item = Item(
                    space_id=existing_space.id,
                    name=item_add.name or item_add.category.value if hasattr(item_add.category, "value") else item_add.category,
                    category=item_add.category.value if hasattr(item_add.category, "value") else item_add.category,
                    technical_specs=item_add.technical_specs,
                    material_preference=item_add.material_preference,
                    color_preference=item_add.color_preference,
                    brand_preference=item_add.brand_preference,
                    special_instruction=item_add.special_instruction,
                    quantity=item_add.quantity,
                    confidence=item_add.confidence,
                )
                created_item = await self.item_repository.create(session, item)
                created_items.append(created_item.id)

        logger.info(
            "Prompt-based additions applied",
            extra={
                "project_id": project_id,
                "prompt": prompt,
                "created_spaces": created_spaces,
                "created_items": created_items,
            },
        )

        return {
            "created_spaces": created_spaces,
            "created_items": created_items,
        }

    async def export_requirements(self, session: AsyncSession, project_id: int, format: str = "json") -> Any:
        """Export requirements in specified format"""
        analysis = await self.get_project_analysis(session, project_id)
        if not analysis:
            return None

        if format == "json":
            filtered_spaces = []
            for space in analysis.get("spaces", []):
                filtered_items = [i for i in space.get("items", []) if i.get("is_accepted") is True]
                if filtered_items:
                    filtered_spaces.append({**space, "items": filtered_items})
            logger.info("Exported requirements (json)", extra={"project_id": project_id})
            return {**analysis, "spaces": filtered_spaces}
        elif format == "csv":
            rows = []
            for space in analysis.get("spaces", []):
                for item in space.get("items", []):
                    if item.get("is_accepted") is not True:
                        continue
                    rows.append({
                        "project_name": analysis["name"],
                        "space": space["room_type"],
                        "item_name": item["name"],
                        "category": item["category"],
                        "technical_specs": item.get("technical_specs", ""),
                        "material": item.get("material_preference", ""),
                        "color": item.get("color_preference", ""),
                        "brand": item.get("brand_preference", ""),
                        "quantity": item.get("quantity", "")
                    })
            logger.info("Exported requirements (csv)", extra={"project_id": project_id, "rows": len(rows)})
            return rows
        return None

# Singleton instance with injected repositories
project_service = ProjectService()
