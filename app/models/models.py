from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ItemCategory(str, Enum):
    FURNITURE = "Furniture"
    FIXTURE = "Fixture"
    APPLIANCE = "Appliance"
    DECOR_ITEM = "Decor Item"
    OTHERS = "Others"

class ItemRequirement(BaseModel):
    name: Optional[str] = Field(None, description="Human-readable item name (e.g., 'Standing desk')")
    category: ItemCategory = Field(description="Category of the item")
    technical_specs: Optional[str] = Field(None, description="Technical specifications")
    material_preference: Optional[str] = Field(None, description="Material preferences")
    color_preference: Optional[str] = Field(None, description="Color preferences")
    brand_preference: Optional[str] = Field(None, description="Brand preferences")
    special_instruction: Optional[str] = Field(None, description="Special instructions")
    quantity: Optional[int] = Field(None, description="Quantity")
    confidence: Optional[float] = Field(None, description="Confidence score for this item (0-1)")
    is_accepted: Optional[bool] = Field(None, description="Whether the item has been accepted (HITL)")

class SpaceRequirements(BaseModel):
    room_type: str = Field(description="Type of the room")
    dimension: Optional[str] = Field(None, description="Dimensions")
    area: Optional[str] = Field(None, description="Area")
    items: List[ItemRequirement] = Field(default_factory=list, description="List of item requirements")

class ProjectMetadata(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    client_type: Optional[str] = Field(None, description="Client type")
    location: Optional[str] = Field(None, description="Location")
    timeline: Optional[str] = Field(None, description="Timeline")
    budget_range: Optional[str] = Field(None, description="Budget range")

class ExtractionResult(BaseModel):
    project_metadata: ProjectMetadata
    spaces: List[SpaceRequirements]
