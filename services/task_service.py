from database.database import get_connection
from services.event_bus import bus
import json

class TaskService:
    @staticmethod
    def create_task(user_id: int, task_data: dict) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Extract fields with defaults
        title = task_data.get("title", "New Task")
        description = task_data.get("description", "")
        category = task_data.get("category", "Work")
        priority = task_data.get("priority", "Medium")
        due_date = task_data.get("due_date", None)
        due_time = task_data.get("due_time", None)
        reminder = task_data.get("reminder", None)
        repeat_rule = task_data.get("repeat_rule", None)
        project_id = task_data.get("project_id", None)
        ai_generated = task_data.get("ai_generated", 0)
        goal_id = task_data.get("goal_id", None)
        estimated_minutes = task_data.get("estimated_minutes", 0)
        source_type = task_data.get("source_type", "Manual")
        
        cursor.execute('''
            INSERT INTO tasks (
                user_id, title, description, category, priority, 
                due_date, due_time, reminder, repeat_rule, 
                project_id, ai_generated, goal_id, estimated_minutes, source_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, title, description, category, priority, 
            due_date, due_time, reminder, repeat_rule, 
            project_id, ai_generated, goal_id, estimated_minutes, source_type
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Publish event
        bus.publish("TASK_CREATED", {"task_id": task_id, "user_id": user_id, "data": task_data})
        return task_id

    @staticmethod
    def get_task(task_id: int) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        task = cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        conn.close()
        return dict(task) if task else None

    @staticmethod
    def get_tasks(user_id: int, filters: dict = None, limit: int = None, offset: int = None) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM tasks WHERE user_id = ?"
        params = [user_id]
        
        if filters:
            if filters.get("project_id"):
                query += " AND project_id = ?"
                params.append(filters["project_id"])
            if filters.get("status"):
                query += " AND status = ?"
                params.append(filters["status"])
            if filters.get("search"):
                query += " AND (title LIKE ? OR description LIKE ?)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
                
        query += " ORDER BY due_date ASC, priority ASC"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)
        
        tasks = cursor.execute(query, tuple(params)).fetchall()
        conn.close()
        return [dict(t) for t in tasks]

    @staticmethod
    def update_task(task_id: int, user_id: int, update_data: dict):
        if not update_data:
            return
            
        conn = get_connection()
        cursor = conn.cursor()
        
        # Filter valid keys
        valid_keys = [
            "title", "description", "category", "priority", "due_date", 
            "due_time", "reminder", "repeat_rule", "status", "progress", 
            "project_id", "goal_id", "estimated_minutes"
        ]
        
        updates = []
        params = []
        for k, v in update_data.items():
            if k in valid_keys:
                updates.append(f"{k} = ?")
                params.append(v)
                
        if not updates:
            conn.close()
            return
            
        updates.append("updated_at = CURRENT_TIMESTAMP")
        
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
        params.extend([task_id, user_id])
        
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()
        
        # Special event handling for completions
        if update_data.get("status") == "Completed":
            bus.publish("TASK_COMPLETED", {"task_id": task_id, "user_id": user_id})
        else:
            bus.publish("TASK_UPDATED", {"task_id": task_id, "user_id": user_id, "updates": update_data})

    @staticmethod
    def delete_task(task_id: int, user_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        # Ensure it belongs to the user
        cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if deleted:
            bus.publish("TASK_DELETED", {"task_id": task_id, "user_id": user_id})

    # Subtasks
    @staticmethod
    def create_subtask(task_id: int, title: str, sort_order: int = 0) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subtasks (task_id, title, sort_order) VALUES (?, ?, ?)",
            (task_id, title, sort_order)
        )
        sub_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        bus.publish("SUBTASK_ADDED", {"subtask_id": sub_id, "task_id": task_id})
        return sub_id

    @staticmethod
    def get_subtasks(task_id: int) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        subs = cursor.execute("SELECT * FROM subtasks WHERE task_id = ? ORDER BY sort_order ASC", (task_id,)).fetchall()
        conn.close()
        return [dict(s) for s in subs]

    @staticmethod
    def update_subtask(subtask_id: int, update_data: dict):
        if not update_data: return
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        for k, v in update_data.items():
            if k in ["title", "completed", "sort_order"]:
                updates.append(f"{k} = ?")
                params.append(v)
                
        if not updates:
            conn.close()
            return
            
        query = f"UPDATE subtasks SET {', '.join(updates)} WHERE id = ?"
        params.append(subtask_id)
        cursor.execute(query, tuple(params))
        conn.commit()
        
        # Fetch task_id to calculate progress
        task_id_row = cursor.execute("SELECT task_id FROM subtasks WHERE id = ?", (subtask_id,)).fetchone()
        
        if task_id_row:
            task_id = task_id_row["task_id"]
            # Recalculate progress based on subtasks
            total = cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id = ?", (task_id,)).fetchone()[0]
            completed = cursor.execute("SELECT COUNT(*) FROM subtasks WHERE task_id = ? AND completed = 1", (task_id,)).fetchone()[0]
            
            prog = int((completed / total) * 100) if total > 0 else 0
            
            # Auto-complete task if progress is 100%
            new_status = "Completed" if prog == 100 else "Pending"
            cursor.execute("UPDATE tasks SET progress = ?, status = ? WHERE id = ?", (prog, new_status, task_id))
            conn.commit()
            
            if new_status == "Completed":
                # Assuming user_id can be fetched or passed, simplified here. Will need a join ideally.
                user_row = cursor.execute("SELECT user_id FROM tasks WHERE id = ?", (task_id,)).fetchone()
                if user_row:
                    bus.publish("TASK_COMPLETED", {"task_id": task_id, "user_id": user_row["user_id"]})
            else:
                bus.publish("TASK_UPDATED", {"task_id": task_id, "updates": {"progress": prog}})
            
            if update_data.get("completed") is not None:
                bus.publish("SUBTASK_COMPLETED", {"subtask_id": subtask_id, "task_id": task_id})

        conn.close()

task_service = TaskService()
