"""Handlers package for FastAPI Auth Service."""

from .users import Users
from .settings import Settings
from .newsletter import Newsletter

__all__ = [
    "Users",
    "Settings", 
    "Newsletter"
]