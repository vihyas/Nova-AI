from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List
from backend.app.models.schemas import ReminderCreate, ReminderResponse
from backend.app.database import get_db

router = APIRouter(prefix="/api/reminders", tags=["reminders"])

@router.get("", response_model=List[ReminderResponse])
def get_reminders():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reminders ORDER BY remind_at ASC")
        return [ReminderResponse(**dict(r)) for r in cursor.fetchall()]

@router.post("", response_model=ReminderResponse)
def create_reminder(reminder: ReminderCreate):
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (title, remind_at, recurrence, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (reminder.title, reminder.remind_at, reminder.recurrence or "none", now))
        reminder_id = cursor.lastrowid
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        return ReminderResponse(**dict(cursor.fetchone()))

@router.put("/{reminder_id}/status")
def update_reminder_status(reminder_id: int, status: str = "dismissed"):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return {"status": "updated", "id": reminder_id, "new_status": status}

@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return {"status": "deleted", "id": reminder_id}

