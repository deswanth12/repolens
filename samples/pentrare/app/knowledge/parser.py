"""Transforms and parses raw documents."""

class DocumentParser:
    def parse_all(self, source_dir: str) -> list[dict]:
        return [{"id": "doc1", "content": "Security finding"}]
