from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.models.schemas import (
    TaskCreate, TaskUpdate, TaskResponse,
    NaturalLanguageTaskParseRequest, NaturalLanguageTaskParseResponse
)
from backend.app.services.task_service import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("", response_model=List[TaskResponse])
def get_all_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None
):
    return task_service.get_tasks(status=status, priority=priority, category=category, search=search)

@router.post("", response_model=TaskResponse)
def create_new_task(task: TaskCreate):
    return task_service.create_task(task)

@router.post("/parse", response_model=NaturalLanguageTaskParseResponse)
def parse_natural_language_task(req: NaturalLanguageTaskParseRequest):
    success, parsed_task, explanation = task_service.parse_natural_language_task(req.text)
    return NaturalLanguageTaskParseResponse(
        success=success,
        parsed_task=parsed_task,
        explanation=explanation
    )

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updates: TaskUpdate):
    res = task_service.update_task(task_id, updates)
    if not res:
        raise HTTPException(status_code=404, detail="Task not found")
    return res

@router.delete("/{task_id}")
def delete_task(task_id: int):
    deleted = task_service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "deleted", "id": task_id}

