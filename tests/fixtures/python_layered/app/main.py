"""Application entry point."""
from app.api.routes import router

def create_app():
    return router

if __name__ == "__main__":
    app = create_app()
