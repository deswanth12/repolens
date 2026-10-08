"""Data processor."""
from .utils import sanitize

def process_data(input_text: str) -> str:
    cleaned = sanitize(input_text)
    return f"Processed: {cleaned}"
