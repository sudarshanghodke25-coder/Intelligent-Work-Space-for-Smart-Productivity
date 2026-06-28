import json
from typing import List
from database.database import get_connection

class EmbeddingStore:
    def store_embedding(self, chunk_id: int, embedding: List[float]):
        pass

class SQLiteEmbeddingStore(EmbeddingStore):
    def store_embedding(self, chunk_id: int, embedding: List[float]):
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE knowledge_chunks SET embedding_json = ? WHERE id = ?", (json.dumps(embedding), chunk_id))
        conn.commit()
        conn.close()

    def get_embeddings_by_source(self, source_id: int) -> List[dict]:
        conn = get_connection()
        c = conn.cursor()
        rows = c.execute("SELECT id, content, embedding_json FROM knowledge_chunks WHERE source_id = ? ORDER BY chunk_index ASC", (source_id,)).fetchall()
        conn.close()
        
        results = []
        for r in rows:
            emb = json.loads(r['embedding_json']) if r['embedding_json'] else None
            results.append({
                "chunk_id": r['id'],
                "content": r['content'],
                "embedding": emb
            })
        return results

class EmbeddingService:
    def __init__(self):
        self.store = SQLiteEmbeddingStore()
        self._model = None
        
    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            print("[EmbeddingService] Loading local sentence-transformers model...")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._model
        
    def preload(self):
        """Load the model into memory in a background thread."""
        try:
            self._get_model()
            print("[EmbeddingService] Preload complete.")
        except Exception as e:
            print(f"[EmbeddingService] Preload failed: {e}")

    def generate_embedding(self, text: str) -> List[float]:
        try:
            model = self._get_model()
            embedding = model.encode(text).tolist()
            return embedding
        except Exception as e:
            print(f"[EmbeddingService] Failed to generate embedding: {e}")
            return []

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            model = self._get_model()
            embeddings = model.encode(texts).tolist()
            return embeddings
        except Exception as e:
            print(f"[EmbeddingService] Failed to generate batched embeddings: {e}")
            return [[] for _ in texts]

embedding_service = EmbeddingService()
