"""Handles semantic and keyword retrieval."""
from app.knowledge.storage import KnowledgeStorage

class KnowledgeRetriever:
    def __init__(self):
        self.storage = KnowledgeStorage()

    def query(self, query_text: str) -> list[dict]:
        return [{"query": query_text, "score": 0.98}]
