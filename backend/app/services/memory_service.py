import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.app.database import get_db
from backend.app.models.schemas import MemoryCreate, MemoryUpdate, MemoryResponse

class MemoryService:
    def get_all_memories(self, category: Optional[str] = None) -> List[MemoryResponse]:
        with get_db() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute("SELECT * FROM memories WHERE category = ? ORDER BY id DESC", (category,))
            else:
                cursor.execute("SELECT * FROM memories ORDER BY category, id DESC")
            return [MemoryResponse(**dict(r)) for r in cursor.fetchall()]

    def add_memory(self, memory: MemoryCreate) -> MemoryResponse:
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            # Check if key exists in category, update if so
            cursor.execute("SELECT id FROM memories WHERE category = ? AND key = ?", (memory.category, memory.key))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE memories SET value = ?, confidence = ?, updated_at = ?
                    WHERE id = ?
                """, (memory.value, memory.confidence or 1.0, now, existing["id"]))
                memory_id = existing["id"]
            else:
                cursor.execute("""
                    INSERT INTO memories (category, key, value, confidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (memory.category, memory.key, memory.value, memory.confidence or 1.0, now, now))
                memory_id = cursor.lastrowid
            
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            return MemoryResponse(**dict(cursor.fetchone()))

    def update_memory(self, memory_id: int, updates: MemoryUpdate) -> Optional[MemoryResponse]:
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            current = cursor.fetchone()
            if not current:
                return None
            
            update_data = updates.model_dump(exclude_unset=True)
            if not update_data:
                return MemoryResponse(**dict(current))
            
            update_data["updated_at"] = now
            set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
            values = list(update_data.values()) + [memory_id]
            cursor.execute(f"UPDATE memories SET {set_clause} WHERE id = ?", values)
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            return MemoryResponse(**dict(cursor.fetchone()))

    def delete_memory(self, memory_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def get_memory_context_string(self) -> str:
        """
        Formats active user preferences into a clean Markdown system context for LLM agents.
        """
        memories = self.get_all_memories()
        if not memories:
            return ""
        
        lines = ["### User Profile & Saved Memories:"]
        for m in memories:
            clean_key = m.key.replace("_", " ").title()
            lines.append(f"- **{clean_key}** ({m.category}): {m.value}")
        return "\n".join(lines)

    def extract_and_save_memories_from_text(self, text: str) -> List[MemoryResponse]:
        """
        Extracts preferences automatically when user says:
        'Remember that I like TypeScript', 'My goal is to learn Rust', etc.
        """
        saved = []
        patterns = [
            (r"(?:remember\s+(?:that)?|please\s+note\s+(?:that)?)\s+(?:i\s+prefer|i\s+like|my\s+favorite\s+language\s+is)\s+([a-zA-Z0-9#+ ]+)", "preference", "preferred_language"),
            (r"(?:my\s+goal\s+is\s+to|i\s+want\s+to\s+learn|my\s+learning\s+target\s+is)\s+([^.!?]+)", "goal", "learning_goal"),
            (r"(?:remind\s+me\s+usually\s+at|my\s+preferred\s+time\s+is)\s+([^.!?]+)", "preference", "preferred_reminder_time"),
            (r"(?:i\s+speak|i\s+also\s+know|language\s+preference\s+is)\s+([a-zA-Z, ]+)", "preference", "languages_spoken")
        ]
        
        for pat, cat, key in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                mem = self.add_memory(MemoryCreate(category=cat, key=key, value=val, confidence=0.9))
                saved.append(mem)
        return saved

memory_service = MemoryService()

