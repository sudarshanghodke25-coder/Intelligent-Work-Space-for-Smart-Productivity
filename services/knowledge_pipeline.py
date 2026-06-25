import threading
import json
import os
import time
from services.event_bus import bus
from services.knowledge_parser import knowledge_parser
from services.knowledge_service import knowledge_service
from services.media.orchestrator import media_orchestrator
from services.media.cancellation import cancellation_manager
from services.embeddings.embedding_service import embedding_service
from services.api_service import aurex_api

class KnowledgePipeline:
    def __init__(self):
        pass

    def _safe_run_pipeline(self, *args, **kwargs):
        """Top-level wrapper so unhandled exceptions in the background thread are always printed."""
        try:
            self._run_pipeline(*args, **kwargs)
        except Exception:
            import traceback
            print("[CRITICAL] Unhandled exception in _run_pipeline thread:")
            traceback.print_exc()

    def process_file_background(self, file_path: str, title: str, original_filename: str, source_type: str, project: str = "General", category: str = "Uncategorized"):
        print(f"\n[VALIDATION] PASS - Starting processing for file: {original_filename}\n")
        thread = threading.Thread(target=self._safe_run_pipeline, args=(file_path, None, title, original_filename, source_type, project, category), daemon=True)
        thread.start()

    def process_url_background(self, url: str, title: str, source_type: str, project: str = "General", category: str = "Uncategorized"):
        print(f"\n[VALIDATION] PASS - Starting processing for URL: {url}\n")
        thread = threading.Thread(target=self._safe_run_pipeline, args=(None, url, title, url, source_type, project, category), daemon=True)
        thread.start()

    def _run_pipeline(self, file_path: str, url: str, title: str, original_filename: str, source_type: str, project: str = "General", category: str = "Uncategorized"):
        current_stage = "VALIDATION"
        source_id = None
        try:
            # --- AUTO-CORRECT SOURCE TYPE ---
            if url and source_type == "website" and ("youtube.com" in url or "youtu.be" in url):
                print("[DEBUG] Auto-correcting source_type from 'website' to 'youtube'")
                source_type = "youtube"
                
            # 1. Store initial empty record
            file_size = os.path.getsize(file_path) if file_path and os.path.exists(file_path) else 0
            source_id = knowledge_service.create_source(
                source_type=source_type,
                title=title,
                original_filename=original_filename,
                source_path=file_path,
                url=url,
                size=file_size,
                project=project,
                category=category
            )
            
            bus.publish("ANALYSIS_STARTED", {"source_id": source_id, "title": title})
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Validating...", "progress": 10})

            cancellation_manager.register(source_id)

            # 2. Extract Text & Metadata
            current_stage = "EXTRACTION"
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Extracting Content...", "progress": 20})
            print(f"[EXTRACTION]\nStarting...")
            
            start_time = time.time()
            source = url if url else file_path
            
            raw_text = ""
            try:
                # Try Media Orchestrator First (YouTube, Local Media, Podcasts, etc)
                print(f"[EXTRACTION] Trying Media Orchestrator for {source}")
                media_data = media_orchestrator.process(source, source_id)
                raw_text = media_data.get("transcript", "")
                
                title = media_data.get("title", title)
                knowledge_service.update_source_metadata(source_id, {
                    "video_id": media_data.get("video_id"),
                    "channel": media_data.get("channel"),
                    "extraction_method": media_data.get("extraction_method"),
                    "title": title
                })
            except ValueError:
                # Not a media plugin, fallback to standard document parsing
                print("[EXTRACTION] Not a media source, falling back to standard document parsing.")
                if file_path:
                    ext = os.path.splitext(file_path)[1].lower().strip('.')
                    raw_text = knowledge_parser.extract_text(file_path, ext)
                elif url:
                    raw_text = knowledge_parser.extract_from_url(url, source_type)
            
            cancellation_manager.check_cancelled(source_id)
            
            if not raw_text or raw_text.startswith("[Extraction Error"):
                error_msg = raw_text if raw_text else "No extractable text found."
                knowledge_service.update_source_metadata(source_id, {"raw_content": error_msg, "status": "FAILED"})
                bus.publish("ANALYSIS_COMPLETED", {"source_id": source_id, "success": False, "error": error_msg})
                return
                
            # Title Extraction for URLs (fallback)
            if url and source_type != "youtube" and title == url:
                try:
                    import requests
                    from bs4 import BeautifulSoup
                    r = requests.get(url, timeout=5)
                    s = BeautifulSoup(r.text, 'html.parser')
                    if s.title and s.title.string:
                        title = s.title.string.strip()
                        knowledge_service.update_source_metadata(source_id, {"title": title})
                except Exception:
                    pass

            # Update with raw text first
            transcript_length = len(raw_text)
            knowledge_service.update_source_metadata(source_id, {
                "raw_content": raw_text, 
                "transcript": raw_text, # Always populate transcript just in case
                "transcript_length": transcript_length,
                "status": "PROCESSING"
            })
            
            # --- HARD FAIL VALIDATIONS ---
            print("================= TRACE LOGS =================")
            print(f"[DEBUG] Transcript Length: {transcript_length}")
            print(f"[DEBUG] Transcript Preview: {raw_text[:300]}")
            
            if transcript_length < 100:
                raise Exception("HARD FAIL: Insufficient transcript data (<100 chars). Aborting analysis.")
                
            # Check for YouTube generic metadata (HTML scrape leak)
            generic_keywords = ["About Press Copyright Contact us Creators", "Terms Privacy Policy & Safety"]
            if any(k in raw_text for k in generic_keywords) and transcript_length < 5000:
                raise Exception("HARD FAIL: Extracted content is YouTube website HTML/metadata, not video transcript. Aborting analysis.")
            # -----------------------------
            
            # --- CACHING CHECK (Phase 3) ---
            import hashlib
            from database.database import get_connection
            content_hash = hashlib.sha256(raw_text.encode("utf-8", errors="ignore")).hexdigest()
            
            conn = get_connection()
            cached = conn.cursor().execute(
                "SELECT * FROM knowledge_sources WHERE content_hash = ? AND status = 'COMPLETED' AND id != ? LIMIT 1",
                (content_hash, source_id)
            ).fetchone()
            conn.close()
            
            if cached:
                print(f"[CACHE HIT] Exact content match found. Copying from source {cached['id']}")
                bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Loading from Cache...", "progress": 90})
                
                cached_dict = dict(cached)
                knowledge_service.update_source_metadata(source_id, {
                    "summary": cached_dict.get("summary"),
                    "key_points": cached_dict.get("key_points"),
                    "important_concepts": cached_dict.get("important_concepts"),
                    "suggested_questions": cached_dict.get("suggested_questions"),
                    "knowledge_tags": cached_dict.get("knowledge_tags"),
                    "quotes": cached_dict.get("quotes"),
                    "chapters": cached_dict.get("chapters"),
                    "people_mentioned": cached_dict.get("people_mentioned"),
                    "companies_mentioned": cached_dict.get("companies_mentioned"),
                    "action_items": cached_dict.get("action_items"),
                    "topics": cached_dict.get("topics"),
                    "raw_response": cached_dict.get("raw_response"),
                    "status": "COMPLETED",
                    "content_hash": content_hash,
                    "processing_time": 0.0
                })
                
                # Copy chunks and embeddings
                chunks_data = embedding_service.store.get_embeddings_by_source(cached_dict['id'])
                if chunks_data:
                    # Convert to list of dicts that save_chunks expects
                    formatted_chunks = [{"text": c["content"], "embedding_json": json.dumps(c["embedding"]) if c["embedding"] else None} for c in chunks_data]
                    knowledge_service.save_chunks(source_id, formatted_chunks)

                bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Completed", "progress": 100})
                bus.publish("ANALYSIS_COMPLETED", {"source_id": source_id, "success": True})
                return
            # -----------------------------

            # 3. Chunk Content & Generate Embeddings
            current_stage = "CHUNKING"
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Chunking & Generating Embeddings...", "progress": 40})
            words = raw_text.split()
            
            if len(words) < 2000:
                raw_chunks = [raw_text]
                print(f"[DEBUG] Document is small ({len(words)} words). Processing as single chunk.")
            else:
                chunk_size = 2000
                raw_chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
            
            print(f"[DEBUG] Chunk Count: {len(raw_chunks)}")
            
            t_emb_start = time.time()
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Generating Embeddings...", "progress": 45})
            emb_batch = embedding_service.generate_embeddings_batch(raw_chunks)
            emb_elapsed = time.time() - t_emb_start
            print(f"[PERF] Embeddings: {emb_elapsed:.2f}s")
            
            embedded_chunks = []
            for idx, c_text in enumerate(raw_chunks):
                emb = emb_batch[idx] if idx < len(emb_batch) else []
                embedded_chunks.append({
                    "text": c_text,
                    "embedding_json": json.dumps(emb) if emb else None
                })
                
            # Save chunks to DB
            knowledge_service.save_chunks(source_id, embedded_chunks)
            chunks = raw_chunks # Pass strings to Groq

            # 4. Groq/API Analysis (Map-Reduce)
            current_stage = "API_ANALYSIS"
            if not aurex_api.client:
                raise Exception("A valid AI Provider API key is missing.")
                
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Analyzing Content...", "progress": 50})
            
            system_prompt = """You MUST return ONLY valid JSON.
Do not use markdown.
Return EXACTLY this schema:
{
  "summary": "Detailed summary of the media",
  "key_points": ["point 1", "point 2"],
  "simple_explanation": "Explain like I'm 5",
  "important_concepts": ["concept 1"],
  "suggested_questions": ["question 1"],
  "chapters": ["00:00 - Intro", "05:00 - Middle"],
  "keywords": ["keyword1"],
  "action_items": ["action 1"],
  "people_mentioned": ["Person A"],
  "companies_mentioned": ["Company A"],
  "topics": ["Topic A"],
  "quotes": ["Important Quote 1"]
}"""

            import concurrent.futures

            def process_chunk(idx, chunk):
                cancellation_manager.check_cancelled(source_id)
                if len(chunk.strip()) < 10:
                    raise Exception("HARD FAIL: GROQ input does not contain meaningful transcript data.")
                try:
                    completion = aurex_api.chat_completions_create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"DOCUMENT CONTENT:\n{chunk}"}
                        ]
                    )
                    return idx, completion.choices[0].message.content
                except Exception as e:
                    print(f"Groq API Error on chunk {idx}: {e}")
                    return idx, None

            chunk_summaries = [None] * len(chunks)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(process_chunk, i, chunk): i for i, chunk in enumerate(chunks)}
                completed_count = 0
                for future in concurrent.futures.as_completed(futures):
                    i = futures[future]
                    completed_count += 1
                    progress_pct = 50 + int((completed_count / len(chunks)) * 30)
                    bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": f"Analyzing Chunk {completed_count}/{len(chunks)}...", "progress": progress_pct})
                    
                    try:
                        idx, resp = future.result()
                        if resp:
                            chunk_summaries[idx] = resp
                    except Exception as e:
                        print(f"Chunk processing error: {e}")
            
            chunk_summaries = [s for s in chunk_summaries if s is not None]

            # Reduce Phase
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Generating Summary...", "progress": 85})
            if len(chunk_summaries) > 1:
                reduce_prompt = "Merge the following JSON summaries into a single comprehensive JSON object matching the exact schema provided in the system prompt."
                combined_text = "\n\n".join(chunk_summaries)
                try:
                    completion = aurex_api.chat_completions_create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"{reduce_prompt}\n\nSUMMARIES:\n{combined_text[:20000]}"}
                        ]
                    )
                    final_response_text = completion.choices[0].message.content
                except Exception as e:
                    final_response_text = chunk_summaries[0]
            else:
                final_response_text = chunk_summaries[0] if chunk_summaries else "{}"

            # 5. Parse and Update
            cleaned_response = final_response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            try:
                ai_data = json.loads(cleaned_response)
            except Exception as e:
                ai_data = {"summary": final_response_text}
                
            def list_to_str(val):
                if isinstance(val, list):
                    return "\n".join([f"• {item}" for item in val])
                return str(val) if val else ""

            summary = str(ai_data.get("summary", "")) or str(ai_data.get("simple_explanation", ""))
            key_points = list_to_str(ai_data.get("key_points", ""))
            important_concepts = list_to_str(ai_data.get("important_concepts", ""))
            suggested_questions = list_to_str(ai_data.get("suggested_questions", ""))
            knowledge_tags = ",".join(ai_data.get("keywords", []) + ai_data.get("topics", []))
            
            quotes = list_to_str(ai_data.get("quotes", ""))
            chapters = list_to_str(ai_data.get("chapters", ""))
            people_mentioned = list_to_str(ai_data.get("people_mentioned", ""))
            companies_mentioned = list_to_str(ai_data.get("companies_mentioned", ""))
            action_items = list_to_str(ai_data.get("action_items", ""))
            topics = list_to_str(ai_data.get("topics", ""))
            
            print(f"[DEBUG] Stored Summary: {summary[:300]}...")
            
            processing_time = time.time() - start_time

            update_data = {
                "summary": summary,
                "key_points": key_points,
                "important_concepts": important_concepts,
                "suggested_questions": suggested_questions,
                "knowledge_tags": knowledge_tags,
                "raw_response": final_response_text,
                "processing_time": processing_time,
                "status": "COMPLETED",
                "quotes": quotes,
                "chapters": chapters,
                "people_mentioned": people_mentioned,
                "companies_mentioned": companies_mentioned,
                "action_items": action_items,
                "topics": topics,
                "content_hash": content_hash
            }
            
            t_db = time.time()
            current_stage = "DATABASE"
            print("[STEP] Before ANALYSIS_PROGRESS (Saving Results) publish")
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Saving Results...", "progress": 95})
            print("[STEP] After ANALYSIS_PROGRESS publish")
            
            print("[STEP] Before database save (update_source_metadata)")
            knowledge_service.update_source_metadata(source_id, update_data)
            print("[STEP] After database save")
            
            # 6. UI Refresh
            current_stage = "UI"
            print("[STEP] Before ANALYSIS_PROGRESS (Completed) publish")
            bus.publish("ANALYSIS_PROGRESS", {"source_id": source_id, "status": "Completed", "progress": 100})
            print("[STEP] After ANALYSIS_PROGRESS (Completed) publish")
            
            print("[STEP] Before ANALYSIS_COMPLETED publish")
            bus.publish("ANALYSIS_COMPLETED", {"source_id": source_id, "success": True})
            print("[STEP] After ANALYSIS_COMPLETED publish -- pipeline thread finished cleanly")

        except Exception as e:
            err_msg = f"Stage:\n{current_stage}\n\n{str(e)}"
            print(f"Knowledge Pipeline Error: {err_msg}")
            if source_id is not None:
                knowledge_service.update_source_metadata(source_id, {"status": "FAILED", "raw_content": err_msg})
                bus.publish("ANALYSIS_COMPLETED", {"source_id": source_id, "success": False, "error": err_msg})
        finally:
            if source_id is not None:
                cancellation_manager.unregister(source_id)

    def ask_source_background(self, source_id: int, question: str):
        print(f"[VALIDATION] Starting Ask AI for source {source_id}")
        thread = threading.Thread(target=self._run_rag_query, args=(source_id, question), daemon=True)
        thread.start()

    def _run_rag_query(self, source_id: int, question: str):
        try:
            if not aurex_api.client:
                raise Exception("AI API key not found.")
                
            print(f"[EXTRACTION] Retrieving chunks and embeddings for source {source_id}")
            chunk_dicts = embedding_service.store.get_embeddings_by_source(source_id)
            if not chunk_dicts:
                raise Exception("Source has no extracted text or chunks.")
                
            print("[CHUNKING] Generating embedding for question...")
            q_emb = embedding_service.generate_embedding(question)
            
            print("[CHUNKING] Scoring and selecting top chunks (Vector Search)...")
            q_words = set(question.lower().split())
            scored_chunks = []
            
            import math
            for chunk_dict in chunk_dicts:
                emb = chunk_dict['embedding']
                chunk_text = chunk_dict['content']
                if emb and q_emb:
                    dot = sum(a*b for a, b in zip(q_emb, emb))
                    norm_a = math.sqrt(sum(a*a for a in q_emb))
                    norm_b = math.sqrt(sum(b*b for b in emb))
                    score = dot / (norm_a * norm_b) if norm_a and norm_b else 0
                else:
                    # Fallback to keyword matching
                    score = sum(1 for w in q_words if w in chunk_text.lower())
                scored_chunks.append((score, chunk_text))
                
            scored_chunks.sort(key=lambda x: x[0], reverse=True)
            top_chunks = [c[1] for c in scored_chunks[:3]] # Take top 3 most relevant chunks
            context = "\n\n---\n\n".join(top_chunks)
            print(f"[CHUNKING] Selected {len(top_chunks)} chunks for context.")
            
            system_prompt = f"""You are an AI assistant answering questions about a document or media.
Use the provided document context to answer the user's question accurately.
If the answer is not in the context, say "I cannot find the answer in the provided document."

CONTEXT:
{context}
"""
            print("[GROQ REQUEST] Sending RAG query...")
            try:
                completion = aurex_api.chat_completions_create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ]
                )
                response_text = completion.choices[0].message.content
                print("[GROQ RESPONSE] Success.")
            except Exception as e:
                raise Exception(f"Groq API Error: {e}")
            
            # Save chat to DB
            print("[DB WRITE] Saving RAG chat history...")
            from database.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO knowledge_chat (source_id, role, content) VALUES (?, 'user', ?)", (source_id, question))
            cursor.execute("INSERT INTO knowledge_chat (source_id, role, content) VALUES (?, 'assistant', ?)", (source_id, response_text))
            conn.commit()
            conn.close()
            
            print("[UI REFRESH] Publishing CHAT_RESPONSE success.")
            bus.publish("CHAT_RESPONSE", {"source_id": source_id, "success": True, "response": response_text})
            
        except Exception as e:
            err_msg = str(e)
            print(f"RAG Pipeline Error: {err_msg}")
            print(f"[UI REFRESH] Publishing CHAT_RESPONSE failure: {err_msg}")
            bus.publish("CHAT_RESPONSE", {"source_id": source_id, "success": False, "error": err_msg})

knowledge_pipeline = KnowledgePipeline()
