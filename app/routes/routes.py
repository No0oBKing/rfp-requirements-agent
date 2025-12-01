from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional

from fastapi import status

from app.core.db import get_session
from app.core.logging import get_logger
from app.services.project_service import project_service
from app.core.auth import create_access_token, verify_credentials, get_current_user
import shutil
import os
import csv
from io import StringIO

router = APIRouter()
logger = get_logger(__name__)


class ItemCreate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    technical_specs: Optional[str] = None
    material_preference: Optional[str] = None
    color_preference: Optional[str] = None
    brand_preference: Optional[str] = None
    special_instruction: Optional[str] = None
    quantity: Optional[int] = None
    confidence: Optional[float] = None
    is_accepted: Optional[bool] = None


class SpaceCreate(BaseModel):
    room_type: str
    dimension: Optional[str] = None
    area: Optional[str] = None
    items: Optional[List[ItemCreate]] = None


class PromptAddRequest(BaseModel):
    prompt: str


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
async def login(payload: LoginRequest):
    if not verify_credentials(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(payload.username)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/projects/upload")
async def upload_rfp(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Upload RFP document (does not create project or trigger analysis)"""
    # Save file temporarily
    file_path = f"/tmp/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document_id = await project_service.upload_document(session, file.filename, file_path)
        return {
            "document_id": document_id,
            "message": "Document uploaded successfully",
            "filename": file.filename
        }
    except Exception as exc:
        logger.exception("File upload failed", extra={"filename": file.filename, "error": str(exc)})
        raise HTTPException(status_code=500, detail="Upload failed")

@router.get("/documents")
async def list_documents(session: AsyncSession = Depends(get_session)):
    """List all uploaded documents"""
    documents = await project_service.get_all_documents(session)
    return {"documents": documents}


@router.get("/projects/{id}")
async def get_project(
    id: int,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Get project details"""
    project = await project_service.get_project(session, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "id": project.id,
        "name": project.name,
        "client_type": project.client_type,
        "location": project.location,
        "timeline": project.timeline,
        "budget_range": project.budget_range,
        "created_at": project.created_at
    }

@router.get("/projects/{id}/analysis")
async def get_analysis(
    id: int,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Get extraction results"""
    analysis = await project_service.get_project_analysis(session, id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Project not found")
    return analysis

@router.post("/documents/{document_id}/analyze")
async def trigger_analysis(
    document_id: int,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Trigger analysis for uploaded document - creates project"""
    try:
        result = await project_service.analyze_document(session, document_id)
        return {"message": "Analysis complete", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Analysis endpoint failed", extra={"document_id": document_id, "error": str(e)})
        raise HTTPException(status_code=500, detail="Analysis failed")

@router.patch("/projects/{id}/requirements/{req_id}")
async def update_requirement(
    id: int,
    req_id: int,
    updates: dict,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Update requirement (HITL)"""
    item = await project_service.update_requirement(session, req_id, updates)
    if not item:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "technical_specs": item.technical_specs,
        "material_preference": item.material_preference,
        "color_preference": item.color_preference,
        "brand_preference": item.brand_preference,
        "special_instruction": item.special_instruction,
        "quantity": item.quantity,
        "is_accepted": item.is_accepted,
    }

@router.post("/projects/{id}/requirements")
async def add_requirement(
    id: int,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Add requirement manually"""
    raise HTTPException(status_code=501, detail="Manual requirement addition not yet implemented")


@router.post("/projects/{id}/spaces")
async def add_space(
    id: int,
    payload: SpaceCreate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Add a new space (optionally with items) to a project."""
    try:
        space = await project_service.add_space_with_items(session, id, payload.model_dump())
        if not space:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"space_id": space.id, "project_id": id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Add space failed", extra={"project_id": id, "error": str(exc)})
        raise HTTPException(status_code=500, detail="Failed to add space")


@router.post("/spaces/{space_id}/items")
async def add_item_to_space(
    space_id: int,
    payload: ItemCreate,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Add a new item to an existing space."""
    try:
        item = await project_service.add_item_to_space(session, space_id, payload.model_dump())
        if not item:
            raise HTTPException(status_code=404, detail="Space not found")
        return {"item_id": item.id, "space_id": space_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Add item failed", extra={"space_id": space_id, "error": str(exc)})
        raise HTTPException(status_code=500, detail="Failed to add item")


@router.post("/projects/{id}/prompt-add")
async def prompt_add(
    id: int,
    payload: PromptAddRequest,
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Add spaces/items via a natural-language prompt."""
    try:
        result = await project_service.prompt_add(session, id, payload.prompt)
        if result.get("error"):
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Prompt add failed", extra={"project_id": id, "error": str(exc)})
        raise HTTPException(status_code=500, detail="Failed to add via prompt")

@router.get("/projects/{id}/export")
async def export_requirements(
    id: int,
    format: str = "json",
    session: AsyncSession = Depends(get_session),
    user: str = Depends(get_current_user),
):
    """Export requirements (JSON/CSV)"""
    data = await project_service.export_requirements(session, id, format)
    
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if format == "csv":
        output = StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            csv_content = output.getvalue()
            return JSONResponse(content={"csv": csv_content})
        return JSONResponse(content={"csv": ""})
    
    return data
