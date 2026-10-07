from .frontend import bp as frontend_bp
from .api import bp as api_bp
from .admin import bp as admin_bp

__all__ = ["frontend_bp", "api_bp", "admin_bp"]
