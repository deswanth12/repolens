"""Controls the main document ingestion workflow."""
from app.knowledge.parser import DocumentParser
from app.knowledge.storage import KnowledgeStorage

class IngestWorkflow:
    def __init__(self):
        self.parser = DocumentParser()
        self.storage = KnowledgeStorage()

    def run(self, source_dir: str):
        docs = self.parser.parse_all(source_dir)
        self.storage.save_batch(docs)
