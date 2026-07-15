"""TeamAgent storage layer - SQLite database management."""

from .schema import init_database, get_database_path

__all__ = ['init_database', 'get_database_path']
