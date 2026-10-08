"""API endpoints."""
from fastapi import APIRouter
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.get("/users")
def get_users():
    return auth_service.list_users()
