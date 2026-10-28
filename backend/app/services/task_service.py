import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from backend.app.database import get_db
from backend.app.models.schemas import TaskCreate, TaskUpdate, TaskResponse

class TaskService:
    def parse_natural_language_task(self, text: str) -> Tuple[bool, Optional[TaskCreate], str]:
        """
        Parses commands like:
        'Create a task to study Java for two hours tomorrow at 6 PM'
        'Add task: Build REST API by Friday 5pm'
        'Study machine learning today at 8:00'
        """
        clean_text = text.strip()
        lower = clean_text.lower()

        # Remove introductory triggers
        triggers = [
            r"^(please\s+)?(create|add|schedule|set(\s+up)?|make)(\s+a)?\s+task(\s+to|\s+for|\s*:)?\s*",
            r"^(can\s+you\s+)?(create|add|schedule|set(\s+up)?|make)(\s+a)?\s+task(\s+to|\s+for|\s*:)?\s*",
            r"^remind\s+me\s+to\s*",
            r"^i\s+need\s+to\s*",
            r"^task:\s*"
        ]
        task_body = clean_text
        for trig in triggers:
            match = re.match(trig, task_body, re.IGNORECASE)
            if match:
                task_body = task_body[match.end():].strip()
                break

        # Duration extraction
        duration_minutes = 60 # Default 60 mins
        duration_patterns = [
            (r"for\s+(\d+)\s+hours?", lambda m: int(m.group(1)) * 60),
            (r"for\s+(one|two|three|four|five|six|seven|eight)\s+hours?", lambda m: {
                "one": 60, "two": 120, "three": 180, "four": 240, "five": 300, "six": 360, "seven": 420, "eight": 480
            }[m.group(1).lower()]),
            (r"for\s+(\d+)\s+(mins|minutes)", lambda m: int(m.group(1))),
            (r"(\d+)\s+hour(s)?", lambda m: int(m.group(1)) * 60),
            (r"(\d+)\s+(mins|minutes)", lambda m: int(m.group(1)))
        ]
        for pattern, extractor in duration_patterns:
            dur_match = re.search(pattern, task_body, re.IGNORECASE)
            if dur_match:
                try:
                    duration_minutes = extractor(dur_match)
                    task_body = (task_body[:dur_match.start()] + task_body[dur_match.end():]).strip()
                    break
                except Exception:
                    pass

        # Target Date and Time extraction
        now = datetime.now()
        target_date = now.date()
        target_hour = 18
        target_minute = 0
        date_identified = False

        if "tomorrow" in lower:
            target_date = now.date() + timedelta(days=1)
            date_identified = True
            task_body = re.sub(r"\btomorrow\b", "", task_body, flags=re.IGNORECASE).strip()
        elif "today" in lower:
            target_date = now.date()
            date_identified = True
            task_body = re.sub(r"\btoday\b", "", task_body, flags=re.IGNORECASE).strip()
        elif "day after tomorrow" in lower:
            target_date = now.date() + timedelta(days=2)
            date_identified = True
            task_body = re.sub(r"\bday after tomorrow\b", "", task_body, flags=re.IGNORECASE).strip()

        # Time extraction: e.g. "at 6 PM", "at 6:30 pm", "at 18:00", "at 9 am"
        time_match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", task_body, re.IGNORECASE)
        if time_match:
            h = int(time_match.group(1))
            m = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3).lower() if time_match.group(3) else None
            if meridiem == "pm" and h < 12:
                h += 12
            elif meridiem == "am" and h == 12:
                h = 0
            target_hour = h
            target_minute = m
            date_identified = True
            task_body = (task_body[:time_match.start()] + task_body[time_match.end():]).strip()

        # Priority detection
        priority = "medium"
        if any(w in lower for w in ["urgent", "asap", "critical", "immediately"]):
            priority = "urgent"
        elif any(w in lower for w in ["important", "high priority", "essential"]):
            priority = "high"
        elif any(w in lower for w in ["low priority", "whenever", "optional"]):
            priority = "low"

        # Category and Tag detection
        category = "General"
        tags_list = []
        if any(w in lower for w in ["code", "bug", "api", "database", "programming", "software"]):
            category = "Development"
            tags_list.append("coding")
        if any(w in lower for w in ["study", "learn", "read", "course", "lecture", "revision"]):
            category = "Study"
            tags_list.append("education")
        if "java" in lower:
            tags_list.append("java")
        if "ml" in lower or "machine learning" in lower:
            tags_list.append("ml")

        # Cleanup residual connectors in task title
        task_title = re.sub(r"\s+", " ", task_body).strip()
        task_title = re.sub(r"^(to|at|on|for|by)\s+", "", task_title, flags=re.IGNORECASE).strip()
        if not task_title or len(task_title) < 2:
            return False, None, "Could not determine a valid task title. Please specify what you'd like to do."

        # Format full datetime string
        due_datetime = datetime(target_date.year, target_date.month, target_date.day, target_hour, target_minute)
        due_iso = due_datetime.isoformat()

        parsed_task = TaskCreate(
            title=task_title[:100].capitalize(),
            description=f"Created via natural language: \"{clean_text}\"",
            priority=priority,
            status="pending",
            due_date=due_iso,
            duration_minutes=duration_minutes,
            category=category,
            tags=",".join(tags_list)
        )

        explanation = f"Created task '{parsed_task.title}' scheduled for {due_datetime.strftime('%b %d at %I:%M %p')} ({duration_minutes} mins)."
        return True, parsed_task, explanation

    def create_task(self, task: TaskCreate) -> TaskResponse:
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (title, description, priority, status, due_date, duration_minutes, category, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.title,
                task.description or "",
                task.priority or "medium",
                task.status or "pending",
                task.due_date,
                task.duration_minutes or 30,
                task.category or "General",
                task.tags or "",
                now,
                now
            ))
            task_id = cursor.lastrowid
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            return TaskResponse(**dict(row))

    def get_tasks(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[TaskResponse]:
        with get_db() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            if category:
                query += " AND category = ?"
                params.append(category)
            if search:
                query += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
                term = f"%{search}%"
                params.extend([term, term, term])
            
            query += " ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, due_date ASC, id DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [TaskResponse(**dict(r)) for r in rows]

    def update_task(self, task_id: int, updates: TaskUpdate) -> Optional[TaskResponse]:
        now = datetime.now().isoformat()
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            current = cursor.fetchone()
            if not current:
                return None
            
            update_data = updates.model_dump(exclude_unset=True)
            if not update_data:
                return TaskResponse(**dict(current))

            if update_data.get("status") == "completed" and current["status"] != "completed":
                update_data["completed_at"] = now
            elif update_data.get("status") in ["pending", "in_progress"]:
                update_data["completed_at"] = None

            update_data["updated_at"] = now

            set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
            values = list(update_data.values()) + [task_id]
            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
            
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return TaskResponse(**dict(cursor.fetchone()))

    def delete_task(self, task_id: int) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cursor.rowcount > 0

task_service = TaskService()
