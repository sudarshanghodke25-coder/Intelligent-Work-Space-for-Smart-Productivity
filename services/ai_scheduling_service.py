import os
import json
import uuid
from datetime import datetime, date, timedelta
from database.database import get_connection
from services.event_bus import bus
from services.api_service import aurex_api

class AISchedulingService:
    def __init__(self):
        pass

    def _get_context(self) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Fetch Open Tasks
        tasks = cursor.execute("SELECT id, title, priority, due_date, estimated_minutes, category FROM tasks WHERE status != 'Completed'").fetchall()
        
        # 2. Fetch Active Goals
        goals = cursor.execute("SELECT id, title, status FROM goals WHERE status != 'Completed'").fetchall()
        
        # 3. Fetch Existing Events (to avoid conflicts)
        # Fetching for the next 7 days for context
        today = datetime.now()
        end_date = today + timedelta(days=7)
        
        # Support both old event_date and new start_time
        events_query = """
            SELECT id, title, start_time, end_time, event_date, event_time, event_type
            FROM events
            WHERE (start_time >= ? AND start_time <= ?) OR (event_date >= ? AND event_date <= ?)
        """
        today_str = today.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        events = cursor.execute(events_query, (today, end_date, today_str, end_date_str)).fetchall()
        
        conn.close()
        
        return {
            "tasks": [dict(t) for t in tasks],
            "goals": [dict(g) for g in goals],
            "existing_events": [dict(e) for e in events]
        }

    def generate_schedule(self, prompt: str, priority_mode: str = "Balanced", focus_duration: str = "50 min", density: str = "Medium") -> dict:
        if not aurex_api.client:
            raise Exception("A valid AI Provider API key is missing. Cannot generate schedule.")
                
        context = self._get_context()
        
        system_prompt = f"""You are an expert AI productivity assistant. Your task is to generate a highly optimized schedule for the user.
You must return a raw JSON object matching the exact schema below. Do not include markdown formatting like ```json.

Schema:
{{
  "schedule_name": "Name of the generated schedule (e.g., Weekly Exam Plan)",
  "blocks": [
    {{
      "title": "Block Title",
      "type": "event|task|focus|deadline|goal",
      "priority": "High|Medium|Low",
      "start_time": "YYYY-MM-DD HH:MM:00",
      "end_time": "YYYY-MM-DD HH:MM:00",
      "notes": "Brief notes or instructions"
    }}
  ]
}}

Current Context:
- Current Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Priority Mode: {priority_mode}
- Preferred Focus Duration: {focus_duration}
- Schedule Density: {density}

Open Tasks: {json.dumps(context['tasks'])}
Active Goals: {json.dumps(context['goals'])}
Existing Events (Avoid Conflicts): {json.dumps(context['existing_events'], default=str)}

Instructions:
1. Parse the user's prompt carefully to understand their goal (e.g., 'Study DBMS for 2 hours daily').
2. Allocate blocks using the available open tasks and goals where relevant.
3. Ensure no overlapping times with 'Existing Events'.
4. Ensure start_time and end_time are valid future dates formatted as 'YYYY-MM-DD HH:MM:00'.
5. ONLY return the JSON object.
"""

        try:
            response = aurex_api.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            raw_json = response.choices[0].message.content.strip()
            schedule_data = json.loads(raw_json)
            
            # Save to database
            schedule_group_id = str(uuid.uuid4())
            self._save_schedule(schedule_data, schedule_group_id, prompt)
            
            return schedule_data
            
        except Exception as e:
            print(f"[AISchedulingService] Error generating schedule: {e}")
            raise

    def _save_schedule(self, schedule_data: dict, group_id: str, prompt: str):
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Save to History
        schedule_name = schedule_data.get("schedule_name", "AI Schedule")
        cursor.execute(
            "INSERT INTO schedule_history (schedule_group_id, schedule_name, prompt) VALUES (?, ?, ?)",
            (group_id, schedule_name, prompt)
        )
        
        # 2. Insert blocks as events
        blocks = schedule_data.get("blocks", [])
        for block in blocks:
            start_time_str = block.get("start_time")
            end_time_str = block.get("end_time")
            
            # Basic parsing to extract date and time for fallback columns
            try:
                st = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                event_date = st.strftime('%Y-%m-%d')
                event_time = st.strftime('%H:%M')
            except:
                event_date = datetime.now().strftime('%Y-%m-%d')
                event_time = "12:00"

            cursor.execute('''
                INSERT INTO events (
                    title, description, event_date, event_time, 
                    start_time, end_time, event_type, priority, category, 
                    ai_generated, schedule_group_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 'Scheduled')
            ''', (
                block.get("title", "AI Block"),
                block.get("notes", ""),
                event_date,
                event_time,
                start_time_str,
                end_time_str,
                block.get("type", "event").lower(),
                block.get("priority", "Medium"),
                block.get("category", "AI Planned"),
                group_id
            ))
            
        conn.commit()
        conn.close()
        
        # Notify UI
        bus.publish("EVENTS_UPDATED", {"action": "ai_schedule_generated", "group_id": group_id})

    def get_schedule_history(self):
        conn = get_connection()
        cursor = conn.cursor()
        history = cursor.execute("SELECT * FROM schedule_history ORDER BY created_at DESC LIMIT 20").fetchall()
        conn.close()
        return [dict(h) for h in history]
        
    def clear_schedule_group(self, group_id: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE schedule_group_id = ?", (group_id,))
        cursor.execute("DELETE FROM schedule_history WHERE schedule_group_id = ?", (group_id,))
        conn.commit()
        conn.close()
        bus.publish("EVENTS_UPDATED", {"action": "ai_schedule_cleared", "group_id": group_id})

ai_scheduling_service = AISchedulingService()
