import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "review.db"

class ReviewService:
    def __init__(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guten_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        self.db.commit()

    def create_review(self, guten_id: int, username: str, rating: int, text: str):
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute("""
            INSERT INTO reviews (guten_id, username, rating, text, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (guten_id, username, rating, text, now))
        self.db.commit()
        return {"guten_id": guten_id, "username": username, "rating": rating, "text": text, "created_at": now}

    def list_reviews(self, guten_id: int):
        cur = self.db.execute("""
            SELECT * FROM reviews WHERE guten_id=? ORDER BY created_at DESC
        """, (guten_id,))
        return [dict(row) for row in cur.fetchall()]
