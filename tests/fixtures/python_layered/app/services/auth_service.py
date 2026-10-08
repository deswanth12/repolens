"""Authentication service."""
from app.db.repository import UserRepository
from app.models import User

class AuthService:
    def __init__(self):
        self.repo = UserRepository()

    def list_users(self) -> list[User]:
        return self.repo.find_all()
