import json
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from backend.app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from backend.app.services.agent_service import agent_service
from backend.app.database import get_db

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def process_chat(req: ChatRequest):
    try:
        response = await agent_service.execute_orchestration(
            message=req.message,
            session_id=req.session_id or "default",
            requested_agent=req.agent_name or "auto",
            provider=req.provider,
            context_document_id=req.context_document_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ChatMessage])
def get_chat_history(session_id: str = "default", limit: int = 50):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content, agent_name, created_at, metadata_json
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY id ASC
            LIMIT ?
        """, (session_id, limit))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            meta = json.loads(r["metadata_json"]) if r["metadata_json"] else {}
            result.append(ChatMessage(
                role=r["role"],
                content=r["content"],
                agent_name=r["agent_name"],
                created_at=r["created_at"],
                metadata=meta
            ))
        return result

@router.delete("/history")
def clear_chat_history(session_id: str = "default"):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        return {"status": "cleared", "session_id": session_id}

@router.get("/agents/logs")
def get_agent_logs(limit: int = 25):
    return agent_service.get_recent_agent_logs(limit=limit)

