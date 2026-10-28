from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.models.schemas import MemoryCreate, MemoryUpdate, MemoryResponse
from backend.app.services.memory_service import memory_service

router = APIRouter(prefix="/api/memory", tags=["memory"])

@router.get("", response_model=List[MemoryResponse])
def get_memories(category: Optional[str] = None):
    return memory_service.get_all_memories(category=category)

@router.post("", response_model=MemoryResponse)
def add_memory(memory: MemoryCreate):
    return memory_service.add_memory(memory)

@router.put("/{memory_id}", response_model=MemoryResponse)
def update_memory(memory_id: int, updates: MemoryUpdate):
    res = memory_service.update_memory(memory_id, updates)
    if not res:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return res

@router.delete("/{memory_id}")
def delete_memory(memory_id: int):
    success = memory_service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return {"status": "deleted", "id": memory_id}

@router.get("/export")
def export_memories():
    memories = memory_service.get_all_memories()
    markdown = memory_service.get_memory_context_string()
    return {
        "memories": [m.model_dump() for m in memories],
        "markdown_format": markdown
    }

