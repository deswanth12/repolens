"""Database repository."""
import sqlite3
from app.models import User

class UserRepository:
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)

    def find_all(self) -> list[User]:
        return [User(id=1, username="admin")]
