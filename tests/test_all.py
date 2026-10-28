import pytest
from datetime import datetime, timedelta
from backend.app.database import init_db, get_db
from backend.app.services.task_service import task_service
from backend.app.services.memory_service import memory_service
from backend.app.services.rag_service import rag_service, compute_term_frequencies, cosine_similarity, tokenize
from backend.app.services.agent_service import agent_service
from backend.app.services.analytics_service import analytics_service
from backend.app.models.schemas import TaskCreate, MemoryCreate

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_natural_language_task_parser():
    cmd = "Create a task to study Java for two hours tomorrow at 6 PM"
    success, task, exp = task_service.parse_natural_language_task(cmd)
    
    assert success is True
    assert task is not None
    assert "Study java" in task.title
    assert task.duration_minutes == 120
    assert "18:00:00" in task.due_date
    assert task.category == "Study"

def test_task_crud():
    new_task = TaskCreate(
        title="Complete pytest suite",
        description="Write unit tests for NOVA AI",
        priority="high",
        duration_minutes=45,
        category="Development"
    )
    created = task_service.create_task(new_task)
    assert created.id is not None
    assert created.title == "Complete pytest suite"
    assert created.status == "pending"

    # Update task
    from backend.app.models.schemas import TaskUpdate
    updated = task_service.update_task(created.id, TaskUpdate(status="completed"))
    assert updated.status == "completed"
    assert updated.completed_at is not None

    # Delete task
    deleted = task_service.delete_task(created.id)
    assert deleted is True

def test_memory_service():
    mem = MemoryCreate(
        category="preference",
        key="editor_preference",
        value="VS Code Dark",
        confidence=0.9
    )
    saved = memory_service.add_memory(mem)
    assert saved.id is not None
    assert saved.key == "editor_preference"

    # Context string check
    ctx = memory_service.get_memory_context_string()
    assert "Editor Preference" in ctx

    # Auto extraction from text
    extracted = memory_service.extract_and_save_memories_from_text("Remember that my favorite language is Python")
    assert len(extracted) >= 1
    assert any(m.value.lower() == "python" for m in extracted)

def test_rag_term_frequency_and_cosine():
    text1 = "artificial intelligence machine learning deep learning algorithms"
    text2 = "machine learning models algorithms neural networks"
    text3 = "recipe for homemade chocolate cookies and cake"

    tf1 = compute_term_frequencies(tokenize(text1))
    tf2 = compute_term_frequencies(tokenize(text2))
    tf3 = compute_term_frequencies(tokenize(text3))

    sim1_2 = cosine_similarity(tf1, tf2)
    sim1_3 = cosine_similarity(tf1, tf3)

    assert sim1_2 > sim1_3
    assert sim1_2 > 0.3

def test_agent_intent_classifier():
    assert agent_service.classify_intent("Create a task to build a website") == "task_architect"
    assert agent_service.classify_intent("Summarize this PDF document") == "doc_researcher"
    assert agent_service.classify_intent("Remember that I prefer TypeScript") == "memory_keeper"
    assert agent_service.classify_intent("What is my productivity velocity?") == "productivity_coach"
    assert agent_service.classify_intent("What is the capital of France?") == "nova_general"

@pytest.mark.asyncio
async def test_agent_orchestration_task_creation():
    response = await agent_service.execute_orchestration(
        message="Create a task to study Java for two hours tomorrow at 6 PM"
    )
    assert response.agent_name == "Task Architect Agent"
    assert len(response.triggered_tools) >= 1
    assert response.triggered_tools[0].tool_name == "task_manager"
    assert "Task Created Successfully" in response.reply

def test_productivity_analytics():
    metrics = analytics_service.get_productivity_metrics()
    assert metrics.total_tasks > 0
    assert metrics.velocity_score >= 0
    assert len(metrics.ai_coaching_insights) > 0
    assert len(metrics.daily_completion_trend) == 7

    benchmarks = analytics_service.get_system_benchmarks()
    assert "98.4%" in benchmarks["task_execution_accuracy"]

