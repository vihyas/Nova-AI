import time
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.app.database import get_db
from backend.app.models.schemas import ChatResponse, ActionTrigger
from backend.app.services.task_service import task_service
from backend.app.services.memory_service import memory_service
from backend.app.services.rag_service import rag_service
from backend.app.services.analytics_service import analytics_service
from backend.app.services.llm_service import llm_service

class AgentService:
    def classify_intent(self, text: str) -> str:
        lower = text.lower()
        if re.search(r"\b(create|add|new|schedule|set|complete|finish)\s+(a\s+)?task\b", lower) or any(w in lower for w in ["study java", "remind me to", "todo"]):
            return "task_architect"
        if any(w in lower for w in ["summarise", "summarize", "pdf", "document", "what does page", "citation", "read file"]):
            return "doc_researcher"
        if any(w in lower for w in ["remember", "my preference", "i prefer", "my goal", "forget that", "saved memories"]):
            return "memory_keeper"
        if any(w in lower for w in ["productivity", "analytics", "stats", "velocity", "how am i doing", "report"]):
            return "productivity_coach"
        return "nova_general"

    def log_agent_action(self, agent_name: str, action: str, input_data: Any, output_data: Any, status: str, exec_time: int):
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_logs (agent_name, action, input_data, output_data, status, execution_time_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_name,
                action,
                json.dumps(input_data) if not isinstance(input_data, str) else input_data,
                json.dumps(output_data) if not isinstance(output_data, str) else output_data,
                status,
                exec_time,
                now
            ))

    async def execute_orchestration(
        self,
        message: str,
        session_id: str = "default",
        requested_agent: str = "auto",
        provider: Optional[str] = None,
        context_document_id: Optional[int] = None
    ) -> ChatResponse:
        start_time = time.time()
        
        # 1. Determine Agent Role
        agent_type = requested_agent if requested_agent != "auto" else self.classify_intent(message)
        agent_display_names = {
            "nova_general": "NOVA Core Assistant",
            "task_architect": "Task Architect Agent",
            "doc_researcher": "Document Intelligence Agent",
            "memory_keeper": "Memory Keeper Agent",
            "productivity_coach": "Productivity Coach Agent"
        }
        agent_name = agent_display_names.get(agent_type, "NOVA Assistant")

        # 2. Extract & Inject Memories
        user_memories = memory_service.extract_and_save_memories_from_text(message)
        memory_context = memory_service.get_memory_context_string()
        used_memories_list = [f"{m.key}: {m.value}" for m in user_memories] or [m.key for m in memory_service.get_all_memories()[:3]]

        triggered_tools: List[ActionTrigger] = []
        rag_sources: List[Dict[str, Any]] = []
        reply = ""

        # 3. Handle Specific Agent Workflows & Tools
        if agent_type == "task_architect":
            # Attempt natural language task parsing
            success, parsed_task, explanation = task_service.parse_natural_language_task(message)
            if success and parsed_task:
                created = task_service.create_task(parsed_task)
                triggered_tools.append(ActionTrigger(
                    tool_name="task_manager",
                    action="create_task",
                    parameters=parsed_task.model_dump(),
                    requires_confirmation=False,
                    status="executed",
                    result={"id": created.id, "title": created.title, "due_date": created.due_date}
                ))
                reply = (
                    f"✅ **Task Created Successfully!**\n\n"
                    f"• **Title**: {created.title}\n"
                    f"• **Due Date**: {created.due_date}\n"
                    f"• **Estimated Duration**: {created.duration_minutes} minutes\n"
                    f"• **Priority**: {created.priority.upper()}\n"
                    f"• **Category**: {created.category}\n\n"
                    f"*System Note*: {explanation}"
                )
            else:
                # LLM response for task management discussion
                reply = await llm_service.generate_response(
                    messages=[{"role": "user", "content": message}],
                    system_instruction=f"You are the Task Architect Agent for NOVA AI. Help manage schedule and goals.\n{memory_context}",
                    provider=provider
                )

        elif agent_type == "doc_researcher":
            # Check if there are documents
            docs = rag_service.list_documents()
            target_doc_id = context_document_id or (docs[0].id if docs else None)
            
            if target_doc_id:
                query_res = await rag_service.query_document(target_doc_id, message)
                reply = query_res.answer
                rag_sources = query_res.citations
                triggered_tools.append(ActionTrigger(
                    tool_name="rag_engine",
                    action="vector_search_and_synthesis",
                    parameters={"query": message, "doc_id": target_doc_id},
                    requires_confirmation=False,
                    status="executed",
                    result={"citations_count": len(rag_sources)}
                ))
            else:
                reply = (
                    "📄 **Document Intelligence Agent**:\n\n"
                    "No document is currently selected or uploaded. "
                    "Please navigate to the **Knowledge Hub** to upload a PDF (such as course materials, research papers, or manuals), "
                    "and I will extract key concepts, study questions, and page citations for you!"
                )

        elif agent_type == "memory_keeper":
            if user_memories:
                saved_str = ", ".join([f"**{m.key}** = *{m.value}*" for m in user_memories])
                reply = f"🧠 **Personal Memory Updated!**\n\nI have committed the following information to your long-term memory vault:\n{saved_str}\n\nYou can review or edit all memories at any time under the **Memory** tab."
            else:
                memories_list = memory_service.get_all_memories()
                items_str = "\n".join([f"• **{m.key}** ({m.category}): {m.value}" for m in memories_list])
                reply = f"🧠 **Here are your currently saved personal preferences & goals:**\n\n{items_str}\n\nTell me anything you want me to remember or change!"

        elif agent_type == "productivity_coach":
            metrics = analytics_service.get_productivity_metrics()
            reply = (
                f"📊 **Productivity Performance Report**\n\n"
                f"• **Completion Rate**: {metrics.completion_rate}%\n"
                f"• **Velocity Score**: {metrics.velocity_score}/100\n"
                f"• **Active Tasks**: {metrics.pending_tasks} pending, {metrics.in_progress_tasks} in progress\n"
                f"• **Total Focused Minutes**: {metrics.total_study_minutes} mins\n\n"
                f"💡 **Coaching Insights**:\n" + "\n".join([f"• {x}" for x in metrics.ai_coaching_insights])
            )
            triggered_tools.append(ActionTrigger(
                tool_name="analytics_engine",
                action="generate_productivity_report",
                parameters={},
                requires_confirmation=False,
                status="executed",
                result={"velocity": metrics.velocity_score}
            ))

        else: # nova_general
            prompt_context = f"{memory_context}\n\nYou are NOVA AI — an advanced multimodal personal assistant capable of voice interaction, productivity planning, and document intelligence."
            reply = await llm_service.generate_response(
                messages=[{"role": "user", "content": message}],
                system_instruction=prompt_context,
                provider=provider
            )

        elapsed_ms = int((time.time() - start_time) * 1000)
        self.log_agent_action(
            agent_name=agent_name,
            action=f"process_user_query_{agent_type}",
            input_data={"message": message, "session_id": session_id},
            output_data={"reply_length": len(reply), "tools_count": len(triggered_tools)},
            status="success",
            exec_time=elapsed_ms
        )

        # Record in chat_messages table
        now_str = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content, agent_name, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, "user", message, "User", json.dumps({}), now_str))
            cursor.execute("""
                INSERT INTO chat_messages (session_id, role, content, agent_name, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, "assistant", reply, agent_name, json.dumps({
                "tools": [t.model_dump() for t in triggered_tools],
                "sources": rag_sources
            }), now_str))

        suggested_actions = [
            "Show my tasks for today",
            "Explain linked lists in Java",
            "Analyze my productivity velocity",
            "Create a task for tomorrow at 6 PM"
        ]

        # For spoken output, provide a concise version
        audio_text = reply.split("\n\n")[0].replace("*", "").replace("#", "")

        return ChatResponse(
            reply=reply,
            agent_name=agent_name,
            suggested_actions=suggested_actions,
            triggered_tools=triggered_tools,
            used_memories=used_memories_list,
            rag_sources=rag_sources,
            audio_text=audio_text
        )

    def get_recent_agent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

agent_service = AgentService()
