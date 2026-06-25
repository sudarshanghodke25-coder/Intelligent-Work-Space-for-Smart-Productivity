import re
from datetime import datetime, timedelta
from services.ai_service import ai_service
from services.task_service import task_service

class TaskParser:
    @staticmethod
    def parse_and_create(user_id: int, text: str) -> dict:
        """
        Two-stage parsing system:
        Stage 1: Fast local regex parser
        Stage 2: Aurex AI fallback if confidence is low
        """
        parsed_data, confidence = TaskParser._local_parse(text)
        
        if confidence < 0.7:
            # Stage 2: AI Fallback
            ai_data = TaskParser._ai_parse(text)
            if ai_data:
                parsed_data.update(ai_data)
                parsed_data["ai_generated"] = 1
        
        # Default fallbacks
        if "title" not in parsed_data or not parsed_data["title"]:
            parsed_data["title"] = text
            
        task_id = task_service.create_task(user_id, parsed_data)
        parsed_data["id"] = task_id
        return parsed_data

    @staticmethod
    def _local_parse(text: str) -> tuple[dict, float]:
        data = {}
        confidence = 0.0
        
        text_lower = text.lower()
        
        # Match "tomorrow"
        if "tomorrow" in text_lower:
            data["due_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            confidence += 0.4
            text = re.sub(r'(?i)\btomorrow\b', '', text)
            
        # Match "today"
        elif "today" in text_lower:
            data["due_date"] = datetime.now().strftime("%Y-%m-%d")
            confidence += 0.4
            text = re.sub(r'(?i)\btoday\b', '', text)
            
        # Match time "at 8 PM" or "at 14:00"
        time_match = re.search(r'(?i)at (\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)', text)
        if time_match:
            data["due_time"] = time_match.group(1).strip()
            confidence += 0.3
            text = text.replace(time_match.group(0), "")
            
        # Match priority "high priority" or "!high"
        if "high priority" in text_lower or "!high" in text_lower:
            data["priority"] = "High"
            confidence += 0.2
            text = re.sub(r'(?i)high priority|!high', '', text)
        elif "low priority" in text_lower or "!low" in text_lower:
            data["priority"] = "Low"
            confidence += 0.2
            text = re.sub(r'(?i)low priority|!low', '', text)
            
        # Clean up title
        title = " ".join(text.split()).strip()
        if title:
            data["title"] = title
            confidence += 0.2
            
        return data, min(confidence, 1.0)

    @staticmethod
    def _ai_parse(text: str) -> dict:
        prompt = f"""
        Extract task details from this text and return ONLY valid JSON: "{text}"
        Keys needed: title (string), due_date (YYYY-MM-DD or null), due_time (HH:MM AM/PM or null), priority (High, Medium, Low).
        """
        response = ai_service.generate_json(prompt)
        # Assuming ai_service returns a dict if valid JSON is found
        if isinstance(response, dict):
            return response
        return {}

task_parser = TaskParser()
