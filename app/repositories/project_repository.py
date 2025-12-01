from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.logging import get_logger
from app.entities.entities import Project, Space, Item, Document

logger = get_logger(__name__)

class ProjectRepository:
    async def create(self, session: AsyncSession, project: Project) -> Project:
        session.add(project)
        await session.commit()
        await session.refresh(project)
        logger.info("Project created", extra={"project_id": project.id})
        return project

    async def get_by_id(self, session: AsyncSession, project_id: int) -> Optional[Project]:
        result = await session.execute(
            select(Project).filter(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession) -> List[Project]:
        result = await session.execute(select(Project))
        return result.scalars().all()

    async def update(self, session: AsyncSession, project: Project) -> Project:
        await session.commit()
        await session.refresh(project)
        logger.info("Project updated", extra={"project_id": project.id})
        return project

class SpaceRepository:
    async def create(self, session: AsyncSession, space: Space) -> Space:
        session.add(space)
        await session.commit()
        await session.refresh(space)
        logger.info("Space created", extra={"space_id": space.id, "project_id": space.project_id})
        return space

    async def get_by_id(self, session: AsyncSession, space_id: int) -> Optional[Space]:
        result = await session.execute(
            select(Space).filter(Space.id == space_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_id(self, session: AsyncSession, project_id: int) -> List[Space]:
        result = await session.execute(
            select(Space).filter(Space.project_id == project_id)
        )
        return result.scalars().all()

class ItemRepository:
    async def create(self, session: AsyncSession, item: Item) -> Item:
        session.add(item)
        await session.commit()
        await session.refresh(item)
        logger.info(
            "Item created",
            extra={"item_id": item.id, "space_id": item.space_id, "category": item.category},
        )
        return item

    async def get_by_id(self, session: AsyncSession, item_id: int) -> Optional[Item]:
        result = await session.execute(
            select(Item).filter(Item.id == item_id)
        )
        return result.scalar_one_or_none()

    async def update(self, session: AsyncSession, item: Item) -> Item:
        await session.commit()
        await session.refresh(item)
        logger.info("Item updated", extra={"item_id": item.id, "space_id": item.space_id})
        return item

class DocumentRepository:
    async def create(self, session: AsyncSession, document: Document) -> Document:
        session.add(document)
        await session.commit()
        await session.refresh(document)
        logger.info("Document created", extra={"document_id": document.id, "filename": document.filename})
        return document

    async def get_by_id(self, session: AsyncSession, document_id: int) -> Optional[Document]:
        result = await session.execute(
            select(Document).filter(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_id(self, session: AsyncSession, project_id: int) -> List[Document]:
        result = await session.execute(
            select(Document).filter(Document.project_id == project_id)
        )
        return result.scalars().all()

    async def get_all(self, session: AsyncSession) -> List[Document]:
        result = await session.execute(select(Document).order_by(Document.upload_date.desc()))
        return result.scalars().all()

# Singleton instances
project_repository = ProjectRepository()
space_repository = SpaceRepository()
item_repository = ItemRepository()
document_repository = DocumentRepository()
