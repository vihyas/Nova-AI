from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Chat & Assistant Schemas ---
class ChatMessage(BaseModel):
    role: str # user, assistant, system, tool
    content: str
    agent_name: Optional[str] = "NOVA"
    created_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    agent_name: Optional[str] = "auto" # auto, general, task_architect, doc_researcher, memory_keeper, productivity_coach
    provider: Optional[str] = None # gemini, openai, offline
    temperature: Optional[float] = 0.7
    voice_enabled: Optional[bool] = False
    context_document_id: Optional[int] = None

class ActionTrigger(BaseModel):
    tool_name: str
    action: str
    parameters: Dict[str, Any]
    requires_confirmation: bool = False
    status: str = "executed" # pending_approval, executed, rejected
    result: Optional[Any] = None

class ChatResponse(BaseModel):
    reply: str
    agent_name: str
    suggested_actions: List[str] = []
    triggered_tools: List[ActionTrigger] = []
    used_memories: List[str] = []
    rag_sources: List[Dict[str, Any]] = []
    audio_text: Optional[str] = None

# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium" # low, medium, high, urgent
    status: Optional[str] = "pending" # pending, in_progress, completed
    due_date: Optional[str] = None
    duration_minutes: Optional[int] = 30
    category: Optional[str] = "General"
    tags: Optional[str] = ""

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    duration_minutes: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[str] = None

class TaskResponse(TaskBase):
    id: int
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None

class NaturalLanguageTaskParseRequest(BaseModel):
    text: str

class NaturalLanguageTaskParseResponse(BaseModel):
    success: bool
    parsed_task: Optional[TaskCreate] = None
    explanation: str

# --- Reminder Schemas ---
class ReminderCreate(BaseModel):
    title: str
    remind_at: str
    recurrence: Optional[str] = "none" # none, daily, weekly

class ReminderResponse(BaseModel):
    id: int
    title: str
    remind_at: str
    recurrence: str
    status: str # pending, dismissed, snoozed
    created_at: str

# --- Memory Schemas ---
class MemoryCreate(BaseModel):
    category: str # preference, goal, habit, fact, constraint
    key: str
    value: str
    confidence: Optional[float] = 1.0

class MemoryUpdate(BaseModel):
    category: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    confidence: Optional[float] = None

class MemoryResponse(BaseModel):
    id: int
    category: str
    key: str
    value: str
    confidence: float
    created_at: str
    updated_at: str

# --- Document & RAG Schemas ---
class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int
    page_count: int
    summary: str
    created_at: str

class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    page_number: int
    content: str

class DocumentQueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4

class DocumentQueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[Dict[str, Any]]
    related_questions: List[str]

class StudyGuideResponse(BaseModel):
    document_id: int
    document_name: str
    summary: str
    key_points: List[str]
    important_dates_and_milestones: List[str]
    study_questions: List[Dict[str, str]] # question, answer_page

# --- Analytics Schemas ---
class ProductivityMetrics(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completion_rate: float
    urgent_tasks_count: int
    total_study_minutes: int
    velocity_score: int # 0 to 100
    category_distribution: Dict[str, int]
    daily_completion_trend: List[Dict[str, Any]]
    ai_coaching_insights: List[str]

# --- Settings Schemas ---
class SettingsUpdate(BaseModel):
    default_provider: Optional[str] = None
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    temperature: Optional[float] = None
    system_language: Optional[str] = None
    voice_speed: Optional[float] = None
    voice_pitch: Optional[float] = None

class SettingsResponse(BaseModel):
    app_name: str
    version: str
    default_provider: str
    gemini_api_key_configured: bool
    gemini_model: str
    openai_api_key_configured: bool
    openai_model: str
    temperature: float
    system_language: str
    voice_speed: float
    voice_pitch: float

