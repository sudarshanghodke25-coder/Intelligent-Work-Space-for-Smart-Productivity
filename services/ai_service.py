import os
from groq import Groq
from services.event_bus import bus

class GroqService:
    def __init__(self):
        # Using the provided key snippet or falling back to environment variables
        api_key = os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        
    def generate_response(self, conversation_history):
        """
        Executes a Groq chat completion request.
        Must be invoked from a background thread to prevent UI locking.
        
        Args:
            conversation_history (list): A list of dicts [{"role": "user", "content": "..."}]
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=conversation_history
            )
            response_text = completion.choices[0].message.content
        except Exception as e:
            response_text = f"Transmission Error: {str(e)}"
            
        # Safely broadcast to the main thread EventBus
        bus.publish("AI_RESPONSE_RECEIVED", {"text": response_text})

    def parse_schedule_intent(self, user_input, current_time):
        """
        Parses a natural language scheduling request into JSON.
        Must be invoked from a background thread.
        """
        import json
        
        system_prompt = f"""You are a strict JSON extraction engine.
Extract scheduling details from the user's input.
The current time is: {current_time}

Extract exactly these four keys:
- "event_name": (string) The title of the event.
- "start_time": (string) Formatted exactly as YYYY-MM-DD HH:MM
- "end_time": (string) Formatted exactly as YYYY-MM-DD HH:MM
- "category": (string) Must be exactly one of: Work, Meeting, Personal, Break. Guess if unspecified.

Output ONLY valid JSON.
"""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            parsed_data = json.loads(response_text)
            bus.publish("NLP_SCHEDULE_PARSED", {"success": True, "data": parsed_data})
        except Exception as e:
            bus.publish("NLP_SCHEDULE_PARSED", {"success": False, "error": str(e)})

    def analyze_document_background(self, doc_id, raw_text):
        """
        Analyzes a document's text and returns a summary and key points in JSON format.
        Must be invoked from a background thread.
        """
        import json
        
        # Truncate text to fit into Llama-3 8k/32k token window safely (~6000 words limit here)
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
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            parsed_data = json.loads(response_text)
            
            # Safely publish event with the payload
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

# Singleton instance
ai_service = GroqService()
