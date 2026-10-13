import json
import sqlite3
import uuid

from pathlib import Path
from datetime import datetime, timezone

import numpy as np
from sentence_transformers import SentenceTransformer

from memoryos.context import ContextEngine
from memoryos.relationships import RelationshipEngine
from memoryos.conflict_identity import ConflictIdentityEngine, register_conflict_in_transaction


class MemoryPipeline:

    def __init__(self, db_path="data/pipeline.db"):

        Path(db_path).parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.db = sqlite3.connect(db_path)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                subject TEXT NOT NULL,
                attribute TEXT NOT NULL,
                source TEXT,
                valid_at TEXT,
                embedding TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS conflicts (
                id TEXT PRIMARY KEY,
                existing_id TEXT NOT NULL,
                incoming_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(existing_id) REFERENCES memories(id),
                FOREIGN KEY(incoming_id) REFERENCES memories(id)
            )
        """)

        self.db.commit()

        # Initialize the canonical conflict identity registry.
        # This uses the same database file, before memory writes begin.
        self.identity = ConflictIdentityEngine(db_path)
        self.identity.close()

        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        self.context_engine = ContextEngine(
            relationship_engine=RelationshipEngine()
        )

    def _embed(self, text):

        return self.embedding_model.encode(
            text,
            normalize_embeddings=True
        ).tolist()

    def remember(
        self,
        content,
        subject,
        attribute,
        source=None,
        valid_at=None,
        threshold=0.50
    ):

        if not 0 <= threshold <= 1:
            raise ValueError("Invalid similarity threshold")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (content, subject, attribute)
        ):
            raise ValueError(
                "Content, subject and attribute must be nonempty strings"
            )

        memory_id = str(uuid.uuid4())

        embedding = self._embed(content)

        incoming = {
            "content": content,
            "subject": subject,
            "attribute": attribute,
            "valid_at": valid_at
        }

        rows = self.db.execute("""
            SELECT id, content, subject,
                   attribute, valid_at, embedding
            FROM memories
        """).fetchall()

        relationships = []

        for row in rows:

            (
                existing_id,
                old_content,
                old_subject,
                old_attribute,
                old_time,
                old_embedding
            ) = row

            # Check contextual identity before expensive NLI
            if (
                old_subject != subject
                or old_attribute != attribute
            ):
                continue

            vector = np.array(
                json.loads(old_embedding)
            )

            similarity = float(
                np.dot(embedding, vector)
            )

            if similarity < threshold:
                continue

            existing = {
                "content": old_content,
                "subject": old_subject,
                "attribute": old_attribute,
                "valid_at": old_time
            }

            result = self.context_engine.compare(
                existing,
                incoming
            )

            relationships.append({
                "existing_id": existing_id,
                "similarity": round(similarity, 4),
                "relationship": result["relationship"],
                "conflict": result["conflict"]
            })

        now = datetime.now(timezone.utc).isoformat()

        with self.db:

            self.db.execute("""
                INSERT INTO memories
                (
                    id, content, subject, attribute,
                    source, valid_at, embedding, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                content,
                subject,
                attribute,
                source,
                valid_at,
                json.dumps(embedding),
                now
            ))

            for result in relationships:

                if result["conflict"]:

                    register_conflict_in_transaction(
                        self.db,
                        result["existing_id"],
                        memory_id,
                        result["relationship"]
                    )

        return {
            "memory_id": memory_id,
            "relationships": relationships,
            "conflicts_detected": sum(
                item["conflict"]
                for item in relationships
            )
        }

    def recall(self, query, limit=5):

        if limit < 1:
            raise ValueError("limit must be positive")

        query_vector = self._embed(query)

        rows = self.db.execute("""
            SELECT id, content, subject,
                   attribute, embedding
            FROM memories
        """).fetchall()

        results = []

        for row in rows:

            memory_id, content, subject, attribute, embedding = row

            vector = np.array(
                json.loads(embedding)
            )

            similarity = float(
                np.dot(query_vector, vector)
            )

            results.append({
                "id": memory_id,
                "content": content,
                "subject": subject,
                "attribute": attribute,
                "score": round(similarity, 4)
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:limit]


    def recall_with_conflicts(self, query, limit=5):
        """
        Retrieve semantic memories together with
        their recorded conflict relationships.

        Conflict status is based on stored reports,
        not on a fresh NLI evaluation.
        """

        memories = self.recall(query, limit=limit)

        for memory in memories:

            memory_id = memory["id"]

            rows = self.db.execute("""
                SELECT
                    c.id,
                    c.relationship,
                    c.existing_id,
                    c.incoming_id,
                    m1.content,
                    m2.content
                FROM conflicts c
                JOIN memories m1
                    ON c.existing_id = m1.id
                JOIN memories m2
                    ON c.incoming_id = m2.id
                WHERE
                    c.existing_id = ?
                    OR c.incoming_id = ?
            """, (memory_id, memory_id)).fetchall()

            conflicting_memories = []

            for row in rows:

                (
                    conflict_id,
                    relationship,
                    existing_id,
                    incoming_id,
                    existing_content,
                    incoming_content
                ) = row

                # Determine which side is the other memory
                if memory_id == existing_id:
                    other_id = incoming_id
                    other_content = incoming_content
                else:
                    other_id = existing_id
                    other_content = existing_content

                conflicting_memories.append({
                    "conflict_id": conflict_id,
                    "memory_id": other_id,
                    "content": other_content,
                    "relationship": relationship
                })

            memory["status"] = (
                "disputed"
                if conflicting_memories
                else "no_recorded_conflict"
            )

            memory["conflict_count"] = len(
                conflicting_memories
            )

            memory["conflicting_memories"] = (
                conflicting_memories
            )

        return memories

    def get_conflicts(self):

        return self.db.execute("""
            SELECT
                c.existing_id,
                c.incoming_id,
                m1.content,
                m2.content,
                c.relationship
            FROM conflicts c
            JOIN memories m1
                ON c.existing_id = m1.id
            JOIN memories m2
                ON c.incoming_id = m2.id
        """).fetchall()

    def close(self):
        self.db.close()
