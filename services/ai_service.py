import json
import webbrowser
import urllib.parse
from dotenv import load_dotenv
from services.event_bus import bus
from database.database import get_connection
from services.api_service import aurex_api

load_dotenv()

class AIService:
    def __init__(self):
        pass

    def process_message(self, session_id, user_id, user_input):
        """
        Main entry point for AI command router and response generation.
        Runs in background thread.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Save user message
        cursor.execute('''INSERT INTO chat_messages (session_id, role, message) 
                          VALUES (?, 'user', ?)''', (session_id, user_input))
        
        # Check if this is the first message to determine if we need to auto-title
        cursor.execute("SELECT COUNT(*) as count FROM chat_messages WHERE session_id=?", (session_id,))
        msg_count = cursor.fetchone()["count"]
        
        # Update session updated_at
        cursor.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id=?", (session_id,))
        conn.commit()

        # Route Command
        intent_data = self._classify_intent(user_input)
        intent = intent_data.get("intent", "ai_chat")
        target = intent_data.get("target", "")

        # Auto-title from first message without an extra API call
        if msg_count == 1:
            new_title = user_input.strip()
            if len(new_title) > 40:
                new_title = new_title[:37] + "..."
            cursor.execute("UPDATE chat_sessions SET title = ? WHERE session_id=?", (new_title, session_id))
            conn.commit()
            bus.publish("HISTORY_UPDATED", {})

        # Handle the intent
        if intent != "ai_chat":
            response_text = self._execute_intent(intent, target, user_input)
        else:
            # AI Chat Generation
            cursor.execute("SELECT role, message FROM chat_messages WHERE session_id=? ORDER BY timestamp DESC LIMIT 12", (session_id,))
            history_rows = list(reversed(cursor.fetchall()))
            
            messages = [{"role": "system", "content": "You are FLOWSPACE AI, a futuristic AI workspace assistant. You must provide high-level, extremely concise, and fast responses. When asked to generate content, prioritize high-level summaries and avoid long-winded explanations to ensure the fastest possible output."}]
            for row in history_rows:
                messages.append({"role": row["role"], "content": row["message"]})

            try:
                completion = aurex_api.chat_completions_create(
                    messages=messages,
                    max_tokens=512,
                    temperature=0.5,
                )
                response_text = completion.choices[0].message.content
            except Exception as e:
                response_text = f"Transmission Error:\n{str(e)}"

        # Save AI Response
        cursor.execute('''INSERT INTO chat_messages (session_id, role, message) 
                          VALUES (?, 'assistant', ?)''', (session_id, response_text))
        cursor.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id=?", (session_id,))
        conn.commit()
        conn.close()

        bus.publish("AI_RESPONSE_RECEIVED", {"text": response_text, "session_id": session_id})

    def generate_conversation_title(self, user_input):
        """
        Helper method to generate a short, descriptive title for a conversation.
        """
        prompt = f"""Generate a concise title (maximum 4 words) for this conversation starter.
Do not use quotes or punctuation. Just return the title.

Message: "{user_input}"
"""
        try:
            completion = aurex_api.chat_completions_create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            title = completion.choices[0].message.content.strip().replace('"', '').replace("'", "")
            return title
        except:
            return "New Conversation"

    def _classify_intent(self, text):
        """Lightweight intent router using the unified AI router."""
        lower_text = text.lower()
        if not ("open " in lower_text or "search " in lower_text or "navigate " in lower_text):
            return {"intent": "ai_chat", "target": ""}
            
        prompt = f"""Classify the user intent into exactly one of these: 
[navigation, web_search, ai_chat].

RULES:
1. ONLY return 'navigation' if the user explicitly says "open [app]" (e.g. "Open Notes", "Open Calendar").
2. ONLY return 'web_search' if the user explicitly says "open [website]" or "search [website] for" (e.g. "Open YouTube", "Search Google for Python").
3. EVERYTHING ELSE is 'ai_chat'. For example: "What is Python language?", "Teach me recursion" MUST be 'ai_chat'. Do NOT open the browser for questions.
4. If uncertain, ALWAYS default to 'ai_chat'.

Extract 'target' if applicable (e.g. the app or website name).
Return ONLY valid JSON with keys "intent" and "target".

Text: "{text}"
"""
        try:
            completion = aurex_api.chat_completions_create(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except:
            return {"intent": "ai_chat", "target": ""}

    def _execute_intent(self, intent, target, original_text):
        if intent == "navigation":
            page_map = {
                "youtube": "web_search",
                "google": "web_search",
                "notes": "Notes & Docs",
                "calendar": "Calendar",
                "tasks": "Task Manager",
                "analytics": "Analytics",
                "focus": "Focus Mode",
                "goals": "Goal Tracker",
                "settings": "Settings",
                "dashboard": "Dashboard"
            }
            target_lower = target.lower() if target else ""
            orig_lower = original_text.lower()
            
            if target_lower in ["youtube", "google"] or "youtube" in orig_lower or "google" in orig_lower:
                return self._execute_intent("web_search", target_lower or original_text, original_text)
                
            page = "Dashboard"
            for k, v in page_map.items():
                if k in target_lower or k in orig_lower:
                    page = v
                    break
            
            bus.publish("NAVIGATE_TO", page)
            return f"Navigating to {page}..."

        elif intent == "web_search":
            query_text = target or original_text
            # Try to strip out "search youtube for" etc.
            lower_text = query_text.lower()
            for prefix in ["search youtube for", "search google for", "search for", "open youtube", "open google"]:
                if lower_text.startswith(prefix):
                    query_text = query_text[len(prefix):].strip()
            
            query = urllib.parse.quote_plus(query_text)
            
            if "youtube" in original_text.lower():
                webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
                return "Opening YouTube in your browser."
            else:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return "Opening Google in your browser."

        return "Intent recognized, but not explicitly handled."

    def generate_roadmap(self, goal, plan_type):
        """
        Generates structured AI Roadmap JSON.
        Must be invoked from a background thread.
        """
        import json
        
        system_prompt = f"""You are an elite AI Strategist and Planner.
Your task is to generate a structured, actionable roadmap for the user.

Plan Type: {plan_type}
Goal: {goal}

Return ONLY a strict JSON object with EXACTLY these keys:
- "title": (string) A short, inspiring title for the roadmap.
- "description": (string) A 2-3 sentence overview of the plan.
- "timeline": (array of strings) High-level timeline phases (e.g., ["Phase 1: Basics", "Phase 2: Intermediate"]).
- "steps": (array of objects) Actionable steps. Each object must have "title" (string), "duration" (string), and "details" (string).
- "resources": (array of objects) Curated learning resources. Each object must have "title", "type", and "search_query".
- "difficulty": (string) E.g., "Beginner", "Intermediate", "Advanced".
- "daily_time": (string) E.g., "1-2 hours/day".
- "duration": (string) E.g., "30 Days", "3 Months".
- "success_probability": (string) E.g., "High", "Medium", based on typical completion rates.
- "prerequisites": (array of strings) Skills or tools needed before starting.
- "tips": (array of strings) AI-generated strategic guidance and execution advice. This will be shown as the FLOWSPACE Recommendation.
- "common_mistakes": (array of strings) Mistakes users commonly make.
- "recommended_tools": (array of objects) Objects with "title" (string) and "url" (string, a guess at the official url).
- "success_metrics": (array of strings) Measurable completion criteria.

Output ONLY valid JSON.
"""
        try:
            completion = aurex_api.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Build a {plan_type} roadmap for: {goal}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=2048,
                temperature=0.6,
            )
            response_text = completion.choices[0].message.content
            parsed_data = json.loads(response_text)
            bus.publish("ROADMAP_GENERATED", {"success": True, "data": parsed_data, "goal": goal, "plan_type": plan_type})
        except Exception as e:
            bus.publish("ROADMAP_GENERATED", {"success": False, "error": str(e)})

    def analyze_document_background(self, doc_id, raw_text):
        """
        Analyzes a document's text and returns a summary and key points in JSON format.
        Must be invoked from a background thread.
        """
        import json
        
        words = raw_text.split()
        if len(words) > 6000:
            raw_text = " ".join(words[:6000]) + "\n\n...[TRUNCATED]"
            
        system_prompt = """You are a professional document analyst. 
Read the provided document text and return a strict JSON object with EXACTLY two keys:
1. "summary": A concise, 3-sentence executive overview of the document.
2. "key_points": A formatted string of bullet points extracting the most critical data and insights. Use standard dash (-) bullet points.

Output ONLY valid JSON.
"""
        try:
            completion = aurex_api.chat_completions_create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            parsed_data = json.loads(response_text)
            
            bus.publish("DOC_ANALYZED", {
                "doc_id": doc_id,
                "summary": parsed_data.get("summary", "No summary generated."),
                "key_points": parsed_data.get("key_points", "No key points extracted.")
            })
        except Exception as e:
            bus.publish("DOC_ANALYZED", {
                "doc_id": doc_id,
                "error": str(e)
            })

    def parse_smart_task(self, text, current_time):
        """Parses natural language task capture into structured JSON."""
        system_prompt = f"""You are a smart task parser.
Current time: {current_time}
Extract task details from the user's input.
Return ONLY valid JSON with EXACTLY these keys:
- "title": (string) Cleaned task title.
- "due_date": (string) Format 'YYYY-MM-DD HH:MM'. If no time, use '23:59'. If no date, leave empty string.
- "priority": (string) 'High', 'Medium', or 'Low'. Default 'Medium'.
- "category": (string) e.g., 'Work', 'Study', 'Personal', 'Project'. Default 'Work'.
- "estimated_time": (integer) Estimated minutes to complete. Default 30.
"""
        try:
            completion = aurex_api.chat_completions_create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
                response_format={"type": "json_object"}
            )
            parsed = json.loads(completion.choices[0].message.content)
            bus.publish("SMART_TASK_PARSED", {"success": True, "data": parsed})
        except Exception as e:
            bus.publish("SMART_TASK_PARSED", {"success": False, "error": str(e)})

    def generate_subtasks(self, task_title, task_id):
        """Generates actionable subtasks for a high-level task."""
        system_prompt = """You are a productivity expert. Break down the given task into 3-5 concrete, actionable subtasks.
Return ONLY valid JSON with EXACTLY this structure:
{"subtasks": ["subtask 1", "subtask 2", "subtask 3"]}
"""
        try:
            completion = aurex_api.chat_completions_create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Task: {task_title}"}],
                response_format={"type": "json_object"}
            )
            parsed = json.loads(completion.choices[0].message.content)
            bus.publish("SUBTASKS_GENERATED", {"success": True, "task_id": task_id, "subtasks": parsed.get("subtasks", [])})
        except Exception as e:
            bus.publish("SUBTASKS_GENERATED", {"success": False, "task_id": task_id, "error": str(e)})

    def generate_task_intelligence(self, task_title, priority, due_date, task_id):
        """Generates AI insights for a specific task."""
        system_prompt = """You are an AI Task Strategist.
Analyze the task and provide execution insights.
Return ONLY valid JSON with EXACTLY these keys:
- "risk_level": (string) 'Low', 'Medium', or 'High'.
- "suggested_next_action": (string) The very first physical step to take.
- "focus_recommendation": (string) Suggested focus session length and approach.
- "productivity_insight": (string) A psychological or strategic tip for this specific task.
"""
        try:
            user_msg = f"Task: {task_title}\nPriority: {priority}\nDue: {due_date}"
            completion = aurex_api.chat_completions_create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_msg}],
                response_format={"type": "json_object"}
            )
            parsed = json.loads(completion.choices[0].message.content)
            bus.publish("TASK_INTELLIGENCE_GENERATED", {"success": True, "task_id": task_id, "insights": parsed})
        except Exception as e:
            bus.publish("TASK_INTELLIGENCE_GENERATED", {"success": False, "task_id": task_id, "error": str(e)})

# Singleton instance
ai_service = AIService()
