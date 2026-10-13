import sqlite3
import uuid


class ConflictIdentityEngine:
    """
    Canonical conflict identity for unordered memory pairs.

    This experimental engine creates a separate registry
    referencing the existing conflicts table.

    It does not migrate historical duplicate conflicts.
    """

    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.db.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def _initialize(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS conflict_identity (
                memory_a TEXT NOT NULL,
                memory_b TEXT NOT NULL,
                conflict_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (memory_a, memory_b),

                CHECK (memory_a < memory_b),

                FOREIGN KEY (memory_a)
                    REFERENCES memories(id),

                FOREIGN KEY (memory_b)
                    REFERENCES memories(id),

                FOREIGN KEY (conflict_id)
                    REFERENCES conflicts(id)
            )
        """)
        self.db.commit()

    @staticmethod
    def canonical_pair(first_id, second_id):
        if not isinstance(first_id, str):
            raise ValueError("Memory IDs must be strings")

        if not isinstance(second_id, str):
            raise ValueError("Memory IDs must be strings")

        if not first_id or not second_id:
            raise ValueError("Memory IDs cannot be empty")

        if first_id == second_id:
            raise ValueError(
                "A memory cannot conflict with itself"
            )

        return tuple(sorted((first_id, second_id)))

    def get_conflict_id(self, first_id, second_id):
        memory_a, memory_b = self.canonical_pair(
            first_id,
            second_id
        )

        row = self.db.execute("""
            SELECT conflict_id
            FROM conflict_identity
            WHERE memory_a = ?
              AND memory_b = ?
        """, (memory_a, memory_b)).fetchone()

        return row[0] if row else None

    def get_or_create(
        self,
        first_id,
        second_id,
        relationship="potential_conflict"
    ):
        memory_a, memory_b = self.canonical_pair(
            first_id,
            second_id
        )

        # SQLite's write transaction serializes competing writers.
        # This protects the read-and-create operation.
        self.db.execute("BEGIN IMMEDIATE")

        try:
            existing = self.db.execute("""
                SELECT conflict_id
                FROM conflict_identity
                WHERE memory_a = ?
                  AND memory_b = ?
            """, (memory_a, memory_b)).fetchone()

            if existing:
                self.db.commit()

                return {
                    "conflict_id": existing[0],
                    "created": False,
                    "memory_pair": (memory_a, memory_b)
                }

            # Require both original memories to exist.
            rows = self.db.execute("""
                SELECT id
                FROM memories
                WHERE id IN (?, ?)
            """, (memory_a, memory_b)).fetchall()

            if len(rows) != 2:
                raise ValueError(
                    "Both memories must exist"
                )

            conflict_id = str(uuid.uuid4())

            self.db.execute("""
                INSERT INTO conflicts (
                    id,
                    existing_id,
                    incoming_id,
                    relationship,
                    created_at
                )
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (
                conflict_id,
                memory_a,
                memory_b,
                relationship
            ))

            self.db.execute("""
                INSERT INTO conflict_identity (
                    memory_a,
                    memory_b,
                    conflict_id
                )
                VALUES (?, ?, ?)
            """, (
                memory_a,
                memory_b,
                conflict_id
            ))

            self.db.commit()

            return {
                "conflict_id": conflict_id,
                "created": True,
                "memory_pair": (memory_a, memory_b)
            }

        except Exception:
            self.db.rollback()
            raise

    def close(self):
        self.db.close()


def register_conflict_in_transaction(
    db,
    first_id,
    second_id,
    relationship="potential_conflict"
):
    """
    Register or reuse a conflict inside the caller's transaction.

    The caller must manage BEGIN/COMMIT/ROLLBACK.
    No new connection is opened here.
    """

    memory_a, memory_b = ConflictIdentityEngine.canonical_pair(
        first_id,
        second_id
    )

    existing = db.execute("""
        SELECT conflict_id
        FROM conflict_identity
        WHERE memory_a = ? AND memory_b = ?
    """, (memory_a, memory_b)).fetchone()

    if existing:
        return {
            "conflict_id": existing[0],
            "created": False
        }

    # Historical conflicts may exist without registry entries.
    # Reuse an existing record instead of inserting a duplicate.
    historical = db.execute("""
        SELECT id
        FROM conflicts
        WHERE
            (existing_id = ? AND incoming_id = ?)
            OR
            (existing_id = ? AND incoming_id = ?)
        ORDER BY created_at, rowid
        LIMIT 1
    """, (
        memory_a,
        memory_b,
        memory_b,
        memory_a
    )).fetchone()

    if historical:
        conflict_id = historical[0]
        created = False
    else:
        conflict_id = str(uuid.uuid4())

        db.execute("""
            INSERT INTO conflicts (
                id,
                existing_id,
                incoming_id,
                relationship,
                created_at
            )
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (
            conflict_id,
            memory_a,
            memory_b,
            relationship
        ))

        created = True

    db.execute("""
        INSERT INTO conflict_identity (
            memory_a,
            memory_b,
            conflict_id
        )
        VALUES (?, ?, ?)
    """, (
        memory_a,
        memory_b,
        conflict_id
    ))

    return {
        "conflict_id": conflict_id,
        "created": created
    }
