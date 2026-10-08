"""Persistent storage for knowledge documents."""
import sqlite3

class KnowledgeStorage:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)

    def save_batch(self, docs: list[dict]):
        pass

    def get_by_id(self, doc_id: str) -> dict | None:
        return {"id": doc_id}
