import sqlite3
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
from sentence_transformers import SentenceTransformer


class MemoryOS:
    def __init__(self, db_path="data/memory.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db = sqlite3.connect(db_path)

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        self.db.commit()

    def remember(self, content, deduplicate=True, threshold=0.92):
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")

        if deduplicate:
            matches = self.recall(content, limit=1)

            if matches and matches[0]["score"] >= threshold:
                return matches[0]["id"]

        memory_id = str(uuid.uuid4())

        embedding = self.model.encode(
            content,
            normalize_embeddings=True
        ).tolist()

        self.db.execute(
            """
            INSERT INTO memories
            (id, content, embedding, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                memory_id,
                content,
                json.dumps(embedding),
                datetime.now(timezone.utc).isoformat()
            )
        )

        self.db.commit()
        return memory_id

    def recall(self, query, limit=5):
        query_vector = self.model.encode(
            query,
            normalize_embeddings=True
        )

        rows = self.db.execute(
            "SELECT id, content, embedding FROM memories"
        ).fetchall()

        results = []

        for memory_id, content, embedding in rows:
            vector = np.array(json.loads(embedding))

            score = float(
                np.dot(query_vector, vector)
            )

            results.append({
                "id": memory_id,
                "content": content,
                "score": round(score, 4)
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:limit]

    def update(self, memory_id, content):
        embedding = self.model.encode(
            content,
            normalize_embeddings=True
        ).tolist()

        cursor = self.db.execute(
            """
            UPDATE memories
            SET content = ?, embedding = ?
            WHERE id = ?
            """,
            (
                content,
                json.dumps(embedding),
                memory_id
            )
        )

        self.db.commit()
        return cursor.rowcount > 0

    def forget(self, memory_id):
        cursor = self.db.execute(
            "DELETE FROM memories WHERE id = ?",
            (memory_id,)
        )

        self.db.commit()
        return cursor.rowcount > 0

    def close(self):
        self.db.close()
