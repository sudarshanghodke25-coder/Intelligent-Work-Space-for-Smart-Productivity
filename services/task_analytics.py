from database.database import get_connection
from datetime import datetime

class TaskAnalytics:
    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get total tasks
        total = cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (user_id,)).fetchone()[0]
        completed = cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Completed'", (user_id,)).fetchone()[0]
        
        # Overdue
        today_str = datetime.now().strftime("%Y-%m-%d")
        overdue = cursor.execute(
            "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status != 'Completed' AND due_date < ?",
            (user_id, today_str)
        ).fetchone()[0]
        
        # Completion Rate
        completion_rate = int((completed / total) * 100) if total > 0 else 0
        
        # Productivity Score (basic metric)
        if total == 0:
            score = 0
        else:
            # 100 base, -5 for each overdue, + (completion_rate * 0.5)
            score = 50 + (completion_rate * 0.5) - (overdue * 5)
            score = max(0, min(100, score))
        
        conn.close()
        
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "overdue_tasks": overdue,
            "completion_rate": completion_rate,
            "productivity_score": int(score)
        }

task_analytics = TaskAnalytics()
