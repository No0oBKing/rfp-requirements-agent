from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime
from typing import List, Optional

class Base(DeclarativeBase):
    pass

class BaseSQLEntity(Base):
    __abstract__ = True
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)
    version = Column(Integer, default=1, nullable=False)

class Project(BaseSQLEntity):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    client_type = Column(String, nullable=True)
    location = Column(String, nullable=True)
    timeline = Column(String, nullable=True)
    budget_range = Column(String, nullable=True)

    spaces = relationship("Space", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")

class Document(BaseSQLEntity):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True) # Optional: if we store the file
    upload_date = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")

class Space(BaseSQLEntity):
    __tablename__ = "spaces"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    room_type = Column(String, nullable=False)
    dimension = Column(String, nullable=True)
    area = Column(String, nullable=True)

    project = relationship("Project", back_populates="spaces")
    items = relationship("Item", back_populates="space", cascade="all, delete-orphan")

class Item(BaseSQLEntity):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    space_id = Column(Integer, ForeignKey("spaces.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    technical_specs = Column(String, nullable=True)
    material_preference = Column(String, nullable=True)
    color_preference = Column(String, nullable=True)
    brand_preference = Column(String, nullable=True)
    special_instruction = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    is_accepted = Column(Boolean, nullable=True)

    space = relationship("Space", back_populates="items")
