import os
from database.database import get_connection
from services.event_bus import bus

class KnowledgeService:
    @staticmethod
    def create_source(source_type: str, title: str, original_filename: str = None, 
                      source_path: str = None, url: str = None, size: int = 0,
                      project: str = "General", category: str = "Uncategorized") -> int:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO knowledge_sources (
                source_type, title, original_filename, source_path, url, size, project, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (source_type, title, original_filename, source_path, url, size, project, category))
        
        source_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        bus.publish("SOURCE_CREATED", {"source_id": source_id, "title": title})
        return source_id

    @staticmethod
    def get_sources(filters: dict = None, limit: int = 50, offset: int = 0) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "SELECT id, source_type, title, original_filename, size, project, category, knowledge_tags, created_at, updated_at, status FROM knowledge_sources WHERE 1=1"
        params = []
        
        if filters:
            if filters.get("project"):
                query += " AND project = ?"
                params.append(filters["project"])
            if filters.get("source_type"):
                query += " AND source_type = ?"
                params.append(filters["source_type"])
            if filters.get("search"):
                query += " AND (title LIKE ? OR knowledge_tags LIKE ? OR simple_explanation LIKE ? OR summary LIKE ? OR source_type LIKE ?)"
                term = f"%{filters['search']}%"
                params.extend([term, term, term, term, term])
                
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        sources = cursor.execute(query, tuple(params)).fetchall()
        conn.close()
        return [dict(s) for s in sources]

    @staticmethod
    def get_source_details(source_id: int) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        source = cursor.execute("SELECT * FROM knowledge_sources WHERE id = ?", (source_id,)).fetchone()
        conn.close()
        return dict(source) if source else None

    @staticmethod
    def update_source_metadata(source_id: int, updates: dict):
        if not updates: return
        conn = get_connection()
        cursor = conn.cursor()
        
        valid_keys = [
            "raw_content", "simple_explanation", "important_concepts", "questions",
            "learning_insights", "action_items", "difficulty_level", "estimated_read_time",
            "knowledge_tags", "title", "project", "category", "source_type",
            "status", "summary", "key_points", "transcript", "suggested_questions", "raw_response",
            "video_id", "channel", "transcript_length", "extraction_method", "processing_time",
            "quotes", "chapters", "people_mentioned", "companies_mentioned", "topics", "content_hash"
        ]
        
        set_clauses = []
        params = []
        for k, v in updates.items():
            if k in valid_keys:
                set_clauses.append(f"{k} = ?")
                params.append(v)
                
        if set_clauses:
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE knowledge_sources SET {', '.join(set_clauses)} WHERE id = ?"
            params.append(source_id)
            cursor.execute(query, tuple(params))
            conn.commit()
            
        conn.close()
        bus.publish("SOURCE_UPDATED", {"source_id": source_id})

    @staticmethod
    def delete_source(source_id: int):
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get path to delete file
        source = cursor.execute("SELECT source_path FROM knowledge_sources WHERE id = ?", (source_id,)).fetchone()
        if source and source["source_path"] and os.path.exists(source["source_path"]):
            try:
                os.remove(source["source_path"])
            except Exception as e:
                print(f"Could not delete file {source['source_path']}: {e}")
                
        cursor.execute("DELETE FROM knowledge_chunks WHERE source_id = ?", (source_id,))
        cursor.execute("DELETE FROM knowledge_chat WHERE source_id = ?", (source_id,))
        cursor.execute("DELETE FROM study_materials WHERE source_id = ?", (source_id,))
        cursor.execute("DELETE FROM knowledge_sources WHERE id = ?", (source_id,))
        
        conn.commit()
        conn.close()
        bus.publish("SOURCE_DELETED", {"source_id": source_id})

    @staticmethod
    def delete_sources(source_ids: list):
        if not source_ids: return
        conn = get_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(source_ids))
        sources = cursor.execute(f"SELECT id, source_path FROM knowledge_sources WHERE id IN ({placeholders})", source_ids).fetchall()
        
        for source in sources:
            if source["source_path"] and os.path.exists(source["source_path"]):
                try:
                    os.remove(source["source_path"])
                except Exception as e:
                    print(f"Could not delete file {source['source_path']}: {e}")
                    
        cursor.execute(f"DELETE FROM knowledge_chunks WHERE source_id IN ({placeholders})", source_ids)
        cursor.execute(f"DELETE FROM knowledge_chat WHERE source_id IN ({placeholders})", source_ids)
        cursor.execute(f"DELETE FROM study_materials WHERE source_id IN ({placeholders})", source_ids)
        cursor.execute(f"DELETE FROM knowledge_sources WHERE id IN ({placeholders})", source_ids)
        
        conn.commit()
        conn.close()
        for sid in source_ids:
            bus.publish("SOURCE_DELETED", {"source_id": sid})

    @staticmethod
    def delete_all_sources():
        conn = get_connection()
        cursor = conn.cursor()
        
        sources = cursor.execute("SELECT id, source_path FROM knowledge_sources").fetchall()
        for source in sources:
            if source["source_path"] and os.path.exists(source["source_path"]):
                try:
                    os.remove(source["source_path"])
                except Exception as e:
                    print(f"Could not delete file {source['source_path']}: {e}")
                    
        cursor.execute("DELETE FROM knowledge_chunks")
        cursor.execute("DELETE FROM knowledge_chat")
        cursor.execute("DELETE FROM study_materials")
        cursor.execute("DELETE FROM knowledge_sources")
        
        conn.commit()
        conn.close()
        # Publish generic event for complete wipe
        bus.publish("ALL_SOURCES_DELETED", {})

    # Chunks Management
    @staticmethod
    def save_chunks(source_id: int, chunks: list):
        if not chunks: return
        conn = get_connection()
        cursor = conn.cursor()
        
        # Clear old chunks if re-analyzing
        cursor.execute("DELETE FROM knowledge_chunks WHERE source_id = ?", (source_id,))
        
        data = []
        for idx, chunk in enumerate(chunks):
            if isinstance(chunk, dict):
                data.append((source_id, idx, chunk.get("text", ""), chunk.get("embedding_json", None)))
            else:
                data.append((source_id, idx, str(chunk), None))
                
        cursor.executemany(
            "INSERT INTO knowledge_chunks (source_id, chunk_index, content, embedding_json) VALUES (?, ?, ?, ?)",
            data
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_chunks(source_id: int) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        chunks = cursor.execute("SELECT content FROM knowledge_chunks WHERE source_id = ? ORDER BY chunk_index ASC", (source_id,)).fetchall()
        conn.close()
        return [c["content"] for c in chunks]

knowledge_service = KnowledgeService()
