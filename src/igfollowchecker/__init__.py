"""Local analysis and optional live collection; imports have no browser side effects."""
from .core import analyze, compare_snapshots, load_users, normalize_username
__version__ = "0.2.0"
__all__ = ["analyze", "compare_snapshots", "load_users", "normalize_username"]
